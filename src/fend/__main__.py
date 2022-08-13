import difflib
from pathlib import Path
import sys
import typer
from typing import Optional
from fend import File, Location, Pattern, Project, Violation
from fend.stock import general, make


_app = typer.Typer()


@_app.callback()
def _documentation():
    """Ensure all of your projects follow the same patterns.

    Fend manages a collection of linters (both pre-built and custom) to enforce patterns
    across all of your projects.
    """
    # This function exists only to provid the text above for the CLI.


def _fix(violation: Violation) -> None:
    lines = violation.location.file.lines
    line_index = violation.location.line - 1
    lines[line_index : line_index + len(violation.before)] = violation.after
    violation.location.file_path.write_text(''.join(lines))

def _find_patterns():
    return general.patterns | make.patterns

def _find_enabled_patterns(enable: list[str]) -> list[Pattern]:
    enabled_patterns = []
    for pattern in _find_patterns():
        if pattern.id in enable:
            pattern_instance = pattern()
            pattern_instance.validate()
            enabled_patterns.append(pattern_instance)
    return enabled_patterns


def _complete_patterns():
    """Find the list of patterns avaialble to the user.  Used in CLI completion."""
    return [pattern.id for pattern in _find_patterns()]


@_app.command()
def check(
    filespec: str = typer.Argument(...),
    diff: bool = typer.Option(False, help='Print a fix for each violation as a diff.'),
    enable: Optional[list[str]] = typer.Option(
        None, help='Enable the given patterns.', autocompletion=_complete_patterns
    ),
) -> None:
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


@_app.command()
def fix(
    filespec: str = typer.Argument(...),
    enable: Optional[list[str]] = typer.Option(
        None, help='Enable the given patterns.', autocompletion=_complete_patterns
    ),
) -> None:
    """Fix any found violations of one or more enabled patterns."""
    enabled_patterns = _find_enabled_patterns(enable or [])
    violations = []
    for pattern in enabled_patterns:
        violations.extend(pattern.check(Project(filespec)))

    for violation in violations:
        _fix(violation)


main = _app
