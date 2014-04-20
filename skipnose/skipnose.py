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
    env_opt = 'NOSE_SKIPNOSE'
    env_include_opt = 'NOSE_SKIPNOSE_INCLUDE'
    env_exclude_opt = 'NOSE_SKIPNOSE_EXCLUDE'

    def __init__(self):
        super(SkipNose, self).__init__()
        self.debug = False
        self.skipnose_include = None
        self.skipnose_exclude = None

    def options(self, parser, env=os.environ):
        skipnose_on = bool(env.get(self.env_opt, False))
        skip_include = filter(bool, re.split(r'[,;:]', env.get(self.env_include_opt, '')))
        skip_exclude = filter(bool, re.split(r'[,;:]', env.get(self.env_exclude_opt, '')))

        parser.add_option(
            '--with-skipnose',
            action='store_true',
            default=skipnose_on,
            dest='skipnose',
            help='skipnose: enable skipnose nose plugin (alternatively, set ${}=1)'
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
            default=skip_include,
            dest='skipnose_include',
            help='skipnose: which directory to include in tests using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_include_opt)
        )
        parser.add_option(
            '--skipnose-exclude',
            action='append',
            default=skip_exclude,
            dest='skipnose_exclude',
            help='skipnose: which directory to exclude in tests using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_exclude_opt)
        )

    def configure(self, options, conf):
        if options.skipnose:
            self.enabled = True
            self.debug = options.skipnose_debug
            self.skipnose_include = options.skipnose_include
            self.skipnose_exclude = options.skipnose_exclude

    def wantDirectory(self, dirname):
        want = True
        basename = os.path.basename(dirname)

        if self.skipnose_include:
            subfolders = map(os.path.basename, list(walk_subfolders(dirname)) + [dirname])
            want = any(map(lambda i: fnmatch.filter(subfolders, i), self.skipnose_include))

            if not want:
                parts = dirname.split(os.sep)
                want = any(map(lambda i: fnmatch.filter(parts, i), self.skipnose_include))

        if self.skipnose_exclude and want != False:
            want = not any(map(lambda i: fnmatch.fnmatch(basename, i), self.skipnose_exclude))

        if self.debug:
            if not want:
                print('Skipnose: Skipping {}'.format(dirname), file=sys.stderr)
            else:
                print('Skipnose:          {}'.format(dirname), file=sys.stderr)

        return False if want == False else None
