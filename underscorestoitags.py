import argparse
import sys

def main(fin):
    with open(fin, 'rt') as f:
        s = f.read()

    close = False
    news = []
    while (i := s.find('_')) != -1:
        news.append(s[:i])
        s = s[i+1:]
        if close:
            news.append('</i>')
        else:
            news.append('<i>')

        close = not close
    news.append(s)
    with open(fin + '.out', 'wt') as fout:
        fout.write(''.join(news))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert markdown underscores"
                                     "to <i> tags")
    parser.add_argument('fin', type=str, help="The text file")
    args = parser.parse_args()

    main(args.fin)
