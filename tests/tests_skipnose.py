from __future__ import print_function, unicode_literals
from unittest import TestCase

import mock
from nose.case import FunctionTestCase
from nose.plugins.skip import SkipTest

from skipnose.skipnose import SkipNose, walk_subfolders


class TestWalkSubfolders(TestCase):
    @mock.patch('os.walk')
    def test_walk_subfolders(self, mock_walk):
        """
        Test that walk_subfolders returns os-joined paths
        as returned by os.walk
        """
        mock_walk.return_value = iter((
            ('path', ('a', 'b', 'c'), ('d', 'e', 'f')),
            ('other', ('q', 'w', 'e'), ('r', 't', 'y')),
        ))
        expected = [
            'path/a',
            'path/b',
            'path/c',
            'other/q',
            'other/w',
            'other/e',
        ]
        actual = walk_subfolders('foo')
        self.assertListEqual(list(actual), expected)
        mock_walk.assert_called_once_with('foo')


@mock.patch('skipnose.skipnose.print', mock.MagicMock(), create=True)
class TestSkipNoseConfig(TestCase):
    """
    Test class for skipnose configurations
    """

    def setUp(self):
        super(TestSkipNoseConfig, self).setUp()
        self.plugin = SkipNose()

    def test_options(self):
        """
        Test skipnose adds all configs to nose with
        correct defaults taken from environment variables.
        """
        env = {
            'NOSE_SKIPNOSE_INCLUDE': 'including',
            'NOSE_SKIPNOSE_EXCLUDE': 'excluding',
            'NOSE_SKIPNOSE': 'on',
        }
        mock_parser = mock.MagicMock()

        self.plugin.options(mock_parser, env)

        mock_parser.add_option.assert_has_calls(
            [
                mock.call('--with-skipnose',
                          action='store_true',
                          default=True,
                          dest=mock.ANY,
                          help=mock.ANY),
                mock.call('--skipnose-debug',
                          action='store_true',
                          default=False,
                          dest=mock.ANY,
                          help=mock.ANY),
                mock.call('--skipnose-include',
                          action='append',
                          default=['including'],
                          dest=mock.ANY,
                          help=mock.ANY),
                mock.call('--skipnose-exclude',
                          action='append',
                          default=['excluding'],
                          dest=mock.ANY,
                          help=mock.ANY),
            ]
        )

    @mock.patch('sys.exit')
    @mock.patch('os.path.exists')
    def test_configure(self, mock_path_exists, mock_sys_exit):
        """
        Test that configure sets class attributes correctly
        """
        mock_options = mock.MagicMock(
            skipnose_debug=mock.sentinel.debug,
            skipnose_include=['a', 'b:c'],
            skipnose_exclude=['x', 'y'],
            skipnose_skip_tests='foo.json',
        )
        mock_path_exists.return_value = True
        mock_open = mock.MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = (
            b'{"skip_tests": ["one", "two"]}'
        )
        mock_sys_exit.side_effect = SystemExit

        with mock.patch('skipnose.skipnose.open', mock_open, create=True):
            self.plugin.configure(mock_options, None)

        self.assertTrue(self.plugin.enabled)
        self.assertEqual(self.plugin.debug, mock.sentinel.debug)
        self.assertEqual(self.plugin.skipnose_include, [['a'], ['b', 'c']])
        self.assertEqual(self.plugin.skipnose_exclude, ['x', 'y'])
        self.assertEqual(self.plugin.skipnose_skip_tests, ['one', 'two'])
        mock_open.assert_called_once_with('foo.json', 'rb')

    @mock.patch('sys.exit')
    @mock.patch('os.path.exists')
    def test_configure_error(self, mock_path_exists, mock_sys_exit):
        """
        Test that configure sets class attributes correctly when
        invalid skip-tests path is provided and nose exits
        """
        mock_options = mock.MagicMock(
            skipnose_debug=mock.sentinel.debug,
            skipnose_include=['a', 'b:c'],
            skipnose_exclude=['x', 'y'],
            skipnose_skip_tests='foo.data',
        )
        mock_path_exists.return_value = False
        mock_open = mock.MagicMock()
        mock_sys_exit.side_effect = SystemExit

        with mock.patch('skipnose.skipnose.open', mock_open, create=True):
            with self.assertRaises(SystemExit):
                self.plugin.configure(mock_options, None)

        self.assertTrue(self.plugin.enabled)
        self.assertEqual(self.plugin.debug, mock.sentinel.debug)
        self.assertEqual(self.plugin.skipnose_include, [['a'], ['b', 'c']])
        self.assertEqual(self.plugin.skipnose_exclude, ['x', 'y'])
        self.assertIsNone(self.plugin.skipnose_skip_tests)
        self.assertFalse(mock_open.called)
        mock_sys_exit.assert_called_once_with(1)


@mock.patch('skipnose.skipnose.print', mock.MagicMock(), create=True)
class TestSkipNose(TestCase):
    """
    Test class for skipnose functionality
    """

    def setUp(self):
        super(TestSkipNose, self).setUp()
        self.plugin = SkipNose()
        self.plugin.debug = True
        self.test_paths = [
            '/test',
            '/test/bar/cat/one',
            '/test/bar/cat/one/subone',
            '/test/bar/cat/two',
            '/test/bar/dog/one',
            '/test/bar/dog/one/api',
            '/test/bar/dog/one/api/subapi',
            '/test/bar/dog/one/api/subapi/moreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi/api',
            '/test/foo',
            '/test/foo/api',
            '/test/foo/api/subapi',
            '/test/foo/api/subapi/moreapi',
            '/test/foo/api/subapi/evenmoreapi',
            '/test/foo/api/subsubapi',
            '/test/foo/api/subsubapi/toomuchapi',
            '/test/foo/nonapi',
            '/test/foo/nonapi/folderone',
            '/test/foo/nonapi/foldertwo',
            '/test/foo/nonapi/foldertwo/morestuff',
            '/test/foo/nonapi/foldertwo/toomuch',
        ]

    def _mock_walk_subfolders(self, path):
        """
        Function to be provided to mock.side_effect to replace
        walk_subfolders functionality to use test paths.
        """
        paths = list(map(lambda i: i, self.test_paths))
        index = paths.index(path)
        if len(paths) > index + 1:
            return filter(lambda i: i.startswith(path), paths[index:])
        else:
            return []

    def _test_paths(self, valid):
        for path in self.test_paths:
            expected = None if path in valid else False
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected,
                             '{} != {} for {}'.format(actual, expected, path))

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include(self, mock_walk_subfolders):
        """
        Test wantDirectory with include parameter
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders
        valid = [
            '/test',
            '/test/bar/dog/one',
            '/test/bar/dog/one/api',
            '/test/bar/dog/one/api/subapi',
            '/test/bar/dog/one/api/subapi/moreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi/api',
            '/test/foo',
            '/test/foo/api',
            '/test/foo/api/subapi',
            '/test/foo/api/subapi/moreapi',
            '/test/foo/api/subapi/evenmoreapi',
            '/test/foo/api/subsubapi',
            '/test/foo/api/subsubapi/toomuchapi',
        ]

        self.plugin.skipnose_include = [['api']]
        self._test_paths(valid)

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include_multiple_or(self, mock_walk_subfolders):
        """
        Test wantDirectory with multiple include OR parameters
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders
        valid = [
            '/test',
            '/test/bar/dog/one',
            '/test/bar/dog/one/api',
            '/test/bar/dog/one/api/subapi',
            '/test/bar/dog/one/api/subapi/moreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi',
            '/test/bar/dog/one/api/subapi/evenmoreapi/api',
            '/test/foo',
            '/test/foo/api',
            '/test/foo/api/subapi',
            '/test/foo/api/subapi/moreapi',
            '/test/foo/api/subapi/evenmoreapi',
            '/test/foo/api/subsubapi',
            '/test/foo/api/subsubapi/toomuchapi',
            '/test/foo/nonapi',
            '/test/foo/nonapi/folderone',
            '/test/foo/nonapi/foldertwo',
            '/test/foo/nonapi/foldertwo/morestuff',
            '/test/foo/nonapi/foldertwo/toomuch',
        ]

        self.plugin.skipnose_include = [['api', 'foo']]
        self._test_paths(valid)

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include_multiple_and(self, mock_walk_subfolders):
        """
        Test wantDirectory with multiple include OR parameters
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders
        valid = [
            '/test',
            '/test/foo',
            '/test/foo/api',
            '/test/foo/api/subapi',
            '/test/foo/api/subapi/moreapi',
            '/test/foo/api/subapi/evenmoreapi',
            '/test/foo/api/subsubapi',
            '/test/foo/api/subsubapi/toomuchapi',
        ]

        self.plugin.skipnose_include = [['api'], ['foo']]
        self._test_paths(valid)

    def test_want_directory_exclude(self):
        """
        Test wantDirectory with exclude parameter
        """
        valid = [
            '/test',
            '/test/bar/cat/one',
            '/test/bar/cat/one/subone',
            '/test/bar/cat/two',
            '/test/bar/dog/one',
            '/test/bar/dog/one/api/subapi',  # implicitly skipped by walk
            '/test/bar/dog/one/api/subapi/moreapi',  # noqa implicitly skipped by walk
            '/test/bar/dog/one/api/subapi/evenmoreapi',  # noqa implicitly skipped by walk
            '/test/foo',
            '/test/foo/api/subapi',  # implicitly skipped by walk
            '/test/foo/api/subapi/moreapi',  # implicitly skipped by walk
            '/test/foo/api/subapi/evenmoreapi',  # implicitly skipped by walk
            '/test/foo/api/subsubapi',  # implicitly skipped by walk
            '/test/foo/api/subsubapi/toomuchapi',  # implicitly skipped by walk
            '/test/foo/nonapi',
            '/test/foo/nonapi/folderone',
            '/test/foo/nonapi/foldertwo',
            '/test/foo/nonapi/foldertwo/morestuff',
            '/test/foo/nonapi/foldertwo/toomuch',
        ]
        self.plugin.skipnose_exclude = ['api']
        self._test_paths(valid)

    def test_want_directory_exclude_multiple(self):
        """
        Test wantDirectory with multiple exclude parameter
        """
        valid = [
            '/test',
            '/test/bar/cat/one',
            '/test/bar/cat/one/subone',
            '/test/bar/cat/two',
            '/test/bar/dog/one',
            '/test/bar/dog/one/api/subapi',  # implicitly skipped by walk
            '/test/bar/dog/one/api/subapi/moreapi',  # noqa implicitly skipped by walk
            '/test/bar/dog/one/api/subapi/evenmoreapi',  # noqa implicitly skipped by walk
            '/test/foo/api/subapi',  # implicitly skipped by walk
            '/test/foo/api/subapi/moreapi',  # implicitly skipped by walk
            '/test/foo/api/subapi/evenmoreapi',  # implicitly skipped by walk
            '/test/foo/api/subsubapi',  # implicitly skipped by walk
            '/test/foo/api/subsubapi/toomuchapi',  # implicitly skipped by walk
            '/test/foo/nonapi',  # implicitly skipped by walk
            '/test/foo/nonapi/folderone',  # implicitly skipped by walk
            '/test/foo/nonapi/foldertwo',  # implicitly skipped by walk
            '/test/foo/nonapi/foldertwo/morestuff',  # noqa implicitly skipped by walk
            '/test/foo/nonapi/foldertwo/toomuch',  # implicitly skipped by walk
        ]
        self.plugin.skipnose_exclude = ['api', 'foo']
        self._test_paths(valid)

    def test_start_test_no_tests_to_skip(self):
        self.plugin.skipnose_skip_tests = None

        self.assertIsNone(self.plugin.startTest(mock.Mock()))

    def test_start_test_function_test_case(self):
        self.plugin.skipnose_skip_tests = ['one', 'two', 'foo.bar']

        def test():
            """"""

        mock_test = mock.MagicMock()
        mock_test.test = mock.MagicMock(spec=FunctionTestCase)
        mock_test.test.test = mock.MagicMock(__module__='foo', __name__='bar')
        mock_test.test._testMethodName = 'method'
        mock_test.test.method = test

        self.plugin.startTest(mock_test)

        replaced_method = mock_test.test.method
        self.assertIsNot(replaced_method, test)
        self.assertTrue(callable(replaced_method))
        with self.assertRaises(SkipTest):
            replaced_method()

    def test_start_test_method_test_case(self):
        self.plugin.skipnose_skip_tests = ['one', 'two', 'foo.Foo.method']

        class Foo(object):
            def method(self):
                """"""

        Foo.__module__ = 'foo'
        instance = Foo()
        test = instance.method

        mock_test = mock.MagicMock()
        mock_test.test = instance
        mock_test.test._testMethodName = 'method'
        mock_test.test.method = test

        self.plugin.startTest(mock_test)

        replaced_method = mock_test.test.method
        self.assertIsNot(replaced_method, test)
        self.assertTrue(callable(replaced_method))
        with self.assertRaises(SkipTest):
            replaced_method()
