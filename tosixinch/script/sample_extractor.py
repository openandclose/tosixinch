#!/usr/bin/env python

"""
A sample extractor program.

According to the file extension, run programs,
and create the ``Extracted_File``.
(in place of the builtin extractor).

Usage:
    sample_extractor.py --prog PROG[,PROG]...
"""

import argparse
import os
import re
import subprocess
import sys

from tosixinch import system

FNAME = os.environ['TOSIXINCH_FNAME']
FNEW = os.environ['TOSIXINCH_FNEW']


def man():
    env = {'MANROFFOPT': '-rIN=2n'}
    cmd = ['man', '-Thtml', FNAME]
    ret = subprocess.run(
        cmd, capture_output=True, check=True, env=os.environ.update(env))
    # TODO: use logging.debug
    print('tosixinch.script.sample_extractor: [man] %s' % FNEW)
    text = ret.stdout.decode(sys.stdout.encoding)
    system.Writer(FNEW, text=text).write()
    return 101


EXTENSION_TABLE = {
    'man': r'^.+\.[1-9]([a-z]+)?(\.gz)?$',
}

FUNCTION_TABLE = {
    'man': man,
}


def check_ext(prog):
    basename = os.path.basename(FNAME)
    func = None
    for p in prog:
        for k, v in EXTENSION_TABLE.items():
            if p == k:
                if re.search(v, basename):
                    func = FUNCTION_TABLE[p]
                    break
    if func:
        return func()


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--prog',
        help='specify the programs you want to run if conditionas match')

    args = parser.parse_args(args)
    return parser, args


def main():
    parser, args = parse_args()
    prog = [p.strip() for p in args.prog.split(',')]
    return check_ext(prog)


if __name__ == '__main__':
    sys.exit(main())
