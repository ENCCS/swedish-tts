import glob
import json
import logging
import os
import random
import re
import sox
import subprocess
import sys
from tqdm import tqdm

def has_digits(text):
    return any(True for _ in filter(str.isdigit, text))

def is_unusual_letter(char):
    unusual_letters = r"([àáæëíñóøšú¿])"
    unusual_letters_re = re.compile(unusual_letters)
    return bool(unusual_letters_re.search(char))

def has_unusual_letters(text):
    return any(True for _ in filter(is_unusual_letter, text))

def split_into_words(line):
    word_regex_improved = r"(\w[\w']*\w|\w)"
    word_matcher = re.compile(word_regex_improved)
    return word_matcher.findall(line)

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

# First command-line argument is the path to SwedishDataset.zip
old_cwd = os.getcwd()
tmp_dir = os.path.join(old_cwd, "tmp")

def unpack_archive():
    logging.info('Unpacking SwedishDataset files')
    subprocess.run(["unzip", "-d", tmp_dir, sys.argv[1]])
#unpack_archive()

combined_dir = "combined-SwedishDataset"
output_dir = os.path.join(old_cwd, combined_dir, "wavs")
os.makedirs(output_dir, exist_ok=True)

# Does the first half of NeMo's
# scripts/dataset_processing/create_manifests_and_textfiles.py to make
# a "wavs" folder that contains matching wav and txt files. We
# currently omit all transcripts that include digits, because we
# haven't written code to spell out all kinds of numbers in words,
# e.g. "103", "10b", and "1945" all need special handling. We also
# omit all texts that have unusual characters, such as accented
# letters not normally used in Swedish.
def combine_wavs_and_make_txt_files():
    logging.info('Combining SwedishDataset files')
    for csv_file in tqdm(glob.glob(os.path.join(tmp_dir, "*", "*", "*", "*.csv"))):
        os.chdir(os.path.join(os.path.dirname(csv_file), "wavs"))
        with open("../output.csv", "r") as a_file:
            for line in a_file:
                print(line)

        with open("../output.csv", "r") as a_file:
            for line in a_file:
                stripped_line = line.strip()
                [path, text] = stripped_line.split('|')

                if has_digits(text):
        #         print('Has digits: ' + text)
        #         new_text=''
        #         for word in split_into_words(text):
        # #            print(f'word is {word}')
        #             if has_digits(word):
        #                 new_word = subprocess.run(["/home/mabraham/go/bin/number-to-words", "--lang", "sv-se", word], capture_output=True, text=True).stdout.rstrip("\n")
        # TODO change "en" to "ett" or use num2words instead
        # TODO cater for years
        #                 print(f'new word is {new_word}')
        #                 new_text+=new_word + ' '
        #             else:
        #                 new_text+=word + ' '
        #         print('Possible written form: ' + new_text )
        #         subprocess.run(["play", wav_filename])
        #         write_txt_file = query_yes_no("Should the proposed written form be accepted?", default="yes")
                    write_txt_file = False
                elif has_unusual_letters(text):
                    print(f'{path} had unusual letters {text}')
                    write_txt_file = False
                else:
                    write_txt_file = True

                if write_txt_file:
                    wav_filename = path.split('/')[-1]
                    # The "betraktarens" data is named "output" rather than
                    # for the novel name, so fix that.
                    final_wav_filename = wav_filename.replace('output', 'betraktarens')
                    txt_filename = os.path.join(output_dir, final_wav_filename.replace('wav', 'txt'))
                    os.replace(wav_filename, os.path.join(output_dir, final_wav_filename))
                    with open(txt_filename, "w") as text_file:
                        text_file.write(text)

        os.chdir(old_cwd)

#combine_wavs_and_make_txt_files()

def make_swedish_mfa_dictionary():
    os.chdir(combined_dir)
    logging.info('Downloading Swedish g2p model')
    subprocess.run(["mfa", "model", "download", "g2p", "swedish_g2p"])
    logging.info('Making Swedish pronunciation dictionary')
    subprocess.run(["mfa", "g2p", "swedish_g2p", "wavs", "pronunciation-dictionary.txt", "-j", "12"])
    os.chdir(old_cwd)

#make_swedish_mfa_dictionary()

# Create JSON mappings from word to phonemes and phonemes to indices
def create_token2idx_dict():
    logging.info("Creating word->phone and phone->idx mappings in mappings.json")
    os.chdir(combined_dir)
    subprocess.run(["python", "../create_token2idx_dict.py", "--dictionary", "pronunciation-dictionary.txt", "--dict_out", "mappings.json"])
    os.chdir(old_cwd)

#create_token2idx_dict()

random.seed(10234)

# Does the other half of NeMo's scripts/dataset_processing/create_manifests_and_textfiles.py
# to make JSON manifest files for the training, validation, and test split
def make_manifest():
    logging.info('Making manifest files for splitting the data')
    os.chdir(combined_dir)
    splits = ['train', 'val', 'test']
    files = {}
    for split in splits:
        files[split] = open(f"combined_{split}.json", 'w')
    for wav_file in tqdm(glob.glob(os.path.join("wavs", "*.wav"))):
        txt_file = wav_file.replace('.wav', '.txt')
        random_number = random.random()
        entry = {
            # TODO does this need to be an absolute path?
            'audio_filepath': os.path.join("/workspace/voxo/combined-SwedishDataset", wav_file),
            'duration': sox.file_info.duration(wav_file),
            'text': open(txt_file).read()
            }
        if random_number < 0.7:
            split_choice = "train"
        elif random_number < 0.9:
            split_choice = "val"
        else:
            split_choice = "test"
        files[split_choice].write(json.dumps(entry) + '\n')
    os.chdir(old_cwd)

#make_manifest()

# Does the equivalent of NeMo's
# scripts/dataset_processing/extract_ljspeech_phonemes_and_durs.sh,
# aligning the wav to the text down to the phoneme level
def align_wav_and_txt():
    logging.info('Downloading Swedish acoustic model')
    subprocess.run(["mfa", "model", "download", "acoustic", "swedish"])

    alignment_command = ["mfa", "align", "--overwrite", combined_dir, os.path.join(combined_dir, "pronunciation-dictionary.txt"), "swedish", os.path.join(combined_dir, "alignments")]
    # currently multiprocessing breaks while making CFM
    alignment_command.append("--disable_mp")
    alignment_command.append("--verbose")
    logging.info('Aligning text and audio')
    subprocess.run(alignment_command)

#align_wav_and_txt()

# Create durations for the corpus based on MFA TextGrid alignments
# based on a modified form of NeMo's
# scripts/text_preprocessing/calculate_durs.py.  Uses defaults for
# sample rate and hop length. Note that the sample rate must match
# that of the .wav files
def calculate_durations():
    logging.info("Calculate phoneme durations from TextGrids")
    subprocess.run(["python", "calculate_durs.py", "--ljspeech_dir", combined_dir, "--mappings", os.path.join(combined_dir, "mappings.json")])
    logging.info("Phoneme durations and tokens written.")

calculate_durations()

# Extract energy and pitch data based on a modified form of NeMo's
# scripts/text_preprocessing/extract_ljspeech_energy_pitch.py.  This
# might need changes to fmin and fmax for different speakers.  Also
# uses defaults for sample rate, which must match that of the .wav
# files.
def extract_energy_and_pitch():
    logging.info("Extracting energy and pitch data")
    subprocess.run(["python", "extract_ljspeech_energy_pitch.py", "--ljspeech_dir", combined_dir])
    logging.info("Extracted energy and pitch data")

#extract_energy_and_pitch()
