import os
import argparse


def main(filename):
    with open(filename, 'rt') as fin:
        text = fin.read()

    size = os.path.getsize(filename)
    chars = set(text)
    charlist = list(chars)
    charlist.sort()
    charstring = ''.join(charlist)
    print(size, charstring)
    if '_' in charstring:
        count = text.count('_')
        print(f"{count} underscores were found in the text.")
        print("An even count implies they are used as markup.")
    if '*' in charstring:
        count = text.count('*')
        print(f"{count} asterisks were found in the text.")
        print("An even count implies they could be markup.")
        print("Visually verify they are not being used as annotations.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get unique characters and size"
                                               "of a text file.")
    parser.add_argument('-f', '--file', type=str, required=True,
                        help="Filename")

    args = parser.parse_args()

    main(args.file)
