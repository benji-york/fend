"""Fend patterns for Makefiles."""

from fend import File, Location, Pattern, Project, Violation
import re
import subprocess
import tree_sitter
from pathlib import Path

## XXX This might should go somewhere else.
from tree_sitter import Language, Parser


MAKE_LANGUAGE = tree_sitter.Language('build/my-languages.so', 'make')


def _find_nodes_by_type(root, type_: str):
    results = []

    def find_nodes(node):
        if node.type == type_:
            results.append(node)
        for child in node.children:
            find_nodes(child)

    find_nodes(root)
    return results


def _node_text(node):
    return node.text.decode('utf8')


# TODO
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


def _extract_calls(lines: str) -> str:
    """Extract Make function calls from a (potentially) multi-line string."""
    parser = Parser()
    parser.set_language(MAKE_LANGUAGE)
    tree = parser.parse(bytes(lines, 'utf8'))
    return list(map(_node_text, _find_nodes_by_type(tree.root_node, 'function_call')))


def _extract_call_arguments(call: str) -> str:
    """Extract the arguments from a Make function call."""
    assert call.startswith('$(call ')
    parser = Parser()
    parser.set_language(MAKE_LANGUAGE)
    tree = parser.parse(bytes(call, 'utf8'))
    assert tree.root_node.child_count == 1, 'text must be simple'
    assert tree.root_node.children[0].type == 'function_call', 'text must be a call'
    arguments = _find_nodes_by_type(tree.root_node, 'argument')
    return list(map(_node_text, arguments))


_required_targets = {'build', 'lint', 'test', 'check', 'clean'}


class _Makefile:
    """Information about a Makefile."""

    def __init__(self, filepath: str | Path):
        self._filepath = Path(filepath)
        self._parse()

    def _parse(self):
        process = subprocess.run(
            ['make', '-pn', '-f', self._filepath],
            encoding='utf8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        targets = set()
        line_iter = iter(process.stdout.splitlines())
        for line in line_iter:
            if line.startswith('# Not a target:'):
                next(line_iter)
                continue
            if match := re.match('^(\S+):.*$', line):
                targets.add(match.group(1))

        self.targets = frozenset(targets)

    def parse_calls(self):
        return _extract_calls(self._filepath.read_text('utf-8'))


class RequiredTargets(Pattern):
    """This pattern identifies targets that should always be available."""

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
                            before=None,
                            after=None,
                        )
                    )
        return violations


class SuperfolousSpaceInCall(Pattern):
    """This pattern identifies and fixes extra spaces in uses of $(call ...)."""

    id = 'make/superfluous-space-in-call'

    def check(self, project: Project) -> list[Violation]:
        files = project.get_files()
        violations = []
        for file in files:
            makefile = _Makefile(file.path)
            for call in makefile.parse_calls():
                for arguments in _extract_call_arguments(call):
                    location = Location(file.path, line=line_index + 1, column=1)
                    violations.append(
                        Violation(
                            (self.id,),
                            f'missing required target in Makefile: {required_target}',
                            location,
                            before=None,
                            after=None,
                        )
                    )
        return violations


patterns: set = {RequiredTargets}
