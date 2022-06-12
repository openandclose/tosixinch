
"""'Map' URLs and system paths.

the process, in effect, makes them current directory paths.
"""

import hashlib
import os
import posixpath
import re
import urllib.parse

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

    def _replace_blank_seg(name):
        def _blank_seg(m):
            return _BLANK_SEG * len(m.group(1)) + '/'
        return re.sub('/(/+)', _blank_seg, name)

    name = _to_filename(url)
    name = _replace_blank_seg(name)
    return urllib.parse.unquote(name)


def _path2url(path):
    """Convert normalized system path to url path."""
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
        path = os.path.relpath(path, os.path.dirname(basepath))
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
    return url  # when fragment=None


def _get_relative_reference(path, basepath, url):
    """Create from path and basepath, relative URL reference."""
    url, fragment = _split_fragment(url)
    ref = _path2ref(path, basepath)
    # change '' to None (forbid blank fragment at this level)
    fragment = fragment or None
    return _add_fragment(ref, fragment)


class URL(object):
    """Unroot URLs."""

    MATCHER = re.compile('^https?://', flags=re.IGNORECASE)

    def __init__(self, url):
        self._url = url
        self.url = urlno.URL(url).url

    @classmethod
    def detect(cls, url):
        if cls.MATCHER.match(url):
            return True
        return False

    def unroot(self):
        url = self.url
        url, _ = _split_fragment(url)
        url = self.MATCHER.sub('', url)
        url = url.rstrip('/')
        if '/' not in url:
            return posixpath.join(url, 'index.html')
        url = _url2path(url)
        return url


class FileURL(object):
    """Unroot file URLs."""

    # Only for local files (no domain names or UNC).
    MATCHER = re.compile(
        '^file:/(/(localhost)?/)?(?=[^/])', flags=re.IGNORECASE)

    def __init__(self, url):
        self._url = url
        self.url = urlno.URL(url).url

    @classmethod
    def detect(cls, url):
        if url.lower().startswith('file:/'):
            return True
        return False

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

        return _url2path('/' + url)


class Path(object):
    """Unroot paths."""

    ROOTPATH = re.compile('^/(/*)(?=[^/]*)')

    def __init__(self, path):
        self._path = path

    def _normalize(self, path):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        return path

    def _resolve(self, path):
        return os.path.abspath(path)

    def _strip_root(self, name):
        return self.ROOTPATH.sub('', name)

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

    INDEX = '_'

    def __init__(self, input_name, input_type=None):
        self._input_name = input_name
        self.sep = '/'
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

    def _add_index(self, url):
        if self.INDEX == '':
            return url

        root, ext = os.path.splitext(url)
        if ext:
            pass
        elif '?' in url:
            pass
        else:
            url = os.path.join(url, self.INDEX)
        return url

    def _map_name(self, name):
        # 'name' is always derived from a url, so it is ascii.
        for segment in name.split(self.sep):
            if len(segment) > 255:
                self._hashed = True
                return hashlib.sha1(name.encode('utf-8')).hexdigest()

        if self.is_remote:
            return self._add_index(name)
        return name

    @property
    def is_remote(self):
        return isinstance(self._cls, URL)

    @property
    def is_local(self):
        return not self.is_remote

    @property
    def url(self):
        # Note: Error when self._cls is Path.
        return self._cls.url

    @property
    def input_name(self):
        if self.is_local:
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
        if self.is_local:
            return self.input_name
        else:
            return self.mapped_name


class Ref(object):
    """Create relative reference from url and parent_url.

    Note it creates it through two system paths.
    So, e.g. from 'http://foo.com/aaa.html' and 'http://bar.com/bbb.html',
    (through './foo.com/aaa.html' and './bar.com/bbb.html'),
    it creates '../foo.com/aaa.html'.
    """

    _CLS = Map
    _INHERIT = ('INDEX',)

    def __init__(self, url, parent, baseurl=None):
        if isinstance(parent, str):
            self._parent_cls = self._CLS(parent, input_type=None)
        else:
            self._parent_cls = parent

        self._url = url
        self.baseurl = baseurl

        url, _ = _split_fragment(url)
        url = self._resolve(url)
        self._cls = self._detect(url)
        self.url = self._cls.input_name
        self.fname = self._cls.fname

    def _resolve(self, url):
        if self.baseurl:
            return urllib.parse.urljoin(self.baseurl, url)

        base = self._parent_cls
        if base.is_remote:
            return urllib.parse.urljoin(base.url, url)
        else:
            if URL.detect(url):
                return url
            path = _url2path(url)
            if path == '':
                return base._cls.path
            return os.path.join(os.path.dirname(base._cls.path), path)

    def _detect(self, url):
        base = self._parent_cls
        if base.is_remote:
            input_type = 'url'
        else:
            input_type = None

        cls = self._CLS(url, input_type=input_type)
        for attr in self._INHERIT:
            setattr(cls, attr, getattr(self._parent_cls, attr))

        return cls

    @property
    def relative_reference(self):
        path, basepath, url = self.fname, self._parent_cls.fname, self._url
        return _get_relative_reference(path, basepath, url)
