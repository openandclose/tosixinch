
"""URL and filepath related module.

URL object collections (URLS):
    Locations

URL object (a URL and destination filepaths):
    _Location -> Location

component URL localizer:
    _Component -> Component
"""

import collections
import logging
import os
import posixpath
import re
import sys
import urllib.parse


logger = logging.getLogger(__name__)

COMMENT_PREFIX = ('#', ';',)
DIRECTIVE_PREFIX = ('#',)

DOWNLOAD_DIR = '_htmls'

# Only http and https schemes are permitted.
SCHEMES = re.compile('^https?://', flags=re.IGNORECASE)

# Borrows from https://github.com/Kozea/WeasyPrint/blob/master/weasyprint/urls.py  # noqa: E501
# cf. urlsplit(r'c:\aaa\bb') returns
#     SplitResult(scheme='c', netloc='', path='\\aaa\\bb')
OTHER_SCHEMES = re.compile('^([a-zA-Z][a-zA-Z0-9.+-]+):')

ROOTPATH = re.compile('^/+')
WINROOTPATH = re.compile(r'^(?:([a-zA-z]):([/\\]*)|[/?\\]+)')


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
        self._itercontainer = None

        self._comment = COMMENT_PREFIX

    def _parse_urls(self):
        for url in self._urls:
            if url.startswith(self._comment):
                continue
            yield url

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
        container = self._itercontainer
        if container is None:
            container = list(self._iterate())
        return container.__iter__()


class _Location(object):
    """Calculate filepaths."""

    def __init__(self, url, platform=sys.platform):
        self._url = url
        self.platform = platform
        self.sep = '\\' if platform == 'win32' else '/'

    def _is_local(self):
        url = self._url
        if SCHEMES.match(url):
            return False
        # m = OTHER_SCHEMES.match(url)
        # if m:
        #     msg = 'Only http, https and file schemes are supported, got %r'
        #     raise ValueError(msg % m.group(1))
        if url.strip().startswith(DIRECTIVE_PREFIX):
            return False
        return True

    def _parse_url(self):
        url = self._url
        if self._is_local():
            url = os.path.expanduser(url)
            url = os.path.expandvars(url)
            url = os.path.abspath(url)
            # if not os.path.exists(url):
            #     raise FileNotFoundError('File not found: %r' % url)
            # if os.path.isdir(url):
            #     raise IsADirectoryError('Got directory name: %r' % url)
        return url

    def _make_directories(self, fname, on_error_exit=True):
        if not self._in_current_dir(fname):
            if on_error_exit:
                msg = 'filename path is outside of current dir: %r' % fname
                logger.error(msg)
                sys.exit(1)
            else:
                return
        dname = os.path.abspath(os.path.dirname(fname))
        os.makedirs(dname, exist_ok=True)

    def _in_current_dir(self, fname, base=os.curdir):
        current = os.path.abspath(base)
        filepath = os.path.abspath(fname)
        # note: the same filepath is not 'in' current dir.
        if filepath.startswith(current + self.sep):
            return True
        else:
            return False

    def _make_path(self, url, ext='html'):
        fname = SCHEMES.sub('', url)
        fname = fname.split('#', 1)[0]
        if '/' not in fname:
            fname += '/'
        root, ext = posixpath.splitext(fname)
        if not ext:
            fname = posixpath.join(fname, 'index--tosixinch')
        if self.platform == 'win32':
            fname = fname.replace('/', '\\')
        fname = os.path.join(DOWNLOAD_DIR, fname)
        return fname

    def _make_new_fname(self,
            fname, appendix='--extracted', ext='html'):
        base = os.path.join(os.curdir, DOWNLOAD_DIR)
        if not self._in_current_dir(fname, base=base):
            fname = self._strip_root(fname)
            fname = os.path.join(DOWNLOAD_DIR, fname)
        return self._edit_fname(fname, appendix, ext)

    def _edit_fname(self, fname, appendix=None, default_ext=None):
        root, ext = os.path.splitext(fname)
        if appendix:
            root = root + appendix
        if default_ext:
            if ext and ext[1:] == default_ext:
                pass
            else:
                ext = ext + '.' + default_ext
        return root + ext

    def _strip_root(self, fname):
        if self.platform == 'win32':
            drive = None
            m = WINROOTPATH.match(fname)
            # cf. 'C:aaa.txt' means 'aaa.txt' in current directory.
            if m and m.group(2):
                drive = m.group(1).upper()
            fname = WINROOTPATH.sub('', fname)
            if drive:
                fname = os.path.join(drive, fname)
        else:
            fname = ROOTPATH.sub('', fname)
        return fname


class Location(_Location):
    """Add convenient APIs."""

    @property
    def url(self):
        return self._parse_url()

    @property
    def fname(self):
        if self._is_local():
            return self.url
        return self._make_path(self.url)

    @property
    def fnew(self):
        return self._make_new_fname(self.fname)

    @property
    def make_directories(self):
        return self._make_directories(self.fnew)

    @property
    def idna_url(self):
        # This is only used by `download` module internally.
        # So every other resource name representations are kept unicode.
        def to_ascii(s):
            # cf. https://github.com/kjd/idna implements newer idna spec.
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


# see Document (Development/URL quoting memo)
_quotes = {
    # reserved characters
    '!': '%21',
    '#': '%23',
    '$': '%24',
    '&': '%26',
    "'": '%27',
    '(': '%28',
    ')': '%29',
    '*': '%2A',
    '+': '%2B',
    ',': '%2C',
    '/': '%2F',
    ':': '%3A',
    ';': '%3B',
    '=': '%3D',
    '?': '%3F',
    '@': '%40',
    '[': '%5B',
    ']': '%5D',
    # others
    '"': '%22',
    # '%': '%25',
    '<': '%3C',
    '>': '%3E',
    '\\': '%5C',
}

_changes = {
    '/': '_',
}

_win_changes = {
    ':': '_',
    '?': '_',
    '*': '_',
    '\\': '_',
    '"': '_',
    '<': '_',
    '>': '_',
}

Rule = collections.namedtuple('Rule', ['quote', 'change'])
Delimiters = collections.namedtuple(
    'Delimiters', ['scheme', 'netloc', 'path', 'query', 'fragment'])
_delimiters = Delimiters(
    Rule('', ''),
    Rule('@:[]', ''),
    Rule('[]', ''),
    Rule('?', '/'),
    Rule('?', ''),
)


class _Component(Location):
    """Calculate component filepath."""

    def __init__(self, url, base, platform=sys.platform):
        super().__init__(url, platform)

        if isinstance(base, str):
            base = Location(base)
        self.base = base

    def _normalize_source_url(self, url, base):
        # It seems relative references starting with slashes
        # are not uniformly handled by libraries.
        # So we'd better manually expand them.
        # cf. https://tools.ietf.org/html/rfc3986#section-4.2
        if url.startswith('//'):
            url = urllib.parse.urlsplit(base)[0] + ':' + url
        elif url.startswith('/'):
            url = '://'.join(urllib.parse.urlsplit(base)[0:2]) + url
        return url

    def _make_local_url(self, url):
        parts = urllib.parse.urlsplit(url)
        newparts = []
        for part, delimiters in zip(parts, _delimiters):
            for delim in delimiters.quote:
                part = part.replace(delim, _quotes[delim])
            for delim in delimiters.change:
                part = part.replace(delim, _changes[delim])
            newparts.append(part)
        return self._urlunsplit_no_query(newparts)

    def _make_filename(self, url):
        parts = urllib.parse.urlsplit(url)
        newparts = []
        for part, delimiters in zip(parts, _delimiters):
            for delim in delimiters.change:
                part = part.replace(delim, _changes[delim])
            newparts.append(part)
        url = urllib.parse.urlunsplit(newparts)

        fname = urllib.parse.unquote(url)
        if self.platform == 'win32':
            fname = fname.replace('/', '\\')
        return fname

    def _remove_windows_chars(self, url):
        for key, value in _win_changes.items():
            url = url.replace(key, value)
            url = url.replace(_quotes[key], value)
        return url

    def _urlunsplit_no_query(self, parts):
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
        if self.platform == 'win32':
            url = self._remove_windows_chars(url)
        url = self._normalize_source_url(url, self.base.url)
        url = urllib.parse.urljoin(self.base.url, url)
        return url

    @property
    def fname(self):
        return self._make_path(self.url, ext=None)

    @property
    def component_fname(self):
        return self._make_filename(self.fname)

    @property
    def component_url(self):
        local_url = self._make_local_url(self.fname)
        fname = self.component_fname
        if self._in_current_dir(fname, DOWNLOAD_DIR):
            src = './' + os.path.relpath(
                local_url, os.path.dirname(self.base.fname))
        else:
            src = local_url
        return src
