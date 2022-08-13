"""Fend patterns for Makefiles."""

from fend import File, Location, Pattern, Project, Violation
import re
import subprocess
from pathlib import Path

# TODO
# required targets (build, test, lint, check, clean)
# remove unneeded spaces after commas in $call() invocations
# no non-phony target depends on a phony target
# no phony target depends on a non-phony target
# see https://clarkgrubb.com/makefile-style-guide about above two

# other sources for rules:
# https://style-guides.readthedocs.io/en/latest/makefile.html
# https://www.gnu.org/prep/standards/html_node/Makefile-Basics.html
# https://clarkgrubb.com/makefile-style-guide
# http://make.mad-scientist.net/papers/rules-of-makefiles/
# https://github.com/mrtazz/checkmake


_required_targets = {'build', 'lint', 'test', 'check', 'clean'}


class _Makefile:
    """Information about a Makefile."""

    def __init__(self, filepath: str | Path):
        self._filepath = Path(filepath)
        self._parse()

    def _parse(self):
        process = subprocess.run(['make', '-pn', self._filepath], check=True,
            encoding='utf8',
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )
        targets = set()
        line_iter = iter(process.stdout.splitlines())
        for line in process.stdout.splitlines():
            #if line.startswith('# Not a target:'):
            #    import pdb;pdb.set_trace()
            #    next(line_iter)
            #    continue
            if match := re.match('^(\S+):.*$', line):
                targets.add(match.group(1))

        self.targets = frozenset(targets)


class RequiredTargets(Pattern):
    """This pattern idientifies targets that should always be available."""

    id = 'make/missing-required-target'

    def check(self, project: Project) -> list[Violation]:
        files = project.get_files()
        violations = []
        for file in files:
            makefile = _Makefile(file.path)
            for required_target in _required_targets:
                if required_target not in makefile.targets:
                    location = Location(file.path, line=1, column=1)
                    violations.append(
                        Violation(
                            (self.id,),
                            f'missing required target in Makefile: {required_target}',
                            location,
                            before = None,
                            after = None,
                        )
                    )
        return violations


patterns: set = {RequiredTargets}
