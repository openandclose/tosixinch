
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

from . import urlno

# When creating system path from url strings,
# '/' in query and fragment parts are changed.
# Otherwise e.g. 'aaa?bbb/ccc' would be segmented to
# 'aaa?bbb' and 'ccc' in system path.
# So we treat it as a single opaque segment ('aaa?bbb_ccc').
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


def _url2path(url, platform=sys.platform):
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
    if platform == 'win32':
        name = _to_windows_filename(name)
    return urllib.parse.unquote(name)


def _path2url(path, platform=sys.platform):
    """Convert normalized system path to url path."""
    if platform == 'win32':
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


def _path2ref(path, basepath, platform=sys.platform):
    """Convert normalized system path to relative reference."""
    if path == basepath:
        path = ''
    else:
        mod = ntpath if platform == 'win32' else posixpath
        path = mod.relpath(path, mod.dirname(basepath))
    return _path2url(path, platform)


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

    def __init__(self, url, baseurl=None, platform=sys.platform):
        self._url = url
        self.baseurl = baseurl
        self.platform = platform

    @classmethod
    def detect(cls, url):
        if cls.MATCHER.match(url):
            return True
        return False

    def is_absolute(self):
        return urllib.parse.urlsplit(self._url)[0] != ''

    def _normalize(self, url, baseurl):
        # manually resolve network-path and absolute-path reference
        if url.startswith('/'):
            fmt = "invalid url: url begins with '/', and base url is None."
            if url.startswith('//'):
                if not baseurl:
                    raise ValueError(fmt)
                url = urllib.parse.urlsplit(baseurl)[0] + ':' + url
            elif url.startswith('/'):
                if not baseurl:
                    raise ValueError(fmt)
                url = '://'.join(urllib.parse.urlsplit(baseurl)[0:2]) + url

        return urlno.URL(url).url

    def _resolve(self, url, baseurl):
        if not baseurl:
            return url
        url = urllib.parse.urljoin(baseurl, url)
        return urlno.URL(url).url

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
        url = self.absolute_url
        url, _ = _split_fragment(url)
        url = self.MATCHER.sub('', url)
        url = self._add_index(url)
        url = _url2path(url, platform=self.platform)
        return url

    @property
    def url(self):
        return self._normalize(self._url, self.baseurl)

    @property
    def absolute_url(self):
        return self._resolve(self.url, self.baseurl)


class FileURL(object):
    """Unroot file URLs."""

    # Only for local files (no domain names or UNC).
    MATCHER = re.compile(
        '^file:/(/(localhost)?/)?(?=[^/])', flags=re.IGNORECASE)
    WINROOTPATH = re.compile(r'^([a-zA-z]:)(/?)(?=[^/])')

    def __init__(self, url, platform=sys.platform):
        self._url = url
        self.platform = platform

    @classmethod
    def detect(cls, url):
        if url.lower().startswith('file:/'):
            return True
        return False

    def _normalize(self, url):
        return urlno.URL(url).url

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
        return Path(self.path, platform=self.platform).unroot()

    @property
    def url(self):
        return self._normalize(self._url)

    @property
    def absolute_url(self):
        return self.url

    @property
    def path(self):
        return self.absolute_path

    @property
    def absolute_path(self):
        url = self.url
        url, _ = _split_fragment(url)
        m = self.MATCHER.match(url)
        if not m:
            raise ValueError('Not local file URL: %r' % url)
        url = url[m.end():]

        if self.platform == 'win32':
            drive, name = self._split_windows_drive(url)
            return drive + _url2path(name, platform='win32')
        else:
            return _url2path('/' + url, platform=self.platform)


class Path(object):
    """Unroot paths."""

    ROOTPATH = re.compile('^//?(/*)')
    WINROOTPATH = re.compile(r'^([a-zA-z]):[/\\]?(?=[^/\\])|\\\\([?.\\]*)')

    def __init__(self, path, platform=sys.platform):
        self._path = path
        self.platform = platform
        self._pathmodule = ntpath if platform == 'win32' else posixpath

    def _normalize(self, path):
        if self.platform == sys.platform:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)

        if self.platform == 'win32':
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
        if m.group(2):
            raise ValueError(fmt % name)

        if m.group(1):
            drive = m.group(1).lower()
        name = name[m.end():]
        return drive, name

    def _strip_root(self, name):
        if self.platform == 'win32':
            drive, name = self._split_windows_drive(name)
            if drive:
                name = drive + '\\' + name
        else:
            name = self.ROOTPATH.sub('', name)
        return name

    def unroot(self):
        return self._strip_root(self.absolute_path)

    @property
    def path(self):
        return self._normalize(self._path)

    @property
    def absolute_path(self):
        return self._resolve(self.path)


class Map(object):
    """Unroot and map URL and system path.

    'map' here means to change somewhat neutral paths to actual filepaths.
    """

    URL = URL
    FileURL = FileURL
    Path = Path

    INDEX = URL.INDEX

    def __init__(self, input_name, baseurl=None,
            input_type=None, platform=sys.platform):
        self._input_name = input_name
        self._baseurl = baseurl
        self.platform = platform
        self.sep = '\\' if platform == 'win32' else '/'
        self._cls = self._detect(input_name, baseurl, input_type)
        self._hashed = False

    def _detect(self, input_name, baseurl, input_type):
        if input_type:
            if input_type == 'url':
                return self.URL(input_name, baseurl, platform=self.platform)
            if input_type == 'fileurl':
                return self.FileURL(input_name, platform=self.platform)
            if input_type == 'path':
                return self.Path(input_name, platform=self.platform)
            fmt = ("got invalid input_type for class 'Map': %r"
                "(must be one of 'url', 'fileurl' or 'path').")
            raise ValueError(fmt % input_type)

        if self.URL.detect(input_name):
            return self.URL(input_name, baseurl, platform=self.platform)
        if self.FileURL.detect(input_name):
            return self.FileURL(input_name, platform=self.platform)
        return self.Path(input_name, platform=self.platform)

    def _map_name(self, name):
        # 'name' is always derived from a url, so it is ascii.
        for segment in name.split(self.sep):
            if len(segment) > 255:
                self._hashed = True
                return hashlib.sha1(name.encode('utf-8')).hexdigest()
        return name

    def is_url(self):
        return isinstance(self._cls, self.URL)

    def is_local(self):
        return not self.is_url()

    @property
    def input_name(self):
        if self.is_local():
            # Note: FileURL returns system path.
            return self._cls.absolute_path
        else:
            return self._cls.absolute_url

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
        if isinstance(other, str):
            other = self.__class__(other, self.input_name, input_type='url')

        url, fragment = _split_fragment(other.input_name)
        path = getattr(other, name)
        basepath = getattr(self, name)
        ref = _path2ref(path, basepath, platform=self.platform)
        return _add_fragment(ref, fragment)


class Ref(object):
    """Create relative reference from url and baseurl.

    Note it creates it through two system paths.
    So, e.g. from 'http://foo.com/aaa' and 'http://bar.com/bbb',
    (through './foo.com/aaa' and './bar.com/bbb'),
    it creates '../foo.com/aaa'.
    """

    _CLS = Map

    def __init__(self, url, baseurl, platform=sys.platform):
        if isinstance(baseurl, str):
            self._base_cls = self._CLS(
                baseurl, input_type='url', platform=platform)
        else:
            self._base_cls = baseurl

        if isinstance(url, str):
            self._cls = self._CLS(
                url, self._base_cls.input_name,
                input_type='url', platform=platform)
        else:
            self._cls = url

        self.url = self._cls.input_name
        self.fname = self._cls.fname

    def split_fragment(self):
        return _split_fragment(self.url)

    @property
    def relative_reference(self):
        return self._base_cls.get_relative_reference(self._cls)
