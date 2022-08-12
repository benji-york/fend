import sys
import difflib
from fend.stock import general
from fend import File, Location, Pattern, Violation, Project

def fix(violation: Violation):
    lines = violation.location.file.lines
    line_index = violation.location.line - 1
    lines[line_index:line_index+len(violation.before)] = violation.after
    violation.location.file_path.write_text(''.join(lines))


def main(argv=sys.argv):
    violations = general.TrailingWhitespace().check(general.Project())

    for violation in violations:
        if 'check' in sys.argv:
            print(f'{violation.location.file_path}:{violation.location.line} {violation.pattern.summary} ({violation.pattern.id})')
            if '--diff' in argv:
                differ = difflib.Differ()
                diff = list(differ.compare(violation.before, violation.after))
                print(''.join(diff))
        elif 'fix' in sys.argv:
            fix(violation)


if __name__ == '__main__':
    main()
