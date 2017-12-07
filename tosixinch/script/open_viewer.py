#!/usr/bin/env python

"""Sample script to open a pdf viewer after conversion."""

import argparse
import os
import subprocess


def open_viewer(cmd, pdfname, check=False):
    if check:
        if _check_viewer(cmd, pdfname):
            return
    cmd = cmd.split()
    cmd.append(pdfname)
    pid = subprocess.Popen(cmd).pid
    return pid


def _check_viewer(cmd, pdfname):
    # checkcmd = ['lsof', '-F', 'c', pdfname]
    viewer = cmd.split()[0]
    checkcmd = ['ps', '-C', viewer, '-o', 'args', '--no-header']
    ret = subprocess.run(checkcmd, stdout=subprocess.PIPE)
    stdout = ret.stdout.decode().strip()
    if pdfname in stdout:
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--command',
        help=('single string with optional spaces in it. '
              'interpreted as a command to open a pdf viewer, '
              'hopefully just application name'))
    parser.add_argument('--check', action='store_true',
        help=('check if the same file is opened with the command '
              "(the first word of the '--command'), "
              'if so, skip another opening.'))
    parser.add_argument('pdfname',
        help='the pdf file path to open')

    args = parser.parse_args()

    if os.path.isfile(args.pdfname):
        open_viewer(args.command, args.pdfname, args.check)


if __name__ == '__main__':
    main()
