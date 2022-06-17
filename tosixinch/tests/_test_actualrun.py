#!/usr/bin/env python

"""Actualy invoke tosixinch.main._main().

For each url from urls.txt,
do download, extract, toc or convert.
And compare the outputs with prepared reference files.

And on error, make it so that I can see the diffs in some way or other.

Require Pillow or PIL python library.
Require Poppler commandline utilities (pdfinfo and pdftoppm).
Require viewer applications (vim and sxiv).

With these steep requirements,
I'm afraid this test is not yet ready for other people to use.

Besides, this test creates and deletes a lot of files.
So it is a bit unsafe.

---
It creates two working directories (and intermediate directories)
in application directory.
    .../tosixinch/tosixinch/tests/temp/actualrun/reference
    .../tosixinch/tosixinch/tests/temp/actualrun/outcome

'--creater-ref' changes current directory to 'reference',
cleans files, prepares (copying urls.txt), and runs main._main().
The result is that it is populated with reference html and pdf files.

Actual tests are always done with 'outcome' as current directory.

Main Command line options are:
-x:     (short)
        try to run only necesarry actions, for only a few selected urls.
        test extract. (3 urls)
        test convert, only when related files are modified. (3 urls)
        test toc extraction, only when related files are modified.
-xx:    (short-plus)
        delete most files in the test derectory before runnnig short.
-xxx:   (normal)
        test extract.
        test convert.
        test ufile-convert, making an 'all in one' pdf.
        test toc extraction (merging htmls).

Environment Variable:

TSI_COMPARE_ERROR_SKIP (default: False)
    if the value (case insensitive) is one of true, yes, on ,1,
    it means ``True``.
    if ``True``, the test does not abort on the first error,
    just reporting there were errors at the last.

TSI_COMPARE_OPEN_VIEWER (default: False)
    if the value (case insensitive) is one of true, yes, on ,1,
    it means ``True``.
    if ``True``, on each error, the test opens a diff viewer (vim or sxiv),
    and blocks.
"""


import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

import tosixinch.main
import tosixinch.settings
import tosixinch.system
import tosixinch.toc

from tosixinch import location


_FAIL = 0

BUFSIZE = 8 * 1024

PNG_DIR = '_png'
IMG_PREFIX = 'pdfcmp'

SELECT_SHORT_ULIST = (
    'en.wikipedia.org',
    'news.ycombinator.com',
    'textwrap.py'
)

CONVERT_RELATED_FILES = (
    'convert.py',
    'data/tosixinch.ini',
    'data/site.ini',
    'data/css/sample.t.css',
)
TOC_RELATED_FILES = (
    'toc.py',
)

HTML_DIFF_VIEWER_CMD = 'vim -d %s %s'
IMAGE_VIEWER_CMD = 'sxiv %s %s %s'
PDF_PAGE_COUNT_CMD = 'pdfinfo %s'
PDF_TO_PNG_CMD = 'pdftoppm -f %s -l %s -png %s %s'

TESTDIR = os.path.dirname(os.path.abspath(__file__))
TEMP = os.path.join(TESTDIR, 'temp')
OUTCOME = os.path.join(TEMP, 'actualrun', 'outcome')
REFERENCE = os.path.join(TEMP, 'actualrun', 'reference')
APPLICATION_ROOT = os.path.dirname(TESTDIR)


class Checker(object):
    """Check file timestamps and the logfile.

    the logfile keeps the last time one of tests in this module was run.

    :param action_type: the type of tests to check
    """

    LOGFILE = os.path.join(TEMP, 'actualrun', '.testlog')
    TABLE = {
        'convert': CONVERT_RELATED_FILES,
        'toc': TOC_RELATED_FILES,
    }

    def __init__(self, action_type):
        self.action_type = action_type

    def _read(self):
        try:
            with open(self.LOGFILE) as f:
                return f.readlines()
        except FileNotFoundError:
            with open(self.LOGFILE, 'w') as f:
                return []

    def _parse(self):
        data = {}
        for line in self._read():
            if not line:
                continue
            action_type, timestamp = map(str.strip, line.split(':', 1))
            data[action_type] = timestamp
        return data

    def check(self):
        """Check to see tests are needed. if needed, return True."""
        timestamp = '0'
        for k, v in self._parse().items():
            if k == self.action_type:
                timestamp = v
                break
        timestamp = float(timestamp)

        files = self.TABLE[self.action_type]
        files = [os.path.join(APPLICATION_ROOT, file) for file in files]

        for file in files:
            if os.path.getmtime(file) > timestamp:
                return True
        return False

    def write(self):
        data = []
        for k, v in self._parse().items():
            if k == self.action_type:
                continue
            data.append('%s: %s' % (k, v))
        data.append('%s: %s' % (self.action_type, str(time.time())))
        data = '\n'.join(data)

        with open(self.LOGFILE, 'w') as f:
            f.write(data)


class _URLData(object):
    """Collect all URL retrieving functions."""

    def __init__(self):
        urls, ufile = tosixinch.settings.SampleURLLoader().get_data()
        self.urls = urls
        self.ufile = ufile

    @property
    def tocfile(self):
        return tosixinch.toc.get_tocfile(self.ufile)

    @property
    def toc_urls(self):
        if not os.path.isfile(self.tocfile):
            raise ValueError('tocfile is not created.')
        return location.Locations(ufile=self.tocfile).urls


URLData = _URLData()
URLS = URLData.urls
UFILE = URLData.ufile
TOCFILE = URLData.tocfile

ALL_PDF = '_all.pdf'
TOC_PDF = '_toc.pdf'


def _get_env_bool(name, default=True):
    e = os.environ.get(name)
    if e and e.lower() in ('true', 'yes', 'on', '1'):
        return True
    if e and e.lower() in ('false', 'no', 'off', '0'):
        return False
    return default


COMPARE_ERROR_SKIP = _get_env_bool('TSI_COMPARE_ERROR_SKIP', False)
COMPARE_OPEN_VIEWER = _get_env_bool('TSI_COMPARE_OPEN_VIEWER', False)


def success():
    if _FAIL == 0:
        print('success!')


def _mkdirs(d):
    if not os.path.exists(d):
        os.makedirs(d)


def _prepare_directories():
    _mkdirs(TEMP)
    _mkdirs(OUTCOME)
    _mkdirs(REFERENCE)

    _mkdirs(os.path.join(OUTCOME, PNG_DIR))


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


def _open_editor(ref, filename):
    cmd = HTML_DIFF_VIEWER_CMD % (ref, filename)
    subprocess.run(cmd.split())


def _check_htmls(ref, filename):
    if COMPARE_OPEN_VIEWER:
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
    elif pagenum < 100:
        digit = '%02d'
    else:
        digit = '%03d'

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
    from PIL import Image, ImageChops
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

        print('creating png images from %r, at page: %d...' % (filename, num))
        _create_diff_png_page(png1, png2, png3)
        if COMPARE_OPEN_VIEWER:
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
    site = [site for site in conf.sites][0]

    if action == 'download':
        filename = site.fname
    if action == 'extract':
        filename = site.fnew
    elif action == 'convert':
        filename = conf.pdfname

    _compare(filename)


def compare_error(filename):
    global _FAIL

    if COMPARE_ERROR_SKIP:
        print('Compare Failed: %r' % filename)
        _FAIL = 1
    else:
        fmt = '%r differs from the reference file.'
        raise ValueError(fmt % filename)


def _run(urls, args, action, do_compare=True):
    for url in urls:
        action_args = args + ['--input', url, '--' + action]
        conf = tosixinch.main._main(args=action_args)

        if do_compare:
            compare(conf, action)


def _run_ufile(args, do_compare=True):
    # Instead of generating each pdf file, generates one big pdf file
    # from all urls.
    # Let's skip extraction test since it should be the same as ``_run``.
    if os.path.isfile(TOCFILE):
        os.remove(TOCFILE)

    action_args = args + ['-f', UFILE, '--convert', '--pdfname', ALL_PDF]
    conf = tosixinch.main._main(args=action_args)

    if do_compare:
        _compare(conf.pdfname)


def _run_toc(args, action, do_compare=True):
    args += ['-f', UFILE]
    if action == 'toc':
        action_args = args + ['--toc']
        conf = tosixinch.main._main(args=action_args)
        if do_compare:
            _compare(TOCFILE)
            urls = URLData.toc_urls
            for url in urls:
                fnew = location.Location(url).fnew
                _compare(fnew)

    # We can almost skip conversion test
    # since it should be similar as ``_run_ufile``.
    # But we have to check at least for the first time.
    elif action == 'convert':
        action_args = args + ['--convert', '--pdfname', TOC_PDF]
        conf = tosixinch.main._main(args=action_args)
        if do_compare:
            _compare(conf.pdfname)
    else:
        raise ValueError("'_run_toc' action must be 'toc' or 'convert'.")


def _clean_directory(excludes=None, top='.'):
    abspath = lambda root, name: os.path.abspath(os.path.join(root, name))

    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            path = abspath(root, name)
            if excludes and path in excludes:
                continue
            os.remove(path)

        for name in dirs:
            path = abspath(root, name)
            if os.listdir(path):
                continue
            if excludes and path in excludes:
                continue
            os.rmdir(path)


def _clean_outcome_directory(urls):
    assert os.path.abspath(os.curdir) == OUTCOME

    # Delete files, but keep ``dfiles``.
    png_dir = os.path.abspath(PNG_DIR)
    fnames = [os.path.abspath(n) for n in _get_downloaded_files(urls)]
    excludes = [png_dir] + fnames
    _clean_directory(excludes=excludes)


def _clean_ref_directory():
    assert os.path.abspath(os.curdir) == REFERENCE

    _clean_directory()


def _clean_ref():
    assert os.path.abspath(os.curdir) == REFERENCE

    _clean_ref_directory()


def _get_downloaded_files(urls):
    for url in urls:
        fname = location.Location(url).fname
        yield tosixinch.system.ExtractReader(fname).get_filename()


def _copy_downloaded_files(urls):
    assert os.path.abspath(os.curdir) == REFERENCE

    fnames = _get_downloaded_files(urls)
    for fname in fnames:
        fname_outcome = os.path.join(OUTCOME, fname)
        if fname_outcome == fname:
            continue
        _mkdirs(os.path.dirname(fname_outcome))
        shutil.copy(fname, fname_outcome)


def _copy_pdf_files():
    assert os.path.abspath(os.curdir) == REFERENCE

    # for _run_ufile
    shutil.copy(ALL_PDF, os.path.join(OUTCOME, ALL_PDF))
    # for _run_toc
    shutil.copy(TOCFILE, os.path.join(OUTCOME, TOCFILE))
    shutil.copy(TOC_PDF, os.path.join(OUTCOME, TOC_PDF))


def create_ref():
    _prepare_directories()

    curdir = os.curdir
    os.chdir(REFERENCE)

    _clean_ref()
    urls = URLS
    args = _minimum_args()

    _run(urls, args, 'download', do_compare=False)
    _run(urls, args, 'extract', do_compare=False)
    _run(urls, args, 'convert', do_compare=False)
    _run_ufile(args, do_compare=False)
    _run_toc(args, 'toc', do_compare=False)
    _run_toc(args, 'convert', do_compare=False)

    _copy_downloaded_files(urls)
    _copy_pdf_files()

    os.chdir(curdir)


def update_one_ref(urls):
    """Update reference efiles and PDFFile.

    If the present code changes and generated files changes is to remain,
    from this new model, recreate reference files, only for one url.
    """
    curdir = os.curdir
    os.chdir(REFERENCE)

    args = _minimum_args()

    update_url_download(urls)
    update_url_extract(urls)
    update_url_convert(urls)

    urls = URLS
    _run_ufile(args, do_compare=False)
    _run_toc(args, 'toc', do_compare=False)
    _run_toc(args, 'convert', do_compare=False)

    _copy_pdf_files()

    os.chdir(curdir)


def _in_short_ulist(url):
    for sel in SELECT_SHORT_ULIST:
        if sel in url:
            return True


def _get_short_ulist(urls):
    return [url for url in urls if _in_short_ulist(url)]


def short_run(urls, args, delete=False):
    assert os.path.abspath(os.curdir) == OUTCOME
    if delete:
        _clean_outcome_directory(urls)

    short_urls = _get_short_ulist(urls)
    _run(short_urls, args, 'extract')

    ch = Checker('convert')
    if ch.check():
        print('doing conversion test...')
        _run(short_urls, args, 'convert')
        ch.write()

    ch = Checker('toc')
    if ch.check():
        print('doing toc test...')
        # Note: Here it uses all urls, the same as normal_run.
        _run(urls, args, 'extract')
        _run_toc(args, 'toc')
        ch.write()

    success()


def normal_run(urls, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _clean_outcome_directory(urls)

    _run(urls, args, 'extract')
    _run(urls, args, 'convert')
    _run_ufile(args)
    _run_toc(args, 'toc')
    _run_toc(args, 'convert')
    success()


def _tox_run(urls, args):
    _run(urls, args, 'download', do_compare=False)
    _run(urls, args, 'extract', do_compare=False)
    _run(urls, args, 'convert', do_compare=False)
    # _run_toc(urls, args, 'toc', do_compare=False)


def tox_run():
    """Just check if actual invocation doesn't raise Errors (for tox)."""
    # Get only the first url (wikipedia.org).
    urls = [URLS[0]]
    args = _minimum_args()

    with tempfile.TemporaryDirectory(prefix='tosixinch-') as tmpdir:
        os.chdir(tmpdir)
        _tox_run(urls, args)


def update_url_download(urls):
    os.chdir(REFERENCE)
    args = _minimum_args()
    args.append('--force-download')
    _run(urls, args, 'download', do_compare=False)
    _copy_downloaded_files(urls)


def update_url_extract(urls):
    os.chdir(REFERENCE)
    args = _minimum_args()
    args.append('--force-download')
    _run(urls, args, 'extract', do_compare=False)


def update_url_convert(urls):
    os.chdir(REFERENCE)
    args = _minimum_args()
    _run(urls, args, 'convert', do_compare=False)


def test_url_extract(urls, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _run(urls, args, 'extract')
    success()


def test_url_convert(urls, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _run(urls, args, 'convert')
    success()


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-x', '--run', action='count',
        help='run test (-x: short, --xx: short-plus, --xxx: all urls).')

    parser.add_argument('-p', '--print',
        action='store_const', const='yes',
        help='print numbers and urls')
    parser.add_argument('-n', '--number',
        help='file number to process in urls.txt.')

    parser.add_argument('--create-ref',
        action='store_const', const='yes',
        help='create reference files from zero')
    parser.add_argument('--update-one-ref',
        action='store_const', const='yes',
        help='update reference files for one url')
    parser.add_argument('--tox-run',
        action='store_const', const='yes',
        help='run -123 and --toc in temporary directory in tox environment.')

    parser.add_argument('-7', '--update-url-download',
        action='store_const', const='yes',
        help='update a reference downloaded file')
    parser.add_argument('-8', '--update-url-extract',
        action='store_const', const='yes',
        help='update a reference extracted file')
    parser.add_argument('-9', '--update-url-convert',
        action='store_const', const='yes',
        help='update a reference pdf file')
    parser.add_argument('-2', '--test-url-extract',
        action='store_const', const='yes',
        help='test extraction for a single url')
    parser.add_argument('-3', '--test-url-convert',
        action='store_const', const='yes',
        help='test conversion for a single url')

    parser.add_argument('--verbose',
        action='store_const', const='yes',
        help='turn on verbose flag')
    # parser.add_argument('--force-download',
    #     action='store_const', const='yes',
    #     help='turn on force_download flag')
    # parser.add_argument('--converter',
    #     choices=['prince', 'weasyprint'],
    #     help='select converters')

    args = parser.parse_args(args)
    return parser, args


def _minimum_args():
    return ['--nouserdir']


def build_cmd_args(args):
    cmd_args = _minimum_args()

    if args.verbose:
        cmd_args.append('--verbose')

    # if args.force_download:
    #     cmd_args.append('--force-download')

    # if args.converter:
    #     cmd_args.append('--' + converter)

    return cmd_args


def main():
    parser, args = parse_args()

    if args.create_ref:
        create_ref()
        return

    if args.tox_run:
        tox_run()
        return

    os.chdir(OUTCOME)

    urls = URLS

    if args.print:
        print_urls(urls)
        return

    cmd_args = build_cmd_args(args)

    if args.run:
        if args.run == 1:
            short_run(urls, cmd_args)
            return
        elif args.run == 2:
            short_run(urls, cmd_args, delete=True)
            return
        elif args.run == 3:
            normal_run(urls, cmd_args)
            return
        else:
            raise ValueError('Not Implemented (only -x, -xx or -xxx).')

    if args.number:
        urls = [urls[int(args.number) - 1]]
        if args.update_one_ref:
            update_one_ref(urls)
        elif args.update_url_download:
            update_url_download(urls)
        elif args.update_url_extract:
            update_url_extract(urls)
        elif args.update_url_convert:
            update_url_convert(urls)
        elif args.test_url_extract:
            test_url_extract(urls, cmd_args)
        elif args.test_url_convert:
            test_url_convert(urls, cmd_args)
        else:
            raise ValueError("'--number' is used without some action")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
    if _FAIL:
        raise ValueError('Errors happened.')
