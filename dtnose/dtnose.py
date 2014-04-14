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


class DtNose(Plugin):
    env_opt = 'NOSE_DTNOSE'
    env_include_opt = 'NOSE_DTNOSE_INCLUDE'
    env_exclude_opt = 'NOSE_DTNOSE_EXCLUDE'

    def __init__(self):
        super(DtNose, self).__init__()
        self.dtnose_include = None
        self.dtnose_exclude = None

    def options(self, parser, env=os.environ):
        dtnose_on = bool(env.get(self.env_opt, False))
        dt_include = filter(bool, re.split(r'[,;:]', env.get(self.env_include_opt, '')))
        dt_exclude = filter(bool, re.split(r'[,;:]', env.get(self.env_exclude_opt, '')))

        parser.add_option(
            '--dtnose',
            action='store_true',
            default=dtnose_on,
            dest='dtnose',
            help='dtnose: enable selective dtnose runner (alternatively, set ${}=1)'
                 ''.format(self.env_opt)
        )
        parser.add_option(
            '--dtnose-debug',
            action='store_true',
            default=False,
            dest='dtnose_debug',
            help='dtnose: enable debugging print outs'
        )
        parser.add_option(
            '--dtnose-include',
            action='append',
            default=dt_include,
            dest='dtnose_include',
            help='dtnose: which directory to include in tests using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_include_opt)
        )
        parser.add_option(
            '--dtnose-exclude',
            action='append',
            default=dt_exclude,
            dest='dtnose_exclude',
            help='dtnose: which directory to exclude in tests using glob syntax.'
                 'can be specified multiple times. '
                 '(alternatively, set ${} as [,;:] delimited string)'
                 ''.format(self.env_exclude_opt)
        )

    def configure(self, options, conf):
        if options.dtnose:
            self.enabled = True
            self.debug = options.dtnose_debug
            self.dtnose_include = options.dtnose_include
            self.dtnose_exclude = options.dtnose_exclude

    def wantDirectory(self, dirname):
        want = True
        basename = os.path.basename(dirname)

        if self.dtnose_include:
            subfolders = map(os.path.basename, list(walk_subfolders(dirname)) + [dirname])
            want = any(map(lambda i: fnmatch.filter(subfolders, i), self.dtnose_include))

            if not want:
                parts = dirname.split(os.sep)
                want = any(map(lambda i: fnmatch.filter(parts, i), self.dtnose_include))

        if self.dtnose_exclude and want != False:
            want = not any(map(lambda i: fnmatch.fnmatch(basename, i), self.dtnose_exclude))

        if self.debug:
            if not want:
                print('Nosetests: Skipping {}'.format(dirname), file=sys.stderr)
            else:
                print('Nosetests:          {}'.format(dirname), file=sys.stderr)

        return want
