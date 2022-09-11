"""Fend patterns for Makefiles."""

import re
import subprocess
import tree_sitter
from typing import Any
from fend import File, Location, Pattern, Project, Violation
from pathlib import Path
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
# make it easier to construct Locations from nodes

# other sources for rules:
# https://style-guides.readthedocs.io/en/latest/makefile.html
# https://www.gnu.org/prep/standards/html_node/Makefile-Basics.html
# https://clarkgrubb.com/makefile-style-guide
# http://make.mad-scientist.net/papers/rules-of-makefiles/
# https://github.com/mrtazz/checkmake


def _extract_targets(text: str) -> str:
    """Extract Make targets from a Makefile."""
    parser = Parser()
    parser.set_language(MAKE_LANGUAGE)
    tree = parser.parse(bytes(text, 'utf8'))
    return list(map(_node_text, _find_nodes_by_type(tree.root_node, 'targets')))


def _extract_call_nodes(lines: str) -> Any:  # XXX really a tree-sitter node
    """Extract Make function calls from a (potentially) multi-line string."""
    parser = Parser()
    parser.set_language(MAKE_LANGUAGE)
    tree = parser.parse(bytes(lines, 'utf8'))
    return _find_nodes_by_type(tree.root_node, 'function_call')


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

    def __init__(self, file: File):
        self._file = file
        self._parse_targets()

    def _parse_targets(self):
        self.targets = frozenset(_extract_targets(self._file.text))


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


def get_children_by_type(
    node: Any, child_type: str
) -> list[Any]:  # XXX really list[node]
    return [child for child in node.children if child.type == child_type]


def line_and_column_from_node(node: Any) -> tuple[int, int]:  # XXX really node
    line, column = node.start_point
    return (line + 1, column + 1)


class SuperfolousSpaceInCall(Pattern):
    """This pattern identifies and fixes extra spaces in uses of $(call ...)."""

    id = 'make/superfluous-space-in-call'

    def check(self, project: Project) -> list[Violation]:
        violations = []
        for file in project.files:
            for call in _extract_call_nodes(file.text):
                for argument in _find_nodes_by_type(call, 'argument'):
                    text = argument.text.decode('utf-8')
                    if not text.startswith(' '):
                        continue

                    line_no, column_no = line_and_column_from_node(argument)
                    # If the argument is entirely on one line, it is easy to make make a
                    # before and after.
                    if argument.start_point[0] == argument.end_point[0]:
                        before_line = file.get_line(line_no)
                        before = [before_line]
                        after = [
                            before_line[: argument.start_point[1]]
                            + text.lstrip()
                            + before_line[argument.end_point[1] :]
                        ]
                    else:
                        before = None
                        after = None

                    location = Location(file.path, line=line_no, column=column_no)
                    violations.append(
                        Violation(
                            (self.id,),
                            f'function call includes superfluous space',
                            location,
                            before=before,
                            after=after,
                        )
                    )
        return violations


patterns: set = {RequiredTargets}
