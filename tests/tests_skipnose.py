from __future__ import unicode_literals, print_function
import mock
from unittest import TestCase

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

    def test_configure(self):
        """
        Test that configure sets class attributes correctly
        """
        mock_options = mock.MagicMock(
            skipnose_debug=mock.sentinel.debug,
            skipnose_include=mock.sentinel.include,
            skipnose_exclude=mock.sentinel.exclude,
        )

        self.plugin.configure(mock_options, None)

        self.assertTrue(self.plugin.enabled)
        self.assertEqual(self.plugin.debug, mock.sentinel.debug)
        self.assertEqual(self.plugin.skipnose_include, mock.sentinel.include)
        self.assertEqual(self.plugin.skipnose_exclude, mock.sentinel.exclude)


@mock.patch('skipnose.skipnose.print', mock.MagicMock(), create=True)
class TestSkipNose(TestCase):
    """
    Test class for skipnose functionality
    """

    def setUp(self):
        super(TestSkipNose, self).setUp()
        self.plugin = SkipNose()
        self.plugin.debug = True
        self.test_paths = (
            ('/test', ('api-parent', 'foo-parent',)),
            ('/test/bar/cat/one', ('non-api',)),
            ('/test/bar/cat/one/subone', ('non-api',)),
            ('/test/bar/cat/two', ('non-api',)),
            ('/test/bar/dog/one', ('api-parent',)),
            ('/test/bar/dog/one/api', ('api',)),
            ('/test/bar/dog/one/api/subapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/moreapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/evenmoreapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/evenmoreapi/api', ('api-child',)),
            ('/test/foo', ('api-parent-foo', 'foo')),
            ('/test/foo/api', ('api', 'foo-child')),
            ('/test/foo/api/subapi', ('api-child', 'foo-child')),
            ('/test/foo/api/subapi/moreapi', ('api-child', 'foo-child')),
            ('/test/foo/api/subapi/evenmoreapi', ('api-child', 'foo-child')),
            ('/test/foo/api/subsubapi', ('api-child', 'foo-child')),
            ('/test/foo/api/subsubapi/toomuchapi', ('api-child', 'foo-child')),
            ('/test/foo/nonapi', ('non-api', 'foo-child')),
            ('/test/foo/nonapi/folderone', ('non-api', 'foo-child')),
            ('/test/foo/nonapi/foldertwo', ('non-api', 'foo-child')),
            ('/test/foo/nonapi/foldertwo/morestuff', ('non-api', 'foo-child')),
            ('/test/foo/nonapi/foldertwo/toomuch', ('non-api', 'foo-child')),
        )

    def _mock_walk_subfolders(self, path):
        """
        Function to be provided to mock.side_effect to replace
        walk_subfolders functionality to use test paths.
        """
        paths = list(map(lambda i: i[0], self.test_paths))
        index = paths.index(path)
        if len(paths) > index + 1:
            return filter(lambda i: i.startswith(path), paths[index:])
        else:
            return []

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include(self, mock_walk_subfolders):
        """
        Test wantDirectory with include parameter
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders

        self.plugin.skipnose_include = ['api']
        for path, properties in self.test_paths:
            accepted = ('api-parent', 'api-parent-foo', 'api', 'api-child')
            expected = (None if any(map(lambda i: i in properties, accepted))
                        else False)
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected,
                             '{} != {} for {}'.format(actual, expected, path))

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include_multiple(self, mock_walk_subfolders):
        """
        Test wantDirectory with multiple include parameters
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders

        self.plugin.skipnose_include = ['api', 'foo']
        for path, properties in self.test_paths:
            accepted = ('api-parent', 'api', 'api-child', 'foo', 'foo-child')
            expected = (None if any(map(lambda i: i in properties, accepted))
                        else False)
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected,
                             '{} != {} for {}'.format(actual, expected, path))

    def test_want_directory_exclude(self):
        """
        Test wantDirectory with exclude parameter
        """
        self.plugin.skipnose_exclude = ['api']
        for path, properties in self.test_paths:
            # exclude subfolders where parent should be rejected
            if 'api-child' in properties:
                continue
            accepted = ('api-parent', 'api-parent-foo', 'non-api')
            expected = (None if any(map(lambda i: i in properties, accepted))
                        else False)
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected,
                             '{} != {} for {}'.format(actual, expected, path))

    def test_want_directory_exclude_multiple(self):
        """
        Test wantDirectory with multiple exclude parameter
        """
        self.plugin.skipnose_exclude = ['api', 'foo']
        for path, properties in self.test_paths:
            # exclude subfolders where parent should be rejected
            if 'api-child' in properties or 'foo-child' in properties:
                continue
            accepted = ('api-parent', 'non-api', 'foo-parent')
            expected = (None if any(map(lambda i: i in properties, accepted))
                        else False)
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected,
                             '{} != {} for {}'.format(actual, expected, path))
