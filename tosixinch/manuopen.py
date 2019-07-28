
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

logger = logging.getLogger(__name__)

CODINGS = ('utf_8',)


def manuopen(fname, codings=None):
    codings = codings or CODINGS
    text = None
    encoding = None

    for coding in codings:
        if text is not None:
            break

        if coding == 'ftfy':
            pass
        elif coding == 'chardet':
            logger.info('using chardet ... %s' % fname)
            try:
                text, encoding = use_chardet(fname)
            except UnicodeDecodeError:
                pass
        else:
            if coding not in ('utf_8', 'utf-8'):
                logger.info('trying %r... %s' % (coding, fname))
            try:
                text, encoding = try_encoding(fname, coding)
            except UnicodeDecodeError:
                pass

    if text and 'ftfy' in codings:
        logger.info('using ftfy ... %s' % fname)
        text = use_ftfy(text)

    if text is not None:
        return text, encoding

    raise UnicodeError('All encodings failed to decode: %r' % codings)


def try_encoding(fname, coding):
    text = open(fname, encoding=coding).read()
    return text, coding


def use_ftfy(text):
    return ftfy.fixes.fix_encoding(text)


def use_chardet(fname):
    ret = chardet.detect(open(fname, 'rb').read())
    logger.info('chardet: %s, %s' % (ret["encoding"], ret["confidence"]))
    text = open(fname, encoding=ret["encoding"]).read()
    return text, ret["encoding"]
