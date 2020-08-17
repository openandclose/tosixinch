
"""Open and read local files in appropriate encoding.

The design is to fail early, but easy for users to check and experiment.
"""

import logging

from tosixinch import _ImportError

try:
    import ftfy
except ImportError:
    ftfy = _ImportError('ftfy')
try:
    import chardet
except ImportError:
    chardet = _ImportError('chardet')
try:
    import html5prescan
except ImportError:
    html5prescan = _ImportError('html5prescan')

logger = logging.getLogger(__name__)

CODINGS = ('utf_8',)


def manuopen(fname, codings=None, errors='strict', length=1024):
    codings = codings or CODINGS
    text = None
    encoding = None
    elist = []  # keep UnicodeDecodeError objects

    for coding in codings:
        if text is not None:
            break

        if coding == 'ftfy':
            pass
        elif coding == 'chardet':
            logger.debug('using chardet ... %s' % fname)
            try:
                text, encoding = use_chardet(fname)
            except UnicodeDecodeError as e:
                elist.append(e)
        elif coding == 'html5prescan':
            logger.debug('using html5prescan ... %s' % fname)
            try:
                text, encoding = use_html5prescan(fname, errors, length)
            except UnicodeDecodeError as e:
                elist.append(e)
        else:
            logger.debug('trying %r... %s' % (coding, fname))
            try:
                text, encoding = try_encoding(fname, coding, errors)
            except UnicodeDecodeError as e:
                elist.append(e)

    if text and 'ftfy' in codings:
        logger.debug('using ftfy ... %s' % fname)
        text = use_ftfy(text)

    if text is not None:
        return text, encoding

    msg = build_message(elist)
    raise UnicodeError(msg)


def try_encoding(fname, coding, errors):
    text = open(fname, encoding=coding, errors=errors).read()
    return text, coding


def use_ftfy(text):
    return ftfy.fixes.fix_encoding(text)


def use_chardet(fname):
    ret = chardet.detect(open(fname, 'rb').read())
    logger.debug('chardet: %s, %s' % (ret["encoding"], ret["confidence"]))
    text = open(fname, encoding=ret["encoding"]).read()
    return text, ret["encoding"]


def use_html5prescan(fname, errors, length):
    with open(fname, 'rb') as f:
        buf = f.read(length)
        scan, buf = html5prescan.get(buf, length=length)
        logger.info('[html5prescan] got encoding: %s' % repr(scan))
    coding = scan.pyname
    text = open(fname, encoding=coding, errors=errors).read()
    return text, coding


def build_message(elist):
    # cf. original message
    # https://github.com/python/cpython/blob/master/Objects/exceptions.c
    # "'%U' codec can't decode byte 0x%02x in position %zd: %U"
    message = ['\n']
    fmt = ("    '%s' codec can't decode byte %#x in position %d: %s\n"
        "        ... %s ...\n")
    for e in elist:
        bstr = _slice_bytestring(e.object, e.start)
        args = (e.encoding, e.object[e.start], e.start, e.reason, bstr)
        message.append(fmt % args)
    return ''.join(message).rstrip()


def _slice_bytestring(bstr, start):
    startpos = max(0, start - 20)
    endpos = min(start + 20, len(bstr))
    return '%s  %s' % (bstr[startpos:start], bstr[start:endpos])
