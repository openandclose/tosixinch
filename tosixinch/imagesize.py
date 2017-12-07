#!/usr/bin/env python

# ----------------------------------------------------------
# This module is a rewrite of phuslu's imgsz.
# https://github.com/phuslu/imgsz
# d4d7e2cc386229db1d2130122076b8e0a8627e31

# - Changed python2 code to python3.
# - Deleted many file format functions,
#   we need only the most popular ones used in html.
# - Errors are made more lenient, and concentrated in a few places.

# ----------------------------------------------------------

"""Recognize image file formats and size based on their first few bytes.

This module is a port of Image::Size Perl Module
see more http://search.cpan.org/author/RJRAY/Image-Size-3.01/lib/Image/Size.pm

ported by jigloo(phus@live.com)
add rgbsize rassize pcxsize function

New BSD license
"""

import re
from struct import unpack


def _jpegsize(stream):
    x = y = 0
    # Skip the match.
    stream.read(2)
    while True:
        # Extract the segment header.
        (marker, code, length) = unpack('>BBH', stream.read(4))
        if marker != 0xFF:
            # Not valid jpeg.
            break
        elif code >= 0xC0 and code <= 0xC3:
            y, x = unpack('>xHH', stream.read(5))
            break
        else:
            # Skip to the next marker.
            stream.read(length - 2)
    if x and y:
        return 'jpeg', x, y


def _pngsize(stream):
    # https://www.w3.org/TR/PNG/#11IHDR
    # Skip the match and 'chunk length' (8 + 4).
    stream.read(12)
    if stream.read(4) == b'IHDR':
        x, y = unpack('>LL', stream.read(8))
        return 'png', x, y


def _gifsize(stream):
    # https://www.w3.org/Graphics/GIF/spec-gif89a.txt
    # Return 'Logical Screen Width' and 'Logical Screen Height'.
    # Skip the match.
    stream.read(6)
    lsw, lsh = unpack('<HH', stream.read(4))
    return 'gif', lsw, lsh


def _bmpsize(stream):
    # https://en.wikipedia.org/wiki/BMP_file_format
    # Skip 'BITMAPFILEHEADER' and header of 'BITMAPINFOHEADER' (14 + 4).
    stream.read(18)
    x, y = unpack('<LL', stream.read(8))
    return 'bmp', x, y


TYPE_MAP = {
    re.compile(br'^\xFF\xD8'):                ('jpeg', _jpegsize),  # noqa: E501,E241 (multiple spaces after ':')
    re.compile(br'^\x89PNG\x0d\x0a\x1a\x0a'): ('png', _pngsize),
    re.compile(br'^GIF8[79]a'):               ('gif', _gifsize),  # noqa: E241
    re.compile(br'^BM'):                      ('bmp', _bmpsize),  # noqa: E241
}

TYPES = ', '.join([TYPE_MAP[key][0] for key in TYPE_MAP])


def _type_match(data):
    """Parse bytes and return mime-type and callback function."""
    for key in TYPE_MAP:
        if key.match(data):
            return TYPE_MAP[key]
    else:
        return None, None


def get_size(filename=None, stream=None):
    """Return image format, width and hight."""
    if not stream:
        stream = open(filename, 'rb')
    data = stream.read(512)
    stream.seek(0, 0)
    ret = None
    mime, callback = _type_match(data)
    if mime and callback:
        ret = callback(stream)
    else:
        raise ValueError('Unable to Recognize (%s)' % TYPES)
    if ret:
        mime, x, y = ret
        if x and y:
            return mime, x, y
    raise ValueError('Unable to get size. (%s)' % mime)


if __name__ == "__main__":
    import sys
    print(get_size(sys.argv[1]))
