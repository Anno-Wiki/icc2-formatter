import sys
import re
import argparse
import yaml
import time
import json

from collections import deque

# Default delimiters
DELIMITERS = {
    'parens':   ['(', ')'],
    'braces':   ['{', '}'],
    'brackets': ['[', ']'],
    'angles':   ['<', '>'],
}

# Global tags to be prepared for searching, payload for annotations
TAGS = {}

# Matching closer tags for searching
CLOSERS = {}

# Default text chunk size
CHUNKSIZE = 100000


def preparetags(toc, delim):
    """Prepare the TAGS dictionary for use in annotating the text."""
    DELIMITED = ['pre', 'quote', 'quotepre', 'preline', 'i', 'b']

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
        opener = ''.join([delim[0], 'h', str(i+1), delim[1]])
        closer = ''.join([delim[0], '/', 'h', str(i+1), delim[1]])
        TAGS[opener] = {
            'type': 'toc',
            'depth': i+1,
            'name': name
        }
        CLOSERS[opener] = closer


def annotate(text):
    """Annotate the text. That is, generate all of the annotations detailing the
    ranges and nature of the stretch of text. They will be used later to strip
    the markup.
    """
    annotations = []
    regex = re.compile('|'.join(list(TAGS.keys()) + list(CLOSERS.values())))
    print(f"Search string: \"{regex}\"")

    offset = 0
    i = 0
    stack = []
    while m := re.search(regex, text[i:]):
        # Opening tag
        match = m.group(0)
        matchloc = m.start(0)
        if match in TAGS.keys():
            payload = TAGS[match].copy()
            i += matchloc
            payload['open'] = i - offset
            i += len(match)
            offset += len(match)
            stack.append(payload)
        elif match in CLOSERS.values():
            payload = stack.pop()
            i += matchloc
            payload['close'] = i - offset
            i += len(match)
            offset += len(match)
            annotations.append(payload)
        else:
            raise Error("Yo, this shit broken bruv.")

    return annotations


def strip(text):
    """Strip all markup from the text."""
    # Strip markup
    for tag in TAGS.keys():
        text = text.replace(tag, '')

    # Strip close tags
    for tag in CLOSERS.values():
        text = text.replace(tag, '')

    return text


def split(text):
    chunks = []
    sequence = 0
    for i in range(0, len(text), CHUNKSIZE):
        chunks.append({
            'offset': i,
            'text': text[i:i+CHUNKSIZE],
            'sequence': sequence
        })
        sequence += 1
    return chunks



def process(text, metadata):
    """Process route, really the main action of the script."""
    if (md := metadata['delimiter']) in DELIMITERS:
        # delimiter is a default
        delimiter = DELIMITERS[md]
    else:
        # delimiter is symmetric
        delimiter = [md, md]

    print('Preparing tags...')
    preparetags(metadata['toc'], delimiter)
    print(TAGS.keys())
    print("Preparing annotations...")
    annotations = annotate(text)

    print("Stripping markup...")
    text = strip(text)

    print("Splitting text into chunks...")
    text = split(text)

    return text, annotations


def main(fin, metadata_in):
    """Main route, to be called when run from command line."""
    metadata = yaml.load(metadata_in, yaml.CLoader)
    text = fin.read()
    fin.close()
    text, annotations = process(text, metadata)

    with open('text.json', 'wt') as fout:
        json.dump(text, fout)
    with open('annotations.json', 'wt') as fout:
        json.dump(annotations, fout)


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
