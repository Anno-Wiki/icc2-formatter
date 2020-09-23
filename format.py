import sys
import re
import argparse
import yaml

from collections import deque

DELIMITERS = {
    'parens':   ['(', ')'],
    'braces':   ['{', '}'],
    'brackets': ['[', ']'],
    'angles':   ['<', '>'],
}

TAGS = {
    '*': {'type': 'style', 'tag': 'bold'},
    '_': {'type': 'style', 'tag': 'italics'},
}

CLOSERS = {}


class InputError(Exception):
    """An error to be raised on malformed input"""
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


def preparetags(toc, delim):
    """Prepare the TAGS dictionary for use in annotating the text."""
    DELIMITED = ['pre', 'quote', 'quotepre']

    # Add all of the tags with their proper delimiters
    for tag in DELIMITED:
        opener = ''.join([delim[0], tag, delim[1]])
        closer = ''.join([delim[0], '/', tag, delim[1]])
        TAGS[opener] = {'type': 'style', 'tag': tag}
        CLOSERS[opener] = closer


    # Add all of the tocs with delimiters
    for i, name in enumerate(toc):
        # We have to add one to i because it's 0 indexed, but depth 0 is the
        # book.
        opener = ''.join([delim[0], str(i+1), delim[1]])
        closer = ''.join([delim[0], '/', str(i+1), delim[1]])
        TAGS[opener] = {
            'type': 'toc',
            'depth': i+1,
            'name': name
        }
        CLOSERS[opener] = closer


def annotate(text, delim):
    """Annotate the text. That is, generate all of the annotations detailing the
    ranges and nature of the stretch of text. They will be used later to strip
    the markup.
    """
    offset = 0
    annotations = []
    for i, char in enumerate(text):
        if char == delim[0] and text[i+1] != '/':
            # We have a delimiter
            found = False
            for tag in TAGS.keys():
                if text[i:i+len(tag)] == tag:
                    found = True
                    break
            if found:
                data = TAGS[tag].copy()
                data['open'] = i - offset
                offset += len(tag)
                close = re.search(CLOSERS[tag], text[i+len(tag):]).span()
                data['close'] = close[0] - offset
                offset += len(CLOSERS[tag])
                annotations.append(data)
            else:
                raise InputError(text[i:i+30], "Malformed tag.")
        elif char == '*' or char == '_':
            data = TAGS[char].copy()
            data['open'] = i - offset
            offset += 1
            close = re.search(char, text[i+1:]).span()
            data['close'] = close[0] - offset
            offset += 1
            annotations.append(data)
    return annotations


def process(text, metadata):
    """Process route, really the main action of the script."""
    if (md := metadata['delimiter']) in DELIMITERS:
        # delimiter is a default
        delimiter = DELIMITERS[md]
    else:
        # delimiter is symmetric
        delimiter = [md, md]

    preparetags(metadata['toc'], delimiter)
    annotations = annotate(text, delimiter)
    print(annotations)


def main(fin, metadata_in):
    """Main route, to be called when run from command line."""
    metadata = yaml.load(metadata_in, yaml.CLoader)
    text = fin.read()
    fin.close()
    process(text, metadata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse .icc texts into json"
                                     "files for import into ICC2")
    parser.add_argument('-m', '--metadata-in', type=argparse.FileType('rt'),
                        default='metadata.yml', help="The metadata.yml file.")
    parser.add_argument('fin', metavar='filein', nargs='?',
                        type=argparse.FileType('rt'), default=sys.stdin,
                        help="The .icc text file")
    args = parser.parse_args()

    main(args.fin, args.metadata_in)
