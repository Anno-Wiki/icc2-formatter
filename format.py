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


def preparetags(toc, delim, bookid):
    """Prepare the TAGS dictionary for use in annotating the text."""
    DELIMITED = ['pre', 'quote', 'quotepre', 'preline', 'i', 'b']

    # Add all of the tags with their proper delimiters
    for tag in DELIMITED:
        opener = ''.join([delim[0], tag, delim[1]])
        closer = ''.join([delim[0], '/', tag, delim[1]])
        TAGS[opener] = {'type': 'style', 'tag': tag, 'bookid': bookid}
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
            'name': name,
            'bookid': bookid
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
    key = 1
    stack = []
    tocs = {}
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
            payload['id'] = key
            if payload['type'] == 'toc':
                tocs[payload['depth']] = key
                if payload['depth'] > 1:
                    payload['parent'] = tocs[payload['depth'] - 1]
                else:
                    payload['parent'] = 0

            annotations.append(payload)
            key += 1
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


def split(text, bookid):
    chunks = []
    sequence = 0
    for i in range(0, len(text), CHUNKSIZE):
        chunks.append({
            'offset': i,
            'text': text[i:i+CHUNKSIZE],
            'sequence': sequence,
            'bookid': bookid
        })
        sequence += 1
    return chunks


def appendcontent(tocs, text):
    for toc in tocs:
        toc['content'] = text[toc['open']:toc['close']]


def process(text, metadata):
    """Process route, really the main action of the script."""
    if (md := metadata['delimiter']) in DELIMITERS:
        # delimiter is a default
        delimiter = DELIMITERS[md]
    else:
        # delimiter is symmetric
        delimiter = [md, md]

    print('Preparing tags...')
    preparetags(metadata['toc'], delimiter, metadata['bookid'])
    print(TAGS.keys())
    print("Preparing annotations...")
    annotations = annotate(text)
    annotations.append({
        'type': 'toc',
        'depth': 0,
        'name': metadata['title'],
        'bookid': metadata['bookid'],
        'slug': metadata['slug'],
        'id': 0
    })

    print("Stripping markup...")
    text = strip(text)

    tocs = list(filter(lambda l: l['type'] == 'toc' and l['depth'] >= 1,
                       annotations))
    print("Appending content to annotations")
    appendcontent(tocs, text)

    print("Splitting text into chunks...")
    text = split(text, metadata['bookid'])

    return text, annotations


def main(din):
    """Main route, to be called when run from command line."""
    with open(f'{din}/metadata.yml') as fin:
        metadata = yaml.load(fin, yaml.CLoader)
    with open(f'{din}/prepared.icc') as fin:
        text = fin.read()
    text, annotations = process(text, metadata)

    with open(f'{din}/text.json', 'wt') as fout:
        json.dump(text, fout)
    with open(f'{din}/annotations.json', 'wt') as fout:
        json.dump(annotations, fout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse .icc texts into json"
                                     "files for import into ICC2")
    parser.add_argument('din', metavar='dirin', nargs='?', type=str,
                        help="The directory containing the prepared.icc file"
                        "and the metdata.yml file.")
    args = parser.parse_args()
    print(args.din)
    main(args.din)
