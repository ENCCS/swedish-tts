import re
import subprocess
import sys

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

with open("../output.csv", "r") as a_file:
  for line in a_file:
    stripped_line = line.strip()
    [path, text] = stripped_line.split('|')
    wav_filename = path.split('/')[-1]
    txt_filename = wav_filename.replace('wav', 'txt')

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
        print(f'Had unusual letters {text}')
        write_txt_file = False
    else:
        write_txt_file = True

    if write_txt_file:
        with open(txt_filename, "w") as text_file:
            text_file.write(text)
