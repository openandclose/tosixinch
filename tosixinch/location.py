
"""URL and filepath related module.

URL object collections (URLS):
    Locations

URL object (a URL and destination filepaths):
    _Location -> Location

component URL localizer:
    _Component -> Component
"""

import collections
import functools
import io
import logging
import os
import posixpath
import re
import string
import sys
import urllib.parse

logger = logging.getLogger(__name__)

COMMENT_PREFIX = ('#', ';',)

DOWNLOAD_DIR = '_htmls'

# Only http, https and file schemes are suported.
# Also file scheme is only for local files.
SCHEMES = re.compile('^https?://', flags=re.IGNORECASE)
# Note: Wikipedia says 'file://localhost/c:/aaa' is an illegal UNC.
# https://en.wikipedia.org/wiki/File_URI_scheme
FILESCHEME = re.compile(
    '^file:/(/(|localhost)/)*(?=[^/])', flags=re.IGNORECASE)

# Not used.
# Borrows from https://github.com/Kozea/WeasyPrint/blob/master/weasyprint/urls.py  # noqa: E501
# cf. urlsplit(r'c:\aaa\bb') returns
#     SplitResult(scheme='c', netloc='', path='\\aaa\\bb')
OTHER_SCHEMES = re.compile('^([a-zA-Z][a-zA-Z0-9.+-]+):')

ROOTPATH = re.compile('^//?(/*)')
WINROOTPATH = re.compile(r'^([a-zA-z]):[/\\]?([/\\])*|\\\\([?.\\]*)')

RESERVED = ':/?#[]@' + "!$&'()*+,;="  # defined special characters in RFC 3986


_Rule = collections.namedtuple('_Rule', ['quote', 'change'])
_Delimiters = collections.namedtuple(
    '_Delimiters', ['scheme', 'netloc', 'path', 'query', 'fragment'])
_delimiters = _Delimiters(
    _Rule('', ''),
    _Rule('@:[]', ''),
    _Rule('[]', ''),
    _Rule('?', '/'),
    _Rule('?', ''),
)

_changes = {
    '/': '_',
}

_win_changes = {
    ':': '_',
    '?': '_',
    '*': '_',
    '"': '_',
    '<': '_',
    '>': '_',
    '|': '_',
}


def _tamper_windows_fname(url):
    for key, value in _win_changes.items():
        url = url.replace(key, value)
        url = url.replace(urllib.parse.quote(key), value)
    url = url.replace('/', '\\')
    return url


def _tamper_fname(url):
    parts = urllib.parse.urlsplit(url)
    newparts = []
    for part, delimiters in zip(parts, _delimiters):
        for delim in delimiters.change:
            part = part.replace(delim, _changes[delim])
        newparts.append(part)
    url = urllib.parse.urlunsplit(newparts)
    return url


def _url2path(url, platform=sys.platform, unquote=True):
    fname = _tamper_fname(url)
    if platform == 'win32':
        fname = _tamper_windows_fname(fname)
    if unquote:
        fname = urllib.parse.unquote(fname)
    return fname


def _path2url(path, platform=sys.platform):
    """Make relative file url from filepath."""
    if platform == 'win32':
        path = slashify(path)
        comp = path.split(':')
        if len(comp) > 1:
            if (len(comp) > 2
                    or comp[0] not in string.ascii_letters.split()):
                raise OSError('Invalid filepath: %r' % path)
            path = '///%s:%s' % (comp[0], comp[1])
    return urllib.parse.quote(path)


def _url_quote(url):
    """Quote only path part of url.

    Only for characters not defined in RFC 3986.
    """
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(path, safe='/%' + RESERVED)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def slashify(name):
    return name.replace('\\', '/')


# Use bottle.py version.
# See also:
# functools.cached_property (new in Python3.8)
# https://github.com/pydanny/cached-property
# https://github.com/django/django/blob/master/django/utils/functional.py
class cached_property(object):  # noqa N801
    """Delay setting instance attributes.

    A property that is only computed once per instance
    and then replaces itself with an ordinary attribute.
    Deleting the attribute resets the property.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class Locations(object):
    """Make ``Location`` object and implement iteration."""

    def __init__(self, urls=None, ufile=None):
        if not urls:
            try:
                with open(ufile) as f:
                    urls = f.readlines()
            except FileNotFoundError:
                urls = []

        self._urls = [url.strip() for url in urls if url.strip()]
        self._ufile = ufile

        self._iterobj = (Location,)
        self._container = None

        self._comment = COMMENT_PREFIX

    def _parse_urls(self):
        for url in self._urls:
            if url.startswith(self._comment):
                continue
            yield url

    def get_tocfile(self):
        if self._ufile:
            root, ext = os.path.splitext(os.path.basename(self._ufile))
            return root + '-toc' + ext

    @property
    def urls(self):
        return list(self._parse_urls())

    def __len__(self):
        return len(self.urls)

    def _iterate(self):
        for url in self.urls:
            obj, *args = self._iterobj
            yield obj(url, *args)

    def __iter__(self):
        if self._container is None:
            self._container = list(self._iterate())
        return self._container.__iter__()


class _Location(object):
    """Calculate filepaths."""

    INDEX = 'index--tosixinch'
    APPENDIX = '--extracted'
    EXTENSION = '.html'

    def __init__(self, url, platform=sys.platform):
        self._url = url
        self.platform = platform
        self.is_local = self._is_local(url)

    def _is_local(self, url):
        if SCHEMES.match(url):
            return False
        # m = OTHER_SCHEMES.match(url)
        # if m:
        #     msg = 'Only http, https and file schemes are supported, got %r'
        #     raise ValueError(msg % m.group(1))
        return True

    def _parse_url(self):
        url = self._url
        if self.is_local:
            if self._check_filescheme(url):
                url = self._strip_filescheme(url)
            elif self.platform == sys.platform:
                url = os.path.expanduser(url)
                url = os.path.expandvars(url)
                url = os.path.abspath(url)
        return url

    def _check_filescheme(self, url):
        return True if url.startswith('file:/') else False

    def _strip_filescheme(self, url):
        m = FILESCHEME.match(url)
        if m:
            if self.platform == 'win32':
                url = url[m.end(0):]
                url = url.replace('/', '\\')
            else:
                url = '/' + url[m.end(0):]
            url = urllib.parse.unquote(url)
        else:
            raise ValueError('Not local file url: %r' % url)
        return url

    def _make_fname(self, url, unquote=True):
        if self.is_local:
            return url

        fname = SCHEMES.sub('', url)
        fname = fname.split('#', 1)[0]
        fname = self._add_index(fname)
        fname = _url2path(fname, platform=self.platform, unquote=unquote)
        fname = os.path.join(DOWNLOAD_DIR, fname)
        return fname

    def _make_fnew(self, fname):
        if self.is_local:
            fname = self._strip_root(fname)
            fname = os.path.join(DOWNLOAD_DIR, fname)
        return self._add_appendix(fname)

    def _add_index(self, fname):
        if '/' not in fname:
            fname += '/'
        root, ext = posixpath.splitext(fname)
        if ext:
            pass
        elif '?' in fname:
            pass
        else:
            fname = os.path.join(fname, self.INDEX)
        return fname

    def _add_appendix(self, fname):
        root, ext = os.path.splitext(fname)
        root += self.APPENDIX
        if ext and ext == self.EXTENSION:
            pass
        else:
            ext = ext + self.EXTENSION
        return root + ext

    def _strip_root(self, fname):
        if self.platform == 'win32':
            drive = None
            m = WINROOTPATH.match(fname)
            # cf. 'C:aaa.txt' means 'aaa.txt' in current directory in C.
            # but the result of this function is the same as 'C:\aaa.txt'.
            if m:
                if m.group(2) or m.group(3):
                    raise ValueError('Unsupported filename format: %r' % fname)
                if m.group(1):
                    drive = m.group(1)
            fname = WINROOTPATH.sub('', fname)
            if drive:
                fname = os.path.join(drive, fname)
        else:
            # Note: normalization is already done by os.path.abspath
            fname = ROOTPATH.sub('', fname)
        return fname


class Location(_Location):
    """Add convenient APIs."""

    @property
    def is_remote(self):
        return not self.is_local

    @property
    def url(self):
        return self._parse_url()

    @property
    def fname(self):
        return self._make_fname(self.url)

    @property
    def fnew(self):
        return self._make_fnew(self.fname)

    @property
    def slash_url(self):
        if self.is_local and self.platform == 'win32':
            return slashify(self.url)
        return self.url

    @property
    def idna_url(self):
        # This is only used by `download` module internally.
        # So every other resource name representations are kept unicode.
        # cf. https://github.com/kjd/idna implements newer idna spec.
        def to_ascii(s):
            return s.encode('idna').decode('ascii')

        url = self.url
        try:
            url.encode('ascii')
            return url
        except UnicodeEncodeError:
            pass

        parts = urllib.parse.urlsplit(url)
        if parts.netloc:
            host = [to_ascii(s) for s in parts.hostname.split('.')]
            host = '.'.join(host)
            netloc = host
            if parts.username:
                netloc = '@'.join(parts.username, host)
            if parts.port:
                netloc = ':'.join(host, parts.port)
            parts = list(parts)
            parts[1] = netloc
            return urllib.parse.urlunsplit(parts)
        else:
            return url

    def slash_fname(self, unquote=True):
        fname = self._make_fname(self.url, unquote=unquote)
        if self.platform == 'win32':
            return slashify(fname)
        return fname

    def check_url(self):
        if self.is_local:
            url = self.url
            if not os.path.exists(url):
                raise FileNotFoundError('[url] File not found: %r' % url)
            if os.path.isdir(url):
                raise IsADirectoryError('[url] Got directory name: %r' % url)

    def check_fname(self, force=False, cache=None):
        """Check if downloading is necessary (done).

        True:  not necessary
        False: necessary
        """
        self.check_url()
        fname = self.fname
        if os.path.exists(fname):
            if not force:
                return True
            else:
                if cache and cache.get(fname):
                    return True

        cache[fname] = 1
        return False


class _Component(Location):
    """Calculate component filepath."""

    def __init__(self, url, base, platform=sys.platform):
        super().__init__(url, platform)

        if isinstance(base, str):
            base = Location(base, platform=self.platform)
        self.base = base

        if base.is_remote:
            self.is_local = False

    def _normalize_source_url(self, url, base):
        # It seems relative references starting with slashes
        # are not uniformly handled by libraries.
        # So we'd better manually expand them.
        # cf. https://tools.ietf.org/html/rfc3986#section-4.2
        if url.startswith('//'):
            url = urllib.parse.urlsplit(base)[0] + ':' + url
        elif url.startswith('/'):
            url = '://'.join(urllib.parse.urlsplit(base)[0:2]) + url

        # quote needed, since some websites provide unquoted urls.
        return _url_quote(url)

    def _escape_fname_reference(self, url):
        parts = urllib.parse.urlsplit(url)
        newparts = []
        for part, delimiters in zip(parts, _delimiters):
            for delim in delimiters.quote:
                part = part.replace(delim, urllib.parse.quote(delim))
            newparts.append(part)
        return self._urlunsplit_with_quote(newparts)

    def _escape_colon_in_first_path(self, path):
        firstpath = path.split('/')[0]
        if firstpath:  # relative url
            if ':' in firstpath:
                return './' + path
        return path

    def _urlunsplit_with_quote(self, parts):
        url = urllib.parse.urlunsplit((*parts[:3], '', ''))
        if parts[3]:
            url = '%3F'.join((url, parts[3]))
        if parts[4]:
            url = '%23'.join((url, parts[4]))
        return url


class Component(_Component):
    """Add convenient APIs."""

    @property
    def url(self):
        url = self._url
        url = self._normalize_source_url(url, self.base.url)
        url = urllib.parse.urljoin(self.base.url, url)
        return url

    @property
    def fname_reference(self):
        src = posixpath.relpath(
            self.slash_fname(unquote=False),
            posixpath.dirname(self.base.slash_fname(unquote=False))
        )
        src = self._escape_colon_in_first_path(src)
        return self._escape_fname_reference(src)


class ReplacementParser(object):
    """Parse url replacement file and return new urls.

    The format:
        zero or more units

    The unit:
        one regex pattern line
        one regex replacement line
        blank line(s) or EOF
        (lines starting with '#' are ignored)
    """

    def __init__(self, replacefile, urls=None, ufile=None):
        loc = Locations(urls=urls, ufile=ufile)
        self.urls, self.ufile = loc.urls, loc._ufile
        self.replacefile = replacefile
        self.state = None
        self.result = None

    def __call__(self):
        if not os.path.isfile(self.replacefile):
            return self.urls
        urls = self._parse()
        return urls

    def _parse(self):
        self.state = 0
        self.result = []
        if isinstance(self.replacefile, io.TextIOBase):
            f = self.replacefile
        else:
            f = open(self.replacefile)
        for i, line in enumerate(f):
            self._parse_line(i, line)
        self._parse_line(i + 1, '')
        return self._apply_regex()

    def _parse_line(self, i, line):
        """
        Parse a line of url replacement file.

        state:
            0: before the first line
            1: done reading the first line
            2: done reading the second line
        """
        line = line.strip()
        errormsg = "Can't parse urlreplace.txt: [%d] %s" % (i, line or "''")
        if line.startswith('#'):
            return
        if self.state == 0:
            if line:
                self.result.append([line])
                self.state = 1
        elif self.state == 1:
            if line:
                self.result[-1].append(line)
                self.state = 2
            else:
                raise ValueError(errormsg)
        elif self.state == 2:
            if line:
                raise ValueError(errormsg)
            else:
                func = functools.partial(re.sub, *self.result[-1])
                self.result[-1] = func
                self.state = 0

    def _apply_regex(self):
        newurls = []
        for url in self.urls:
            for regex in self.result:
                url = regex(url)
            newurls.append(url)
        return newurls
