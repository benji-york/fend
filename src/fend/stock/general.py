import abc
from dataclasses import dataclass
from pathlib import Path


class File:
    """A file, line, and optionally column location."""

    path: Path
    lines: list[str]

    def __init__(self, path: Path):
        self.path = Path(path)

    @property
    def lines(self):
        return self.path.read_text().splitlines(keepends=True)


class Project:
    """A representation of an entire project that is to be validated."""

    def get_files(self) -> list[Path]:
        return [File('my_file.py')]


@dataclass(frozen=True)
class Location:
    """A file, line, and optionally column location."""

    file_path: Path
    line: int | None  # line numbers start at 1
    column: int | None  # column numbers start at 1

    def __post_init__(self) -> None:
        assert self.line is None or self.line >= 1, 'line numbers start at 1'
        assert self.column is None or self.column >= 1, 'column numbers start at 1'
        if self.line is not None:
            assert self.column is not None, 'line and column must both be None or not'


class Pattern(abc.ABC):
    """An aspect of a project that can be enforced.

    e.g., there is a "check" target in the Makefile or the last version number in the
    changelog is the same as the current project version number from pyproject.toml.
    """

    id: str  # e.g., 'trailing-whitespace'
    summary: str  # e.g., 'trailing whitespace'

    def __post_init__(self) -> None:
        assert '\n' not in self.summary, 'summaries must not contain newlines'
        assert len(self.summary) <= 80, 'summaries must be 80 characters or fewer'
        assert ' ' not in self.id, 'IDs may not contain spaces'

    @abc.abstractmethod
    def check(project: Project) -> list['Violation']:
        ...

    def validate(self):
        """Verify that the pattern does not break any known rules."""
        assert ' ' not in self.id


@dataclass(frozen=True)
class Violation:
    """A violation of a pattern and optionally how to fix it."""

    pattern: Pattern
    location: Location
    before: list[str]
    after: list[str]

    def __post_init__(self) -> None:
        assert all(line[-1] == '\n' for line in self.before)
        assert all(line[-1] == '\n' for line in self.after)

########################################################################################
# Everything above this line will eventually live someplace else.

class TrailingWhitespace(Pattern):
    """This pattern idientifies lines with trailing whitespace."""

    id = 'trailing-whitespace'
    summary = 'trailing whitespace'

    def check(self, project: Project) -> list[Violation]:
        files = project.get_files()
        for file in files:
            violations = []
            after_line_index = 1
            for line_index, line in enumerate(file.lines):
                after_line = line.rstrip() + '\n'
                if after_line != line:
                    location = Location(file.path, line=line_index+1, column=1)
                    summary = 'trailing whitespace'
                    violations.append(
                        Violation(self, location, before=[line], after=[after_line]))
        return violations


class StarPhony(Pattern):
    def check(project: Project) -> list[Violation]:
        files = Project.get_files('Makefile.*')
        for file in files:
            phony_declaration = '.PHONY: ★ '
            given_header = file.lines[: len(standard_header)]

            violations = []
            after_line_index = 1
            for line_index, line in reversed(enumerate(file.lines)):
                if line.startswith(phony_declaration):
                    break
                if line.strip() == '':
                    target_line_number = line_index + 1
                    target_line = line
            else:
                location = Location(file.path, line=target_line_number, column=1)
                summary = 'Makefile does not include star PHONY declaration.'
                violations.append(
                    Message(
                        summary, location, before=[line], after=[phony_declaration + '\n', line]
                    )
                )
        return violations

patterns = {
    TrailingWhitespace,
}
