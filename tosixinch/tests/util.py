
import os
import shutil
import string
import subprocess
import sys

import tosixinch.util

TESTDIR = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(TESTDIR, 'res')
TEMP = os.path.join(TESTDIR, 'temp')


def delete_tempfiles(exclude=None):
    if exclude is None:
        exclude = []

    for root, dirs, files in os.walk(TEMP):
        for f in files:
            if f in exclude:
                continue
            os.remove(os.path.join(root, f))

    for root, dirs, files in os.walk(TEMP, topdown=False):
        for d in dirs:
            d = os.path.join(root, d)
            if not os.listdir(d):
                os.rmdir(d)


def _prepare_ufile():
    """Copy 'urls.txt'.

    This is done because actual urls.txt is in TEMP directory,
    likely to be accidentally deleted,
    so I want to keep the original.
    """
    ufile = os.path.join(TESTDIR, 'urls.txt')
    ufile_temp = os.path.join(TEMP, 'urls.txt')
    if (not os.path.exists(ufile_temp)
        or os.path.getmtime(ufile_temp) < os.path.getmtime(ufile)):
        shutil.copy2(ufile, ufile_temp)

    tocfile = os.path.join(TEMP, 'urls-toc.txt')
    if os.path.exists(tocfile):
        os.remove(tocfile)


def get_urls():
    _prepare_ufile()
    ufile = os.path.join(TEMP, 'urls.txt')
    urls = tosixinch.util.parse_ufile(ufile)
    return urls


def print_urls():
    urls = get_urls()
    for i, url in enumerate(urls, 1):
        print('%2d: %s' % (i, url))


def verify_pdf(pdf, ref):
    # very loosely check pdf contents, 
    # comparing with reference text or pdf.
    # about first 1000 words sequences, ignoring whitespaces.
    text = pdf_to_text(pdf)
    if os.path.splitext(ref)[-1].lower() == '.pdf':
        ref = pdf_to_text(ref)
    i = simple_diff(text, ref)
    if i is not None:
        fmt = 'pdf content differs from reference (in %sth word).\n\n%s'
        raise AssertionError(
            fmt % (i, print_diff(text, i)))


def pdf_to_text(pdf):
    cmd = ['pdftotext', pdf, '-']
    ret =  subprocess.check_output(cmd)
    return ret.decode(sys.stdout.encoding)


def simple_diff(text, ref):
    max = min(1000, len(text.split()))
    for i, words in enumerate(zip(text.split(), ref.split())):
        if i > max:
            break
        if words[0] != words[1]:
            return i
    return None


def print_diff(text, i):
    tmp = []
    cnt = 0
    prev = ''
    spaces = string.whitespace
    for c in text:
        if cnt > i:
            return ''.join(tmp)
        if prev not in spaces and c in spaces:
            cnt += 1
        prev = c
        tmp.append(c)
