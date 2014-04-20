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


class TestSkipNose(TestCase):
    def setUp(self):
        self.plugin = SkipNose()
        self.test_paths = (
            ('/test', ('api-parent',)),
            ('/test/bar/cat/one', ('non-api',)),
            ('/test/bar/cat/one/subone', ('non-api',)),
            ('/test/bar/cat/two', ('non-api',)),
            ('/test/bar/dog/one', ('api-parent',)),
            ('/test/bar/dog/one/api', ('api',)),
            ('/test/bar/dog/one/api/subapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/moreapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/evenmoreapi', ('api-child',)),
            ('/test/bar/dog/one/api/subapi/evenmoreapi/crazyapi', ('api-child',)),
            ('/test/foo', ('api-parent', 'foo')),
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
            ('/test/foo/nonapi/foldertwo/toomuchstuff', ('non-api', 'foo-child')),
        )

    def _mock_walk_subfolders(self, path):
        """
        Function to be provided to mock.side_effect to replace
        walk_subfolders functionality to use test paths.
        """
        paths = map(lambda i: i[0], self.test_paths)
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
            accepted = ('api-parent', 'api', 'api-child')
            expected = None if any(map(lambda i: i in properties, accepted)) else False
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected)

    @mock.patch('skipnose.skipnose.walk_subfolders')
    def test_want_directory_include_multiple(self, mock_walk_subfolders):
        """
        Test wantDirectory with multiple include parameters
        """
        mock_walk_subfolders.side_effect = self._mock_walk_subfolders

        self.plugin.skipnose_include = ['api', 'foo']
        for path, properties in self.test_paths:
            accepted = ('api-parent', 'api', 'api-child', 'foo', 'foo-child')
            expected = None if any(map(lambda i: i in properties, accepted)) else False
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected)

    def test_want_directory_exclude(self):
        """
        Test wantDirectory with exclude parameter
        """
        self.plugin.skipnose_exclude = ['api']
        for path, properties in self.test_paths:
            if 'api-child' in properties:
                continue
            accepted = ('api-parent', 'non-api')
            expected = None if any(map(lambda i: i in properties, accepted)) else False
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected)

    def test_want_directory_exclude_multiple(self):
        """
        Test wantDirectory with multiple exclude parameter
        """
        self.plugin.skipnose_exclude = ['api', 'foo']
        for path, properties in self.test_paths:
            if 'api-child' in properties or 'foo-child' in properties:
                continue
            accepted = ('api-parent', 'non-api')
            expected = None if any(map(lambda i: i in properties, accepted)) else False
            if expected is None and 'foo' in path:
                expected = False
            actual = self.plugin.wantDirectory(path)
            self.assertEqual(actual, expected)
