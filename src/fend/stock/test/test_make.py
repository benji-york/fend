import fend
import pathlib
import textwrap
import unittest
from ..make import (
    SuperfolousSpaceInCall,
    _extract_call_arguments,
    _extract_calls,
    _extract_targets,
)
from fend import File, Location, Pattern, Project, Violation

corpus_path = pathlib.Path(fend.__file__).parent.joinpath('test/corpus/make/')


class TestCallParser(unittest.TestCase):
    """Tests for the $(call ...) syntax parsing."""

    def test_extracting_calls(self):
        """The _extract_calls() function can extract a call from a line."""
        self.assertEqual(
            _extract_calls('$(call one)'),
            ['$(call one)'],
        )
        self.assertEqual(
            _extract_calls('foo: before $(call one,two,three) after'),
            ['$(call one,two,three)'],
        )
        self.assertEqual(
            _extract_calls('before $(call one, $(eval $(value "string")),three) after'),
            [
                '$(call one, $(eval $(value "string")),three)',
                '$(eval $(value "string"))',
                '$(value "string")',
            ],
        )
        self.assertEqual(
            _extract_calls('first: $(call one), then $(call two), more'),
            ['$(call one)', '$(call two)'],
        )


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

    def test_no_extra_spaces(self):
        """If there are no extra spaces, no message is generated."""
        self.assertEqual(
            SuperfolousSpaceInCall().check(
                Project.from_file_path(corpus_path / 'trailing-whitespace.mk')
            ),
            [],
        )
