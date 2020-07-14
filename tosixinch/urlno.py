
"""Normalize URL for http, https and file scheme (RFC 3986)."""

import re
import urllib.parse

_UNRESERVED = (
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')
_RESERVED = "!#$&'()*+,/:;=?@[]"
_HEXDIGIT = '0123456789ABCDEFabcdef'

_unquote_table = {a + b: '%' + (a + b).upper()
    for a in _HEXDIGIT for b in _HEXDIGIT}
_unquote_table.update({'%x' % ord(c): c for c in _UNRESERVED})
_unquote_table.update({'%X' % ord(c): c for c in _UNRESERVED})


def requote(url):
    """Normalize percent encodings of url.

    1. Unquote unreserved characters.
        2. Uppercase valid hex strings (%3f -> %3F)
        3. Quote '%' (to '%25') preceding invalid hex strings.
    4. quote except reserved, unreserved and '%' characters.

    Based on:
    https://unspecified.wordpress.com/2012/02/12/how-do-you-escape-a-complete-uri/  # noqa: E501
    https://github.com/psf/requests/blob/master/requests/utils.py
    """
    def _unquote_unreserved(url):
        parts = url.split('%')
        res = [parts[0]]
        append = res.append
        for item in parts[1:]:
            try:
                append(_unquote_table[item[:2]])
                append(item[2:])
            except KeyError:
                append('%25')
                append(item)
        return ''.join(res)

    def _quote(url):
        # Before Python 3.7, '~' was not included in unreserved characters.
        # return urllib.parse.quote(url, safe=_RESERVED + '%')
        return urllib.parse.quote(url, safe=_RESERVED + '%' + '~')

    return _quote(_unquote_unreserved(url))


def get_relative_reference(url, baseurl):
    """Generate relative reference.

    (opposite of relative reference resolution)
    """
    parts = urllib.parse.urlsplit(url)
    baseparts = urllib.parse.urlsplit(baseurl)

    if parts.scheme and parts.scheme != baseparts.scheme:
        return url
    if parts.netloc and parts.netloc != baseparts.netloc:
        return url

    path, basepath = parts.path, baseparts.path
    if path == basepath:
        path = ''
    else:
        path = _relpath(path, basepath)

    if not path and parts.query == baseparts.query:
        querry = ''
    else:
        querry = parts.query

    return urllib.parse.urlunsplit(('', '', path, querry, parts.fragment))


def _relpath(path, basepath):
    """Generate path part of relative reference.

    based on: cpython/Lib/posixpath.py:relpath
    """
    path = [x for x in path.split('/')]
    basepath = [x for x in basepath.split('/')][:-1]

    i = 0
    for index in range(min(len(path), len(basepath))):
        if path[index] == basepath[index]:
            i += 1
        else:
            break
    parent_dirs = len(basepath) - i
    relpath = (['..'] * parent_dirs) + path[i:]

    if relpath == ['']:
        return '.'

    # gray zone:
    # if you want to remove the last slash, you have to climb up one directory.
    # 'http://h/p'(url), 'http://h/p/'(baseurl) -> '../p'
    if relpath == []:
        return '../' + path[-1]
    # gray zone generalized:
    # 'http://h/p'(url), 'http://h/p/p2'(baseurl) -> '../../p'
    if all((p == '..' for p in relpath)):
        return ('../' * (len(relpath) + 1)) + path[-1]

    # the first segment of a relative-path reference cannot contain ':'.
    # change e.g. 'aa:bb' to './aa:bb'
    if ':' in relpath[0]:
        relpath.insert(0, '.')

    return '/'.join(relpath)


def remove_dot_segments(path):
    buf = []
    for segment in path.split('/'):
        if segment == '.':
            pass
        elif segment == '..':
            if buf:
                buf.pop()
                if not buf:
                    buf.append('')
        else:
            buf.append(segment)

    if path.endswith(('/.', '/..')):
        buf.append('')

    return '/'.join(buf)


class URL(object):
    """Normalize URL for http, https and file scheme (RFC 3986).

    Based on:
    https://gist.github.com/mnot/246089
    https://gist.github.com/maggyero/9bc1382b74b0eaf67bb020669c01b234
    """

    _authority = '^(.*?@)?(.*?)?(:[0-9]*)?$'
    AUTHORITY_RE = re.compile(_authority)

    DEFAULT_PORT = {'http': '80', 'https': '443'}

    def __init__(self, url):
        self._url = url

    def normalize(self, url):
        parts = urllib.parse.urlsplit(url)
        parts = self._normalize(parts)
        return urllib.parse.urlunsplit(parts)

    def _normalize(self, parts):
        scheme = parts[0]
        authority, path, query, fragment = [requote(p) for p in parts[1:]]

        if authority:
            m = self.AUTHORITY_RE.match(authority)
            userinfo, host, port = m.groups(default='')
            if port and port[1:] == self.DEFAULT_PORT.get(scheme):
                port = ''
            if port == ':':
                port = ''
            authority = userinfo + host.lower() + port

        # only for (absolute) URI
        if scheme:
            path = remove_dot_segments(path)

        if authority and not path:
            path = '/'

        return scheme, authority, path, query, fragment

    @property
    def url(self):
        return self.normalize(self._url)
