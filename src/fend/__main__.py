import difflib
from pathlib import Path
import sys
import typer
from typing import Optional
from fend import File, Location, Pattern, Project, Violation
from fend.stock import general


def _fix(violation: Violation) -> None:
    lines = violation.location.file.lines
    line_index = violation.location.line - 1
    lines[line_index : line_index + len(violation.before)] = violation.after
    violation.location.file_path.write_text(''.join(lines))

app = typer.Typer()

def _find_enabled_patterns(enable: list[str]) -> list[Pattern]:
    enabled_patterns = []
    for pattern_id, pattern in general.patterns.items():
        assert pattern_id == pattern.id, 'pattern ID must be consistent'
        if pattern_id in enable:
            pattern_instance = pattern()
            pattern_instance.validate()
            enabled_patterns.append(pattern_instance)
    return enabled_patterns


@app.command()
def check(filespec: str = typer.Argument(...), diff: bool = False, enable: Optional[list[str]] = typer.Option(None)) -> None:
    """Check one or more files for compliance with one or more enabled patterns."""
    enabled_patterns = _find_enabled_patterns(enable or [])
    violations = []
    for pattern in enabled_patterns:
        violations.extend(pattern.check(Project(filespec)))

    for violation in violations:
        print(
            f'{violation.location.file_path}:{violation.location.line}'
            f' {violation.summary} ({", ".join(violation.tags)})'
        )
        if diff:
            differ = difflib.Differ()
            print(''.join(list(differ.compare(violation.before, violation.after))))


@app.command()
def fix(filespec: str = typer.Argument(...), enable: Optional[list[str]] = typer.Option(None)) -> None:
    """Fix any found violations of one or more enabled patterns."""
    enabled_patterns = _find_enabled_patterns(enable or [])
    violations = []
    for pattern in enabled_patterns:
        violations.extend(pattern.check(Project(filespec)))

    for violation in violations:
        _fix(violation)

main = app

if __name__ == "__main__":
    main()
