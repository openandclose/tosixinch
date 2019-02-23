#!/usr/bin/env python

"""Actualy invoke tosixinch.main.main().

For each url from urls.txt,
Do download, extract, toc or convert.

And compare the outputs with prepared reference files.

And on error, make it so that I can see the diffs in some way or other.

Require Pillow or PIL python library.
Require Poppler commandline utilities (pdfinfo and pdftoppm).
Require viewer applications (vim and sxiv).
"""

# For now I am not deleting files if not necessary,
# trusting the overwriting capability of the script.


import argparse
import os
import shutil
import subprocess
import sys

import pytest

from PIL import Image, ImageChops

import tosixinch.main
import tosixinch.settings
import tosixinch.util


COMPARE_ERROR_FATAL = True
# COMPARE_ERROR_FATAL = False

BUFSIZE = 8*1024

UFILE = 'urls.txt'
PNG_DIR = '_png'
IMG_PREFIX = 'pdfcmp'

SELECT_SHORT_ULIST = (
    'en.wikipedia.org',
    'news.ycombinator.com',
    'templite.py'
)

HTML_DIFF_VIEWER_CMD = 'vim -d %s %s'
IMAGE_VIEWER_CMD = 'sxiv %s %s %s'
PDF_PAGE_COUNT_CMD = 'pdfinfo %s'
PDF_TO_PNG_CMD = 'pdftoppm -f %s -l %s -png %s %s'


TESTDIR = os.path.dirname(os.path.abspath(__file__))
TEMP = os.path.join(TESTDIR, 'temp')
OUTCOME = os.path.join(TEMP, 'actualrun', 'outcome')
REFERENCE = os.path.join(TEMP, 'actualrun', 'reference')

os.chdir(OUTCOME)
if not os.path.isdir(PNG_DIR):
    os.mkdir(PNG_DIR)


def _get_ufiles():
    ufile = os.path.join(TESTDIR, UFILE)
    ufile_ref = os.path.join(REFERENCE, UFILE)
    ufile_outcome = os.path.join(OUTCOME, UFILE)
    return ufile, ufile_ref, ufile_outcome


def _check_ufiles():
    ufile, ufile_ref, ufile_outcome = _get_ufiles()
    assert os.path.getmtime(ufile) <= os.path.getmtime(ufile_ref)
    assert os.path.getmtime(ufile) <= os.path.getmtime(ufile_outcome)


def update_ufiles():
    """Copy 'urls.txt' from the canonical one in 'tests' direcrtory."""
    print('updating ufiles...')
    ufile, ufile_ref, ufile_outcome = _get_ufiles()
    shutil.copy(ufile, ufile_ref)
    shutil.copy(ufile, ufile_outcome)


def get_urls():
    urls = tosixinch.util.parse_ufile(UFILE)
    return urls


def print_urls(urls):
    for i, url in enumerate(urls, 1):
        print('%2d: %s' % (i, url))


def _bincmp(f1, f2):
    # Borrowed from ``filecmp._do_cmp()`` (Python Standard Library).
    bufsize = BUFSIZE
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                if not b2:
                    return True
                else:
                    return False


def  _open_editor(ref, filename):
    cmd = HTML_DIFF_VIEWER_CMD % (ref, filename)
    subprocess.run(cmd.split())


def _check_htmls(ref, filename):
    _open_editor(ref, filename)
    compare_error(filename)


def _get_page_count(pdfname):
    cmd = PDF_PAGE_COUNT_CMD % pdfname
    ret = subprocess.run(cmd.split(), capture_output=True, text=True)
    for line in ret.stdout.split('\n'):
        line = line.strip()
        if line.startswith('Page'):
            return line.split()[-1]


def _get_png_name(num, pagenum, img_prefix):
    if pagenum < 10:
        digit = '%d'
    else:
        digit = '%02d'

    fmt = '%s/%s-' + digit + '.png'
    return fmt % (PNG_DIR, img_prefix, num)


def _get_png_name_set(num, pagenum):
    png1 = _get_png_name(num, pagenum, IMG_PREFIX + '1')
    png2 = _get_png_name(num, pagenum, IMG_PREFIX + '2')
    png3 = _get_png_name(num, pagenum, IMG_PREFIX + '3')
    return png1, png2, png3


def _create_png_page(num, ref, filename):
    cmd = PDF_TO_PNG_CMD % (num, num, ref, IMG_PREFIX + '1')
    subprocess.run(cmd.split(), cwd=PNG_DIR)
    cmd = PDF_TO_PNG_CMD % (num, num, filename, IMG_PREFIX + '2')
    subprocess.run(cmd.split(), cwd=PNG_DIR)


def _create_diff_png_page(png1, png2, png3):
    # from https://stackoverflow.com/a/1311122
    im1 = Image.open(png1) 
    im2 = Image.open(png2) 
    im3 = ImageChops.difference(im1, im2)
    im3.save(png3)


def _open_image_viewer(png1, png2, png3):
    cmd = IMAGE_VIEWER_CMD % (png3, png1, png2)
    subprocess.run(cmd.split())


def _check_pdfs(ref, filename):
    pagenum = int(_get_page_count(filename))
    for num in range(1, pagenum + 1):
        _create_png_page(num, ref, filename)
        png1, png2, png3 = _get_png_name_set(num, pagenum)

        if _bincmp(png1, png2):
            continue

        print('creating png images from %r...' % filename)
        _create_diff_png_page(png1, png2, png3)
        _open_image_viewer(png1, png2, png3)
        compare_error(filename)


def _compare(filename):
    ref = os.path.join(REFERENCE, filename)
    filename = os.path.join(OUTCOME, filename)
    if _bincmp(ref, filename):
        return

    if filename.endswith('.pdf'):
        _check_pdfs(ref, filename)
    else:
        _check_htmls(ref, filename)


def compare(conf, action):
    if action == 'download':
        filename = conf.sites[0].fname
    if action == 'extract':
        filename = conf.sites[0].fnew
    elif action == 'convert':
        filename = conf.pdfname

    _compare(filename)


def compare_error(filename):
    if COMPARE_ERROR_FATAL:
        fmt = '%r differs from the reference file.'
        raise ValueError(fmt % filename)
    else:
        print('Compare Failed: %r' % filename)


def _run(urls, args, action, do_compare=True):
    for url in urls:
        action_args = args + ['--input', url, '--' + action]
        conf = tosixinch.main._main(args=action_args)

        if do_compare:
            compare(conf, action)


def _clean_directory():
    assert os.path.abspath(os.curdir) in (REFERENCE, OUTCOME)

    for entry in os.listdir():
        if os.path.isfile(entry):
            os.remove(entry)
        elif os.path.isdir:
            shutil.rmtree(entry)


def _clean_ref():
    assert os.path.abspath(os.curdir) == REFERENCE

    _clean_directory()
    update_ufiles()
    

def _copy_downloaded_files(urls):
    assert os.path.abspath(os.curdir) == REFERENCE

    for url in urls:
        fname = tosixinch.util.make_path(url)
        fname_outcome = os.path.join(OUTCOME, fname)
        if fname_outcome == fname:
            continue
        shutil.copy(fname, fname_outcome)


def create_ref(urls):
    curdir = os.curdir
    os.chdir(REFERENCE)

    args = _minimum_args()

    if len(urls) > 1:
        _clean_ref()

    _run(urls, args, 'download', do_compare=False)
    _run(urls, args, 'extract', do_compare=False)
    _run(urls, args, 'convert', do_compare=False)

    _copy_downloaded_files(urls)

    os.chdir(curdir)


def _in_short_ulist(url):
    for sel in SELECT_SHORT_ULIST:
        if sel in url:
            return True


def _get_short_ulist(urls):
    return [url for url in urls if _in_short_ulist(url)]


def very_short_run(urls, args):
    urls = _get_short_ulist(urls)
    _run(urls, args, 'extract')


def short_run(urls, args):
    urls = _get_short_ulist(urls)
    normal_run(urls, args)


def normal_run(urls, args):
    _check_ufiles()
    _run(urls, args, 'extract')
    _run(urls, args, 'convert')
    print('success!')


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-x', '--run', action='count',
            help='run test (-x: very short, --xx: short, --xxx: all urls).')

    parser.add_argument('-p', '--print',
        action='store_const', const='yes',
        help='print numbers and urls')
    parser.add_argument('-n', '--number',
        help='file number to process in urls.txt.')

    parser.add_argument('--update-ufiles',
        action='store_const', const='yes',
        help='update ufiles')
    parser.add_argument('--create-ref',
        action='store_const', const='yes',
        help='create reference files from zero')

    parser.add_argument('--verbose',
        action='store_const', const='yes',
        help='turn on verbose flag')
    parser.add_argument('--force-download',
        action='store_const', const='yes',
        help='turn on force_download flag')
    parser.add_argument('--converter',
        choices=['prince', 'weasyprint', 'wkhtmltopdf', 'ebook-convert'],
        help='select converters')

    parser.add_argument('--compare',
        help='compare files, skipping files creation (for test)')
    parser.add_argument('--download',
        action='store_const', const='yes',
        help='download htmls and compare them with the reference')
    parser.add_argument('--extract',
        action='store_const', const='yes',
        help='extract htmls and compare them with the reference')
    parser.add_argument('--convert',
        action='store_const', const='yes',
        help='convert htmls to pdf and compare it with the reference')
    # parser.add_argument('--toc',
    #     action='store_const', const='yes',
    #     help='create urls-toc.txt and new merged htmls'
    #         'from urls.txt and reference extracted htmls')

    args = parser.parse_args(args)
    return args


def _minimum_args():
    return ['--nouserdir']


def build_cmd_args(args):
    cmd_args = _minimum_args()

    if args.verbose:
        cmd_args.append('--verbose')

    if args.force_download:
        cmd_args.append('--force-download')

    if args.converter:
        cmd_args.append('--' + converter)

    return cmd_args


def main():
    args = parse_args()

    if args.compare:
        filename = os.path.relpath(args.compare, start=OUTCOME)
        _compare(args.compare)
        return

    urls = get_urls()

    if args.print:
        print_urls(urls)
        return

    if args.update_ufiles:
        update_ufiles()
        return

    if args.create_ref:
        create_ref(urls)
        return

    if args.number:
        urls = [urls[int(args.number) - 1]]

    cmd_args = build_cmd_args(args)

    if args.run:
        if args.run == 1:
            very_short_run(urls, cmd_args)
            return
        elif args.run == 2:
            short_run(urls, cmd_args)
            return
        elif args.run == 3:
            normal_run(urls, cmd_args)
            return
        else:
            raise ValueError('Not Implemented (only -x, -xx, or -xxx).')

    if args.download:
        _run(urls, cmd_args, 'download')
    elif args.extract:
        _run(urls, cmd_args, 'extract')
    elif args.convert:
        _run(urls, cmd_args, 'convert')


if __name__ == '__main__':
    main()
