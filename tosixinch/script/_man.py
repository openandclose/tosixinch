#!/usr/bin/env python

"""
A sample hook for man pages.

Usage as an independent script:
    _man.py <FILE>

You have to specify an actual filepath for <FILE>
(not 'grep', but e.g. '/usr/share/man/man1/grep.1.gz').
"""

import logging
import os
import re
import subprocess
import sys

from tosixinch import action
from tosixinch import system

logger = logging.getLogger(__name__)

EXTENSION = r'^(.+\.[1-9]([a-z]+)?)(\.gz)?$'


def man(dfile, efile, delete=True):
    env = {'MANROFFOPT': '-rIN=2n'}
    cmd = ['man', '-Thtml', dfile]
    ret = subprocess.run(
        cmd, capture_output=True, check=True, env=os.environ.update(env))
    if logger.name == '__main__':
        print('processing %r... (write to %r)' % (dfile, efile))
    else:
        logger.info('[man] processing %r...', dfile)
    text = ret.stdout.decode(sys.stdout.encoding)
    system.write(efile, text=text)
    if delete:
        delete_images()
    return 101


def delete_images():
    img = r'grohtml-[0-9]+\.png$'
    for entry in os.scandir('.'):
        if re.match(img, entry.name):
            os.remove(entry)


def match(dfile):
    basename = os.path.basename(dfile)
    m = re.search(EXTENSION, basename)
    if m:
        return m.group(1)
    return False


def run(conf, site):
    ret = _run(site.dfile, site.efile)
    if ret == 101:
        action.CSSWriter(conf, site).read_and_write()
    return ret


def _run(dfile, efile):
    if match(dfile):
        return man(dfile, efile)
    return 0


def main():
    if len(sys.argv) == 2:
        dfile = sys.argv[1]
        name = match(dfile)
        if name:
            man(dfile, name + '.html')
            return
    print(__doc__)


if __name__ == '__main__':
    sys.exit(main())
