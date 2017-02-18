from __future__ import print_function, unicode_literals
import fnmatch
import functools
import json
import os
import re
import sys

from nose.case import FunctionTestCase
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest


def walk_subfolders(path):
    """
    Walk in the subtree within path and generate yield
    all subdirectories.
    """
    for dirpath, dirnames, filenames in os.walk(path):
        for dirname in dirnames:
            yield os.path.join(dirpath, dirname)


class SkipNose(Plugin):
    """
    Nose plugin class for skipnose

    Attributes
    ----------
    skipnose_include : list
        List of glob patterns to include
    skipnose_exclude : list
        List of glob patterns to exclude
    debug : bool
        Whether skipnose should print out debug messages
    """

    env_opt = 'NOSE_SKIPNOSE'
    env_include_opt = 'NOSE_SKIPNOSE_INCLUDE'
    env_exclude_opt = 'NOSE_SKIPNOSE_EXCLUDE'

    def __init__(self):
        super(SkipNose, self).__init__()
        self.debug = False
        self.skipnose_include = None
        self.skipnose_exclude = None
        self.skipnose_skip_tests = None

    def options(self, parser, env=os.environ):
        """
        Nose plugin method which allows to add shell options
        to nosetests runner
        """
        truth = ('true', '1', 'on')
        skipnose_on = env.get(self.env_opt, 'False').lower() in truth

        skip_include = list(filter(
            bool, re.split(r'[,;]', env.get(self.env_include_opt, ''))
        ))

        skip_exclude = list(filter(
            bool, re.split(r'[,;:]', env.get(self.env_exclude_opt, ''))
        ))

        parser.add_option(
            '--with-skipnose',
            action='store_true',
            default=skipnose_on,
            dest='skipnose',
            help='skipnose: enable skipnose nose plugin '
                 '(alternatively, set ${env}=1)'
                 ''.format(env=self.env_opt)
        )
        parser.add_option(
            '--skipnose-debug',
            action='store_true',
            default=False,
            dest='skipnose_debug',
            help='skipnose: enable debugging print-outs'
        )
        parser.add_option(
            '--skipnose-include',
            action='append',
            default=skip_include,
            dest='skipnose_include',
            help='skipnose: which directory to include in tests '
                 'using glob syntax.'
                 'Specifying multiple times will AND the clauses. '
                 'Single parameter ":" delimited clauses will be ORed. '
                 'Alternatively, set ${env} as [,;] delimited string for '
                 'AND and [:] for OR.'
                 ''.format(env=self.env_include_opt)
        )
        parser.add_option(
            '--skipnose-exclude',
            action='append',
            default=skip_exclude,
            dest='skipnose_exclude',
            help='skipnose: which directory to exclude in tests '
                 'using glob syntax.'
                 'Can be specified multiple times. '
                 '(alternatively, set ${env} as [,;:] delimited string)'
                 ''.format(env=self.env_exclude_opt)
        )
        parser.add_option(
            '--skipnose-skip-tests',
            action='store',
            dest='skipnose_skip_tests',
            help='skipnose: path to a json file which should contain '
                 'a list of test method names which should be skipped '
                 'under "skip_tests" key.'
        )

    def configure(self, options, conf):
        """
        When nosetests shell command is executed with correct
        parameters, nose calls configure method which allows
        to reflect the given flags in command
        in the plugin instance.

        One special boolean flag this method should set is
        ``enabled`` attribute which tells nosetests
        if this nose plugin should be enabled
        """
        if options.skipnose:
            self.enabled = True
            self.debug = options.skipnose_debug
            self.skipnose_include = list(map(
                lambda i: i.split(':'),
                options.skipnose_include
            ))
            self.skipnose_exclude = options.skipnose_exclude

            if options.skipnose_skip_tests:
                if not os.path.exists(options.skipnose_skip_tests):
                    print(
                        '{} not found'.format(options.skipnose_skip_tests),
                        file=sys.stderr
                    )
                    sys.exit(1)

                with open(options.skipnose_skip_tests, 'rb') as fid:
                    data = fid.read().decode('utf-8')
                    self.skipnose_skip_tests = json.loads(data)['skip_tests']

    def wantDirectory(self, dirname):
        """
        Nose plugin hook which allows to add logic whether nose
        should look for tests in the given directory.

        Even though nose allows the function to return both boolean
        ``True`` and ``False``, this implementation only returns
        ``False`` when a folder should explicitly be excluded and
        ``None`` when nose should use other factors to determine
        if the directory should be included. One example why
        ``True`` should not be returned is tests in folder
        without ``__init__.py`` file. If returned, all tests
        inside that folder will be executed even though is it
        not a valid Python package. By returning ``None``,
        that tells nose to apply additional logic in the
        determination such as checking if the folder is valid
        Python package.

        Parameters
        ----------
        dirname : str
            Directory path to consider

        Returns
        -------
        want : bool, None
            Boolean if tests should be executed inside the given folder.
            ``None`` is returned for unknown.
        """
        want = True
        basename = os.path.basename(dirname)

        if self.skipnose_include:
            want = all(map(
                lambda i: self._want_directory_by_includes(dirname, i),
                self.skipnose_include
            ))

        if self.skipnose_exclude and want is not False:
            # exclude the folder if the folder path
            # matches any of the exclude patterns
            want = not any(map(
                lambda i: fnmatch.fnmatch(basename, i),
                self.skipnose_exclude
            ))

        if self.debug:
            if not want:
                print('Skipnose: Skipping {}'.format(dirname), file=sys.stderr)
            else:
                print('Skipnose:          {}'.format(dirname), file=sys.stderr)

        # normalize boolean to only ``False`` or ``None``
        return False if want is False else None

    @staticmethod
    def _want_directory_by_includes(dirname, includes):
        # check all subfolders to see if any of them match
        # if yes, then this parent folder should be included
        # so that nose can get to the subfolder
        subfolders = map(
            os.path.basename,
            list(walk_subfolders(dirname)) + [dirname]
        )
        want = any(map(
            lambda i: fnmatch.filter(subfolders, i),
            includes
        ))

        # if directory is not wanted then there is a possibility
        # it is a subfolder of a wanted directory so
        # check against parent folder patterns
        if not want:
            parts = dirname.split(os.sep)
            want = any(map(
                lambda i: fnmatch.filter(parts, i),
                includes
            ))

        return want

    def startTest(self, test):
        """
        Skip tests when skipnose_skip_tests is provided
        """
        if not self.skipnose_skip_tests:
            return

        if isinstance(test.test, FunctionTestCase):
            test_name = '{}.{}'.format(
                test.test.test.__module__,
                test.test.test.__name__,
            )
        else:
            test_name = '{}.{}.{}'.format(
                test.test.__class__.__module__,
                test.test.__class__.__name__,
                test.test._testMethodName,
            )

        if test_name in self.skipnose_skip_tests:
            @functools.wraps(getattr(test.test, test.test._testMethodName))
            def skip_test(*args, **kwargs):
                raise SkipTest(
                    'Skipping {!r} as per --skipnose-skip-tests'
                    ''.format(test_name)
                )

            setattr(test.test, test.test._testMethodName, skip_test)
