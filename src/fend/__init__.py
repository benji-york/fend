import abc
from dataclasses import dataclass
from pathlib import Path


class File:
    """A file, line, and optionally column location."""

    path: Path

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @property
    def lines(self) -> list[str]:
        return self.path.read_text().splitlines(keepends=True)


class Project:
    """A representation of an entire project that is to be validated."""

    def __init__(self, filespec: str) -> None:
        self.filespec = filespec

    def get_files(self) -> list[File]:
        return [File('my_file.py')]


@dataclass(frozen=True)
class Location:
    """A file, line, and optionally column location."""

    file_path: Path
    line: int  # line numbers start at 1
    column: int | None  # column numbers start at 1

    def __post_init__(self) -> None:
        assert self.line is None or self.line >= 1, 'line numbers start at 1'
        assert self.column is None or self.column >= 1, 'column numbers start at 1'
        if self.line is not None:
            assert self.column is not None, 'line and column must both be None or not'

    @property
    def file(self) -> File:
        return File(self.file_path)


class Pattern(abc.ABC):
    """An aspect of a project that can be enforced.

    e.g., there is a "check" target in the Makefile or the last version number in the
    changelog is the same as the current project version number from pyproject.toml.
    """

    id: str  # e.g., 'trailing-whitespace'

    @abc.abstractmethod
    def check(self, project: Project) -> list['Violation']:
        ...

    def validate(self) -> None:
        """Verify that the pattern does not break any known rules."""
        assert ' ' not in self.id
        assert ' ' not in self.id, 'IDs may not contain spaces'


@dataclass(frozen=True)
class Violation:
    """A violation of a pattern and how to fix it."""

    # Tags that identify the violation from least to most specific.  e.g.,
    # ('trailing-whitespace', 'single-trailing-whitespace-markdown')
    tags: tuple[str]
    # An English, human-readable description of the violation.  e.g., 'a single trailing
    # whitespace in a Markdown document'
    summary: str
    location: Location
    # The lines that encompas the violation, plus any context that is needed for
    # applying the fix.
    before: list[str]
    # The lines that would fix the violation if used to replace the "before" lines.
    after: list[str]

    def __post_init__(self) -> None:
        assert all(line[-1] == '\n' for line in self.before)
        assert all(line[-1] == '\n' for line in self.after)
