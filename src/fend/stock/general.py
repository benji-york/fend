import abc
from dataclasses import dataclass
from pathlib import Path
from fend import File, Location, Pattern, Violation, Project


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

patterns = {
    TrailingWhitespace,
}
