
"""URL and filepath related module.

URL object collections (URLS):
    Locations

URL object (a URL and destination filepaths):
    Location

component URL localizer:
    Component
"""

import functools
import io
import logging
import os
import re
import unicodedata
import urllib.parse

from tosixinch import urlmap

logger = logging.getLogger(__name__)

COMMENT_PREFIX = ('#', ';',)

DOWNLOAD_DIR = '_htmls'

# string.punctuation minus '-' and '_'
PUNCTUATION_RE = re.compile(r'[!"#$%&\'()*+,./:;<=>?@[\\\]^`{|}~]')


# Wrap urlmap functions for higher modules to not call them directly.
path2ref = urlmap._path2ref
get_relative_reference = urlmap._get_relative_reference


# based from: django/django/utils/text.py
def slugify(value, allow_unicode=False):
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')

    value = PUNCTUATION_RE.sub('-', value)
    value = re.sub(r'[^\w\s-]', '', value.lower())
    value = re.sub(r'[-\s]+', '-', value).strip('-_')
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


class Location(urlmap.Map):
    """Implement concrete url and system path conversion."""

    PREFIX = DOWNLOAD_DIR
    OVERWRITE = False

    APPENDIX = '~'
    EXTENSION = '.html'
    HASH_DIR = '_hash'

    def _add_appendix(self, name):
        if self.APPENDIX == '':
            return name

        root, ext = os.path.splitext(name)
        root += self.APPENDIX
        if ext and ext == self.EXTENSION:
            pass
        else:
            ext = ext + self.EXTENSION
        return root + ext

    def _map_name(self, name):
        name = super()._map_name(name)  # may modify self._hashed
        if self._hashed:
            return self.sep.join(
                (self.PREFIX, self.HASH_DIR, name))
        else:
            return self.sep.join((self.PREFIX, name))

    # TODO: invent more general term
    @property
    def url(self):
        return self.input_name

    @property
    def fnew(self):
        if self.OVERWRITE:
            return self.fname
        return self._add_appendix(self.mapped_name)

    @property
    def slash_fnew(self):
        return urlmap._path2url(self.fnew)

    @property
    def idna_url(self):
        # This is only used when downloading remote resources.
        # So every other name representations are kept unicode.
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

    def check_url(self):
        if self.is_local:
            url = self.url
            if not os.path.exists(url):
                raise FileNotFoundError('[url] File not found: %r' % url)
            if os.path.isdir(url):
                raise IsADirectoryError('[url] Got directory name: %r' % url)
            return True
        return False

    def check_fname(self, force=False, cache=None):
        """Check if downloading is necessary (done).

        True:  not necessary
        False: necessary
        """
        if self.check_url():
            return True

        fname = self.fname
        if os.path.exists(fname):
            if not force:
                return True
            else:
                if cache and cache.get(fname):
                    return True

        if cache:
            cache[fname] = 1
        return False


class Component(urlmap.Ref):
    """Create relative reference for class 'Location'."""

    _CLS = Location
    _INHERIT = ('PREFIX', 'INDEX', 'APPENDIX')

    def check_fname(self, force=False, cache=None):
        return self._cls.check_fname(force, cache)

    @property
    def idna_url(self):
        return self.url

    @property
    def relative_reference(self):
        path, basepath, url = self.fname, self._parent_cls.fnew, self.url
        return get_relative_reference(path, basepath, url)


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
        self.replacefile = replacefile
        self.urls = urls
        self.ufile = ufile
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
