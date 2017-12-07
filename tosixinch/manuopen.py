
"""Open and read local files in appropriate encoding.

Most aplications just provide an alternative: auto or an explicit encoding.
I think 'auto' is too broad and one encoding is too limitted, for our purpose.

* Let users specify multiple encodings in preference order
  (like editors do).
* So that they can put in ``ftfy`` and ``chardet`` at exactly desired places.
* So that happen-to-be legal bytes can be interpreted first as ``mojibake``.
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

CODINGS = ('utf_8', 'utf-8-variants', 'latin_1', 'cp1252')


def manuopen(fname, codings=None):
    codings = codings or CODINGS
    for coding in codings:
        if coding == 'ftfy':
            logger.info('using ftfy ... %s' % fname)
            try:
                return use_ftfy(fname)
            except UnicodeDecodeError:
                pass
        elif coding == 'chardet':
            logger.info('using chardet ... %s' % fname)
            try:
                return use_chardet(fname)
            except UnicodeDecodeError:
                pass
        else:
            if coding not in ('utf_8', 'utf-8'):
                logger.info('trying %r... %s' % (coding, fname))
            try:
                return try_encoding(fname, coding)
            except UnicodeDecodeError:
                pass

    raise UnicodeDecodeError('All encodings failed: %r' % codings)


def try_encoding(fname, coding):
    return open(fname, encoding=coding).read()


def use_ftfy(fname):
    with open(fname, encoding='utf_8', errors='backslashreplace') as f:
        text = f.read()
    return ftfy.fixes.decode_escapes(text)


def use_chardet(fname):
    ret = chardet.detect(open(fname, 'rb').read())
    logger.info('chardet: %s, %s' % (ret["encoding"], ret["confidence"]))
    return open(fname, encoding=ret["encoding"]).read()
