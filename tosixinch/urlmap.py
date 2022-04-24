
"""'Map' URLs and system paths.

the process, in effect, makes them current directory paths.
"""

import hashlib
import ntpath
import os
import posixpath
import re
import string
import sys
import urllib.parse

from tosixinch import PLATFORM
from tosixinch import urlno


# query and fragment can have '/' character.
# So when creating system path from url strings,
# it is better to change it to some.
# (given URL 'aaa?bbb/ccc', to 'aaa?bbb_ccc')
_CHANGE_TO = {
    'scheme': {},
    'netloc': {},
    'path': {},
    'query': {'/': '_', },
    'fragment': {'/': '_', },
}

# When creating windows system path from url strings,
# illegal filename characters must be changed (to some).
_WIN_CHANGE_TO = {
    ':': '_',
    '?': '_',
    '*': '_',
    '"': '_',
    '<': '_',
    '>': '_',
    '|': '_',
}

# When creating system path from url strings,
# blank segments must be changed (to some).
# e.g. 'a//b' (url path) -> 'a/_blank_/b' (system path).
_BLANK_SEG = '/_blank_'


def _url2path(url):
    """Convert normalized url path to system path."""
    def _to_filename(url):
        parts = urllib.parse.urlsplit(url)
        newparts = []
        for part, key in zip(parts, _CHANGE_TO):
            for char, repl in _CHANGE_TO[key].items():
                part = part.replace(char, repl)
            newparts.append(part)
        return urllib.parse.urlunsplit(newparts)

    def _to_windows_filename(url):
        for key, value in _WIN_CHANGE_TO.items():
            url = url.replace(key, value)
            url = url.replace(urllib.parse.quote(key), value)
        return url.replace('/', '\\')

    def _replace_blank_seg(name):
        def _blank_seg(m):
            return _BLANK_SEG * len(m.group(1)) + '/'
        return re.sub('/(/+)', _blank_seg, name)

    name = _to_filename(url)
    name = _replace_blank_seg(name)
    if PLATFORM == 'win32':
        name = _to_windows_filename(name)
    return urllib.parse.unquote(name)


def _path2url(path):
    """Convert normalized system path to url path."""
    if PLATFORM == 'win32':
        path = path.replace('\\', '/')
        comp = path.split(':')
        if len(comp) > 1:
            if (len(comp) > 2
                    or comp[0] not in string.ascii_letters):
                raise ValueError('Invalid windows path: %r' % path)
            path = '/%s:%s' % (comp[0], comp[1])
    # Before Python 3.7, '~' was not included in unreserved characters.
    # url = urllib.parse.quote(path)
    url = urllib.parse.quote(path, safe='/~')
    if ':' in url.split('/')[0]:
        url = './' + url
    return url


def _path2ref(path, basepath):
    """Convert normalized system path to relative reference."""
    if path == basepath:
        path = ''
    else:
        mod = ntpath if PLATFORM == 'win32' else posixpath
        path = mod.relpath(path, mod.dirname(basepath))
    return _path2url(path)


def _split_fragment(url):
    if '#' in url:
        return url.split('#', maxsplit=1)
    return url, None


def _add_fragment(url, fragment):
    if fragment:
        return url + '#' + fragment
    if fragment == '':
        return url + '#'
    return url


class URL(object):
    """Unroot URLs."""

    MATCHER = re.compile('^https?://', flags=re.IGNORECASE)
    INDEX = '_'

    def __init__(self, url):
        self._url = url
        self.url = urlno.URL(url).url

    @classmethod
    def detect(cls, url):
        if cls.MATCHER.match(url):
            return True
        return False

    def _add_index(self, url):
        if '/' not in url:
            url += '/'
        root, ext = posixpath.splitext(url)
        if ext:
            pass
        elif '?' in url:
            pass
        else:
            url = posixpath.join(url, self.INDEX)
        return url

    def unroot(self):
        url = self.url
        url, _ = _split_fragment(url)
        url = self.MATCHER.sub('', url)
        url = self._add_index(url)
        url = _url2path(url)
        return url


class FileURL(object):
    """Unroot file URLs."""

    # Only for local files (no domain names or UNC).
    MATCHER = re.compile(
        '^file:/(/(localhost)?/)?(?=[^/])', flags=re.IGNORECASE)
    WINROOTPATH = re.compile(r'^([a-zA-z]:)(/?)(?=[^/])')

    def __init__(self, url):
        self._url = url
        self.url = urlno.URL(url).url

    @classmethod
    def detect(cls, url):
        if url.lower().startswith('file:/'):
            return True
        return False

    def _split_windows_drive(self, name):
        m = self.WINROOTPATH.match(name)
        if not m:
            raise ValueError('invalid file scheme url: %r' % self._url)
        drive = m.group(1).lower()
        if m.group(2):
            drive += '\\'
        name = name[m.end():]
        return drive, name

    def unroot(self):
        return Path(self.path).unroot()

    @property
    def path(self):
        url = self.url
        url, _ = _split_fragment(url)
        m = self.MATCHER.match(url)
        if not m:
            raise ValueError('Not local file URL: %r' % url)
        url = url[m.end():]

        if PLATFORM == 'win32':
            drive, name = self._split_windows_drive(url)
            return drive + _url2path(name)
        else:
            return _url2path('/' + url)


class Path(object):
    """Unroot paths."""

    ROOTPATH = re.compile('^/(/*)(?=[^/]*)')
    WINROOTPATH = re.compile(r'^([a-zA-z]):[/\\]?(?=[^/\\])')

    def __init__(self, path):
        self._path = path
        self._pathmodule = ntpath if PLATFORM == 'win32' else posixpath

    def _normalize(self, path):
        if PLATFORM == sys.platform:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)

        if PLATFORM == 'win32':
            return self._pathmodule.normcase(path)
        else:
            return path

    def _resolve(self, path):
        return self._pathmodule.abspath(path)

    def _split_windows_drive(self, name):
        drive = None
        fmt = 'Unsupported windows filename format: %r'
        m = self.WINROOTPATH.match(name)
        if not m:
            raise ValueError(fmt % name)

        if m.group(1):
            drive = m.group(1).lower()
        name = name[m.end():]
        return drive, name

    def _strip_root(self, name):
        if PLATFORM == 'win32':
            drive, name = self._split_windows_drive(name)
            if drive:
                name = drive + '\\' + name
        else:
            name = self.ROOTPATH.sub('', name)
        return name

    def unroot(self):
        return self._strip_root(self.path)

    @property
    def path(self):
        path = self._normalize(self._path)
        path = self._resolve(path)
        return path


class Map(object):
    """Unroot and map URL and system path.

    'map' here means to change somewhat neutral paths to actual filepaths.
    """

    INDEX = URL.INDEX

    def __init__(self, input_name,
            input_type=None):
        self._input_name = input_name
        self.sep = '\\' if PLATFORM == 'win32' else '/'
        self._cls = self._detect(input_name, input_type)
        self._hashed = False

    def _detect(self, input_name, input_type):
        if input_type:
            if input_type == 'url':
                return URL(input_name)
            if input_type == 'fileurl':
                return FileURL(input_name)
            if input_type == 'path':
                return Path(input_name)
            fmt = ("got invalid input_type for class 'Map': %r"
                "(must be one of 'url', 'fileurl' or 'path').")
            raise ValueError(fmt % input_type)

        if URL.detect(input_name):
            return URL(input_name)
        if FileURL.detect(input_name):
            return FileURL(input_name)
        return Path(input_name)

    def _map_name(self, name):
        # 'name' is always derived from a url, so it is ascii.
        for segment in name.split(self.sep):
            if len(segment) > 255:
                self._hashed = True
                return hashlib.sha1(name.encode('utf-8')).hexdigest()
        return name

    def is_url(self):
        return isinstance(self._cls, URL)

    def is_local(self):
        return not self.is_url()

    @property
    def url(self):
        # Note: Error when self._cls is Path.
        return self._cls.url

    @property
    def input_name(self):
        if self.is_local():
            # Note: FileURL returns system path.
            return self._cls.path
        else:
            return self._cls.url

    @property
    def mapped_name(self):
        name = self._cls.unroot()
        return self._map_name(name)

    @property
    def fname(self):
        """Return a new filename only for remote resources (url).

        A kind of shortcut.
        When c.f. retrieving files, it is convenient
        if local resources (fileurl and path) skip to create new names.
        """
        if self.is_local():
            return self.input_name
        else:
            return self.mapped_name

    def get_relative_reference(self, other):
        return self._get_relative_reference(other, name='fname')

    def _get_relative_reference(self, other, name):
        # other is a url class with .url and .<name>
        url, fragment = _split_fragment(other.url)
        path = getattr(other, name)
        basepath = getattr(self, name)
        ref = _path2ref(path, basepath)
        return _add_fragment(ref, fragment)


class Ref(object):
    """Create relative reference from url and parent_url.

    Note it creates it through two system paths.
    So, e.g. from 'http://foo.com/aaa.html' and 'http://bar.com/bbb.html',
    (through './foo.com/aaa.html' and './bar.com/bbb.html'),
    it creates '../foo.com/aaa.html'.
    """

    _CLS = Map

    def __init__(self, url, parent_url, baseurl=None):
        if isinstance(parent_url, str):
            self._parent_cls = self._CLS(parent_url, input_type=None)
        else:
            self._parent_cls = parent_url

        self.baseurl = baseurl
        self._url = self._resolve(url)

        self._cls = self._detect(self._url)
        self.url = self._cls.input_name
        self.fname = self._cls.fname

    def _resolve(self, url):
        baseurl = self.baseurl or self._parent_cls.url
        return urllib.parse.urljoin(baseurl, url)

    def _detect(self, url):
        base = self._parent_cls
        if base.is_url():
            input_type = 'url'
        else:
            input_type = None

        return self._CLS(url, input_type=input_type)

    @property
    def relative_reference(self):
        return self._parent_cls.get_relative_reference(self)
