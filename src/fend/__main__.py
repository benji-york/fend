import sys
import difflib
from fend.stock import general

def main(argv=sys.argv):
    violations = general.TrailingWhitespace().check(general.Project())

    for violation in violations:
        print(f'{violation.location.file_path}:{violation.location.line} {violation.pattern.summary} ({violation.pattern.id})')
        if '--diff' in argv:
            differ = difflib.Differ()
            diff = list(differ.compare(violation.before, violation.after))
            print(''.join(diff))


if __name__ == '__main__':
    main()
