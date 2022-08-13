import abc
from dataclasses import dataclass
from fend import File, Location, Pattern, Project, Violation
from pathlib import Path
from typing import Any


class TrailingWhitespace(Pattern):
    """This pattern idientifies lines with trailing whitespace."""

    id = 'trailing-whitespace'

    def check(self, project: Project) -> list[Violation]:
        files = project.get_files()
        violations = []
        for file in files:
            for line_index, line in enumerate(file.lines):
                after_line = line.rstrip() + '\n'
                if after_line != line:
                    location = Location(file.path, line=line_index + 1, column=1)
                    violations.append(
                        Violation(
                            ('trailing-whitespace',),
                            'trailing whitespace',
                            location,
                            before=[line],
                            after=[after_line],
                        )
                    )
        return violations


patterns: set = {TrailingWhitespace}
