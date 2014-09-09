from __future__ import unicode_literals, print_function
import fnmatch
import os
import re
import sys
from nose.plugins import Plugin


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

    def options(self, parser, env=os.environ):
        """
        Nose plugin method which allows to add shell options
        to nosetests runner
        """
        truth = ('true', '1', 'on')
        skipnose_on = env.get(self.env_opt, 'False').lower() in truth
        skip_include = filter(
            bool, re.split(r'[,;:]', env.get(self.env_include_opt, ''))
        )
        skip_exclude = filter(
            bool, re.split(r'[,;:]', env.get(self.env_exclude_opt, ''))
        )

        parser.add_option(
            '--with-skipnose',
            action='store_true',
            default=skipnose_on,
            dest='skipnose',
            help='skipnose: enable skipnose nose plugin '
                 '(alternatively, set ${}=1)'
                 ''.format(self.env_opt)
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
            default=list(skip_include),
            dest='skipnose_include',
            help='skipnose: which directory to include in tests '
                 'using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_include_opt)
        )
        parser.add_option(
            '--skipnose-exclude',
            action='append',
            default=list(skip_exclude),
            dest='skipnose_exclude',
            help='skipnose: which directory to exclude in tests '
                 'using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_exclude_opt)
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
            self.skipnose_include = options.skipnose_include
            self.skipnose_exclude = options.skipnose_exclude

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
            # check all subfolders to see if any of them match
            # if yes, then this parent folder should be included
            # so that nose can get to the subfolder
            subfolders = map(os.path.basename,
                             list(walk_subfolders(dirname)) + [dirname])
            want = any(map(lambda i: fnmatch.filter(subfolders, i),
                           self.skipnose_include))

            # if directory is not wanted then there is a possibility
            # it is a subfolder of a wanted directory so
            # check against parent folder patterns
            if not want:
                parts = dirname.split(os.sep)
                want = any(map(lambda i: fnmatch.filter(parts, i),
                               self.skipnose_include))

        if self.skipnose_exclude and want is not False:
            # exclude the folder if the folder path
            # matches any of the exclude patterns
            want = not any(map(lambda i: fnmatch.fnmatch(basename, i),
                               self.skipnose_exclude))

        if self.debug:
            if not want:
                print('Skipnose: Skipping {}'.format(dirname), file=sys.stderr)
            else:
                print('Skipnose:          {}'.format(dirname), file=sys.stderr)

        # normalize boolean to only ``False`` or ``None``
        return False if want is False else None
