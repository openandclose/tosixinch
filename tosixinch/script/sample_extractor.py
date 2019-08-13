#!/usr/bin/env python

"""
A sample extractor program.

According to the file extension, run programs,
and create the ``Extracted_File``.
(in place of the builtin extractor).

Usage:
    sample_extractor.py --prog PROG[,PROG...]
"""

import argparse
import logging
import os
import re
import subprocess
import sys

from tosixinch import system

logger = logging.getLogger(__name__)


def man(fname, fnew, delete=True):
    env = {'MANROFFOPT': '-rIN=2n'}
    cmd = ['man', '-Thtml', fname]
    ret = subprocess.run(
        cmd, capture_output=True, check=True, env=os.environ.update(env))
    # TODO: use logging.debug
    if logger.name == '__main__':
        print('sample_extractor (subprocess): [man] processed %r' % fname)
    else:
        logger.info('[man] processed %r', fname)
    text = ret.stdout.decode(sys.stdout.encoding)
    system.Writer(fnew, text=text).write()
    if delete:
        delete_images()
    return 101


def delete_images():
    img = r'grohtml-[0-9]+\.png$'
    for entry in os.scandir('.'):
        if re.match(img, entry.name):
            os.remove(entry)


EXTENSION_TABLE = {
    'man': r'^.+\.[1-9]([a-z]+)?(\.gz)?$',
}

FUNCTION_TABLE = {
    'man': man,
}


def check_ext(fname, fnew, prog):
    basename = os.path.basename(fname)
    func = None
    for p in prog:
        for k, v in EXTENSION_TABLE.items():
            if p == k:
                if re.search(v, basename):
                    func = FUNCTION_TABLE[p]
                    break
    if func:
        return func(fname, fnew)


def run(conf, site):
    extractors = conf.general.add_extractors
    return check_ext(site.fname, site.fnew, extractors)


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--prog',
        help='specify the programs you want to run if conditions match')

    args = parser.parse_args(args)
    return parser, args


def main():
    fname = os.environ.get('TOSIXINCH_FNAME')
    fnew = os.environ.get('TOSIXINCH_FNEW')

    parser, args = parse_args()
    prog = [p.strip() for p in args.prog.split(',')]

    return check_ext(fname, fnew, prog)


if __name__ == '__main__':
    sys.exit(main())
