import sys
import difflib

def main(argv=sys.argv):
    print('my_file.py:1 trailing whitespace (trailing-whitespace)')
    if '--diff' in argv:
        differ = difflib.Differ()
        diff = list(differ.compare(["print('Hello, World!') \n"], ["print('Hello, World!')\n"]))
        print(''.join(diff))


if __name__ == '__main__':
    main()
