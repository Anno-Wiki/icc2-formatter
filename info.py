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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get unique characters and size"
                                               "of a text file.")
    parser.add_argument('-f', '--file', type=str, required=True,
                        help="Filename")

    args = parser.parse_args()

    main(args.file)
