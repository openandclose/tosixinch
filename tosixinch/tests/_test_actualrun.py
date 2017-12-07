#!/usr/bin/env python

"""Actualy run tosixinch.main.main(), doing download, extract and convert.

According to sample urls read from tests/urls.txt."""


import argparse
import os
import subprocess

import pytest

import tosixinch.main
import tosixinch.settings
import tosixinch.util
from tosixinch.tests.util import TEMP, delete_tempfiles, get_urls, print_urls

ARGS = [
    'tosixinch',
    '--download',
    '--extract',
    '--convert',
]

TOC_ARGS = [
    'tosixinch',
    '--download',
    '--extract',
    '--toc',
    '--convert',
]

os.chdir(TEMP)


def prepare(delete=None):
    urls = get_urls()
    exclude = ['urls.txt']
    paths = []
    for url in urls:
        path = tosixinch.util.make_path(url)
        path = os.path.basename(path)
        paths.append(path)

    if delete in ('file', '1'):
        delete_tempfiles(exclude=exclude)
    elif delete in ('conponents', '2'):
        exclude += paths
        delete_tempfiles(exclude=exclude)

    return urls


def run(urls, number, converter=None, verbose=False, viewer=None, toc=False):

    if toc:
        args = TOC_ARGS
    else:
        args = ARGS

        if number == 0:
            pass
        else:
            urls = [urls[number - 1]]
            args.extend(['--input', urls[0]])

    if converter:
        args.append('--' + converter)

    if verbose:
        args.append('-v')

    if viewer:
        viewcmd = 'open_viewer.py --command %s --check conf.pdfname' % viewer
        args.extend(('--view', '--viewcmd', viewcmd))

    # print(args)
    tosixinch.main.main(args[1:])

    # pdf = os.path.join(TEMP, pdfname)
    # ref = os.path.join(RES, 'pdf', pdfname)
    # assert verify_pdf(pdf, ref) is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-n', '--number', type=int, default=1,
        help='file number to process in urls.txt. 0 means all.')
    parser.add_argument('-d', '--delete',
        choices=['file', 'components', 'none', '1', '2', '0'], default='none',
        help=("deleting 'file' or 1 means beginning from download, "
              "'components' or 2 means "
              'beginning from extract with components download, '
              "'none' or 0 means beginning from extract"))
    parser.add_argument('-t', '--toc', action='store_true',
        help="make toc version of pdf, '--number' option is ignored")
    parser.add_argument('-c', '--converter',
        choices=['prince', 'weasyprint', 'wkhtmltopdf', 'ebook-convert'],
        help='select converters')
    parser.add_argument('-V', '--viewer',
        help='open resultant pdf file with this viewer')
    parser.add_argument('-p', '--print', action='store_true',
        help='print numbers and urls')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='turn on verbose flag')

    args = parser.parse_args()

    if args.print:
        print_urls()
        return

    urls = prepare()
    run(urls, args.number, args.converter, args.verbose, args.viewer, args.toc)

if __name__ == '__main__':
    main()
