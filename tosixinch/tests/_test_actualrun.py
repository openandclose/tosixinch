#!/usr/bin/env python

"""Actualy invoke tosixinch.main._main().

For each rsrc from urls.txt,
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
        try to run only necesarry actions, for only a few selected rsrcs.
        test extract. (3 rsrcs)
        test convert, only when related files are modified. (3 rsrcs)
        test toc extraction, only when related files are modified.
-xx:    (short-plus)
        delete most files in the test derectory before runnnig short.
-xxx:   (normal)
        test extract.
        test convert.
        test rfile-convert, making an 'all in one' pdf.
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


class _RSRCData(object):
    """Collect all rsrcs retrieving functions."""

    def __init__(self):
        rsrcs, rfile = tosixinch.settings.SampleLoader().get_data()
        self.rsrcs = rsrcs
        self.rfile = rfile

    @property
    def tocfile(self):
        return tosixinch.toc.get_tocfile(self.rfile)

    @property
    def toc_urls(self):
        if not os.path.isfile(self.tocfile):
            raise ValueError('tocfile is not created.')
        return location.Locations(rfile=self.tocfile).rsrcs


RSRCData = _RSRCData()
RSRCS = RSRCData.rsrcs
RFILE = RSRCData.rfile
TOCFILE = RSRCData.tocfile

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


def print_rsrcs(rsrcs):
    for i, rsrc in enumerate(rsrcs, 1):
        print('%2d: %s' % (i, rsrc))


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
        filename = site.dfile
    if action == 'extract':
        filename = site.efile
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


def _run(rsrcs, args, action, do_compare=True):
    for rsrc in rsrcs:
        action_args = args + ['--input', rsrc, '--' + action]
        conf = tosixinch.main._main(args=action_args)

        if do_compare:
            compare(conf, action)


def _run_rfile(args, do_compare=True):
    # Instead of generating each pdf file, generates one big pdf file
    # from all rsrcs.
    # Let's skip extraction test since it should be the same as ``_run``.
    if os.path.isfile(TOCFILE):
        os.remove(TOCFILE)

    action_args = args + ['-f', RFILE, '--convert', '--pdfname', ALL_PDF]
    conf = tosixinch.main._main(args=action_args)

    if do_compare:
        _compare(conf.pdfname)


def _run_toc(args, action, do_compare=True):
    args += ['-f', RFILE]
    if action == 'toc':
        action_args = args + ['--toc']
        conf = tosixinch.main._main(args=action_args)
        if do_compare:
            _compare(TOCFILE)
            urls = RSRCData.toc_urls
            for url in urls:
                efile = location.Location(url).efile
                _compare(efile)

    # We can almost skip conversion test
    # since it should be similar as ``_run_rfile``.
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


def _clean_outcome_directory(rsrcs):
    assert os.path.abspath(os.curdir) == OUTCOME

    # Delete files, but keep ``dfiles``.
    png_dir = os.path.abspath(PNG_DIR)
    dfiles = [os.path.abspath(n) for n in _get_downloaded_files(rsrcs)]
    excludes = [png_dir] + dfiles
    _clean_directory(excludes=excludes)


def _clean_ref_directory():
    assert os.path.abspath(os.curdir) == REFERENCE

    _clean_directory()


def _clean_ref():
    assert os.path.abspath(os.curdir) == REFERENCE

    _clean_ref_directory()


def _get_downloaded_files(rsrcs):
    for rsrc in rsrcs:
        dfile = location.Location(rsrc).dfile
        yield tosixinch.system.ExtractReader(dfile).get_filename()


def _copy_downloaded_files(rsrcs):
    assert os.path.abspath(os.curdir) == REFERENCE

    dfiles = _get_downloaded_files(rsrcs)
    for dfile in dfiles:
        dfile_outcome = os.path.join(OUTCOME, dfile)
        if dfile_outcome == dfile:
            continue
        _mkdirs(os.path.dirname(dfile_outcome))
        shutil.copy(dfile, dfile_outcome)


def _copy_pdf_files():
    assert os.path.abspath(os.curdir) == REFERENCE

    # for _run_rfile
    shutil.copy(ALL_PDF, os.path.join(OUTCOME, ALL_PDF))
    # for _run_toc
    shutil.copy(TOCFILE, os.path.join(OUTCOME, TOCFILE))
    shutil.copy(TOC_PDF, os.path.join(OUTCOME, TOC_PDF))


def create_ref():
    _prepare_directories()

    curdir = os.curdir
    os.chdir(REFERENCE)

    _clean_ref()
    rsrcs = RSRCS
    args = _minimum_args()

    _run(rsrcs, args, 'download', do_compare=False)
    _run(rsrcs, args, 'extract', do_compare=False)
    _run(rsrcs, args, 'convert', do_compare=False)
    _run_rfile(args, do_compare=False)
    _run_toc(args, 'toc', do_compare=False)
    _run_toc(args, 'convert', do_compare=False)

    _copy_downloaded_files(rsrcs)
    _copy_pdf_files()

    os.chdir(curdir)


def update_one_ref(rsrcs):
    """Update reference efiles and PDFFile.

    If the present code changes and generated files changes is to remain,
    from this new model, recreate reference files, only for one rsrc.
    """
    curdir = os.curdir
    os.chdir(REFERENCE)

    args = _minimum_args()

    update_rsrc_download(rsrcs)
    update_rsrc_extract(rsrcs)
    update_rsrc_convert(rsrcs)

    rsrcs = RSRCS
    _run_rfile(args, do_compare=False)
    _run_toc(args, 'toc', do_compare=False)
    _run_toc(args, 'convert', do_compare=False)

    _copy_pdf_files()

    os.chdir(curdir)


def _in_short_ulist(rsrc):
    for sel in SELECT_SHORT_ULIST:
        if sel in rsrc:
            return True


def _get_short_ulist(rsrcs):
    return [rsrc for rsrc in rsrcs if _in_short_ulist(rsrc)]


def short_run(rsrcs, args, delete=False):
    assert os.path.abspath(os.curdir) == OUTCOME
    if delete:
        _clean_outcome_directory(rsrcs)

    short_rsrcs = _get_short_ulist(rsrcs)
    _run(short_rsrcs, args, 'extract')

    ch = Checker('convert')
    if ch.check():
        print('doing conversion test...')
        _run(short_rsrcs, args, 'convert')
        ch.write()

    ch = Checker('toc')
    if ch.check():
        print('doing toc test...')
        # Note: Here it uses all rsrcs, the same as normal_run.
        _run(rsrcs, args, 'extract')
        _run_toc(args, 'toc')
        ch.write()

    success()


def normal_run(rsrcs, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _clean_outcome_directory(rsrcs)

    _run(rsrcs, args, 'extract')
    _run(rsrcs, args, 'convert')
    _run_rfile(args)
    _run_toc(args, 'toc')
    _run_toc(args, 'convert')
    success()


def _tox_run(rsrcs, args):
    _run(rsrcs, args, 'download', do_compare=False)
    _run(rsrcs, args, 'extract', do_compare=False)
    _run(rsrcs, args, 'convert', do_compare=False)
    # _run_toc(rsrcs, args, 'toc', do_compare=False)


def tox_run():
    """Just check if actual invocation doesn't raise Errors (for tox)."""
    # Get only the first rsrc (wikipedia.org).
    rsrcs = [RSRCS[0]]
    args = _minimum_args()

    with tempfile.TemporaryDirectory(prefix='tosixinch-') as tmpdir:
        os.chdir(tmpdir)
        _tox_run(rsrcs, args)


def update_rsrc_download(rsrcs):
    os.chdir(REFERENCE)
    args = _minimum_args()
    args.append('--force-download')
    _run(rsrcs, args, 'download', do_compare=False)
    _copy_downloaded_files(rsrcs)


def update_rsrc_extract(rsrcs):
    os.chdir(REFERENCE)
    args = _minimum_args()
    args.append('--force-download')
    _run(rsrcs, args, 'extract', do_compare=False)


def update_rsrc_convert(rsrcs):
    os.chdir(REFERENCE)
    args = _minimum_args()
    _run(rsrcs, args, 'convert', do_compare=False)


def test_rsrc_extract(rsrcs, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _run(rsrcs, args, 'extract')
    success()


def test_rsrc_convert(rsrcs, args):
    assert os.path.abspath(os.curdir) == OUTCOME
    _run(rsrcs, args, 'convert')
    success()


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-x', '--run', action='count',
        help='run test (-x: short, --xx: short-plus, --xxx: all rsrcs).')

    parser.add_argument('-p', '--print',
        action='store_const', const='yes',
        help='print numbers and rsrcs')
    parser.add_argument('-n', '--number',
        help='file number to process in urls.txt.')

    parser.add_argument('--create-ref',
        action='store_const', const='yes',
        help='create reference files from zero')
    parser.add_argument('--update-one-ref',
        action='store_const', const='yes',
        help='update reference files for one rsrc')
    parser.add_argument('--tox-run',
        action='store_const', const='yes',
        help='run -123 and --toc in temporary directory in tox environment.')

    parser.add_argument('-7', '--update-rsrc-download',
        action='store_const', const='yes',
        help='update a reference downloaded file')
    parser.add_argument('-8', '--update-rsrc-extract',
        action='store_const', const='yes',
        help='update a reference extracted file')
    parser.add_argument('-9', '--update-rsrc-convert',
        action='store_const', const='yes',
        help='update a reference pdf file')
    parser.add_argument('-2', '--test-rsrc-extract',
        action='store_const', const='yes',
        help='test extraction for a single rsrc')
    parser.add_argument('-3', '--test-rsrc-convert',
        action='store_const', const='yes',
        help='test conversion for a single rsrc')

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

    rsrcs = RSRCS

    if args.print:
        print_rsrcs(rsrcs)
        return

    cmd_args = build_cmd_args(args)

    if args.run:
        if args.run == 1:
            short_run(rsrcs, cmd_args)
            return
        elif args.run == 2:
            short_run(rsrcs, cmd_args, delete=True)
            return
        elif args.run == 3:
            normal_run(rsrcs, cmd_args)
            return
        else:
            raise ValueError('Not Implemented (only -x, -xx or -xxx).')

    if args.number:
        rsrcs = [rsrcs[int(args.number) - 1]]
        if args.update_one_ref:
            update_one_ref(rsrcs)
        elif args.update_rsrc_download:
            update_rsrc_download(rsrcs)
        elif args.update_rsrc_extract:
            update_rsrc_extract(rsrcs)
        elif args.update_rsrc_convert:
            update_rsrc_convert(rsrcs)
        elif args.test_rsrc_extract:
            test_rsrc_extract(rsrcs, cmd_args)
        elif args.test_rsrc_convert:
            test_rsrc_convert(rsrcs, cmd_args)
        else:
            raise ValueError("'--number' is used without some action")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
    if _FAIL:
        raise ValueError('Errors happened.')
