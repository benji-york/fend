import fend
from pathlib import Path
import textwrap
import unittest
from ..make import (
    SuperfolousSpaceInCall,
    _extract_call_arguments,
    _extract_targets,
)
from fend import File, Location, Pattern, Project, Violation

corpus_path = Path(fend.__file__).parent.joinpath('test/corpus/make/')


class Test_extract_targets(unittest.TestCase):
    """Tests for the _extract_targets() function."""

    def test_empty_file(self):
        """An empty Makefile has no targets."""
        self.assertEqual(_extract_targets(''), [])

    def test_no_targets(self):
        """A non-empty Makefile may also have no targets."""
        self.assertEqual(_extract_targets('x := "value"'), [])

    def test_target(self):
        """A target is detected."""
        text = textwrap.dedent(
            """\
            x := "foo"
            check: test lint
        """
        )
        self.assertEqual(_extract_targets(text), ['check'])


class Test_extract_call_arguments(unittest.TestCase):
    """Tests for the _extract_call_arguments() function."""

    def test_extracting_arguments(self):
        """The _extract_call_arguments() function can extract a calls arguments."""
        self.assertEqual(
            _extract_call_arguments('$(call one)'),
            ['one'],
        )
        self.assertEqual(
            _extract_call_arguments('$(call one,two,three)'),
            ['one', 'two', 'three'],
        )
        self.assertEqual(  # test leading whitespace in arguments
            _extract_call_arguments('$(call one, two,  three)'),
            ['one', ' two', '  three'],
        )
        self.assertEqual(  # test trailing whitespace in arguments
            _extract_call_arguments('$(call one ,two  ,three   )'),
            ['one ', 'two  ', 'three   '],
        )

    def test_nested_calls(self):
        """A call within a call is represented in the output."""
        self.assertEqual(
            _extract_call_arguments('$(call one, $(eval $(value "string")),three )'),
            [
                'one',
                ' $(eval $(value "string"))',
                '$(value "string")',
                '"string"',
                'three ',
            ],
        )

    def test_multi_line_calls(self):
        """If a call spans multiple lines, leading whitespace is stripped from args."""
        self.assertEqual(
            _extract_call_arguments('$(call one,\n\ttwo,\n    three)'),
            ['one', 'two', 'three'],
        )


class TestSuperfolousSpaceInCall(unittest.TestCase):
    """Tests for the SuperfolousSpaceInCall class."""

    def test_empty_makefile(self):
        """If the Makefile is completely empty, no messages are reported."""
        self.assertEqual(
            SuperfolousSpaceInCall().check(
                Project.from_file_path(corpus_path / 'empty.mk')
            ),
            [],
        )

    def test_no_extra_spaces(self):
        """If there are no extra spaces, no message is generated."""
        self.assertEqual(
            SuperfolousSpaceInCall().check(
                Project.from_file_path(corpus_path / 'trailing-whitespace.mk')
            ),
            [],
        )

    def test_extra_spaces(self):
        """If there are extra spaces, a message describing the issue is generated."""
        text = 'x := $(call function, one)\n'
        self.assertEqual(
            SuperfolousSpaceInCall().check(Project.from_text(text)),
            [
                Violation(
                    tags=('make/superfluous-space-in-call',),
                    summary='function call includes superfluous space',
                    location=Location(
                        file_path=Path('/tmp/fake/path'), line=1, column=22
                    ),
                    before=['x := $(call function, one)\n'],
                    after=['x := $(call function,one)\n'],
                )
            ],
        )

    def test_multiple_spaces(self):
        """If there are more than one extra space, a single message is generated."""
        text = 'x := $(call function,    one)\n'
        self.assertEqual(
            SuperfolousSpaceInCall().check(Project.from_text(text)),
            [
                Violation(
                    tags=('make/superfluous-space-in-call',),
                    summary='function call includes superfluous space',
                    location=Location(
                        file_path=Path('/tmp/fake/path'), line=1, column=22
                    ),
                    before=['x := $(call function,    one)\n'],
                    after=['x := $(call function,one)\n'],
                )
            ],
        )

    def test_multiple_instances_of_extra_spaces(self):
        """More than one group of extra spaces means a message is generated for each."""
        text = 'x := $(call function, one, two, three)\n'
        violations = SuperfolousSpaceInCall().check(Project.from_text(text))
        self.assertEqual(len(violations), 3)
        violation_columns = []
        for violation in violations:
            self.assertIn('make/superfluous-space-in-call', violation.tags)
            self.assertEqual(len(violation.tags), 1)
            # each violation happened at a different column
            self.assertNotIn(violation.location.column, violation_columns)
            violation_columns.append(violation.location.column)

        assert len(violation_columns) == 3, 'all violation columns were seen'
