import argparse
import sys

def main(fin):
    text = fin.read()
    s = list(text)

    close = False
    news = []
    while i := s.index('_'):
        news.append(s[:i])
        s = s[i+1:]
        if close:
            news.append('</i>')
        else:
            news.append('<i>')

        close = not close
        if not len(news) % 100:
            print(len(s))
    with open(fin + '.out', 'wt') as fout:
        fout.write(''.join(news))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert markdown underscores"
                                     "to <i> tags")
    parser.add_argument('fin', metavar='filein', nargs='?',
                        type=argparse.FileType('rt'), default=sys.stdin,
                        help="The text file")
    args = parser.parse_args()

    main(args.fin)
