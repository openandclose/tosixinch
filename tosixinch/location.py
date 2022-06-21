
"""URL and filepath related module."""


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

    def __init__(self, rsrcs=None, rfile=None):
        if not rsrcs:
            try:
                with open(rfile) as f:
                    rsrcs = f.readlines()
            except FileNotFoundError:
                rsrcs = []

        self._rsrcs = [rsrc.strip() for rsrc in rsrcs if rsrc.strip()]
        self._rfile = rfile

        self._iterobj = (Location,)
        self._container = None

        self._comment = COMMENT_PREFIX

    def _parse_rsrcs(self):
        for rsrc in self._rsrcs:
            if rsrc.startswith(self._comment):
                continue
            yield rsrc

    @property
    def rsrcs(self):
        return list(self._parse_rsrcs())

    def __len__(self):
        return len(self.rsrcs)

    def _iterate(self):
        for rsrc in self.rsrcs:
            obj, *args = self._iterobj
            yield obj(rsrc, *args)

    def __iter__(self):
        if self._container is None:
            self._container = list(self._iterate())
        return self._container.__iter__()


class Location(urlmap.Map):
    """Implement concrete url and system path conversion."""

    PREFIX = DOWNLOAD_DIR
    OVERWRITE = False

    HASH_DIR = '_hash'

    def _map_name(self, name):
        name = super()._map_name(name)  # may modify self._hashed
        if self._hashed:
            return self.sep.join(
                (self.PREFIX, self.HASH_DIR, name))
        else:
            return self.sep.join((self.PREFIX, name))

    @property
    def efile(self):
        if self.OVERWRITE:
            return self.dfile
        return self.mapped_name

    @property
    def slash_efile(self):
        return urlmap._path2url(self.efile)

    @property
    def idna_url(self):
        # This is only used when downloading remote resources.
        # So every other name representations are kept unicode.
        # cf. https://github.com/kjd/idna implements newer idna spec.
        def to_ascii(s):
            return s.encode('idna').decode('ascii')

        url = self.rsrc
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


class Component(urlmap.Ref):
    """Create relative reference for class 'Location'."""

    _CLS = Location
    _INHERIT = ('PREFIX',)

    @property
    def idna_url(self):
        return self.url

    @property
    def relative_reference(self):
        path, basepath, url = self.dfile, self._parent_cls.efile, self.url
        return get_relative_reference(path, basepath, url)


class ReplacementParser(object):
    """Parse rsrc replacement file and return new rsrcs.

    The format:
        zero or more units

    The unit:
        one regex pattern line
        one regex replacement line
        blank line(s) or EOF
        (lines starting with '#' are ignored)
    """

    def __init__(self, replacefile, rsrcs=None, rfile=None):
        self.replacefile = replacefile
        self.rsrcs = rsrcs
        self.rfile = rfile
        self.state = None
        self.result = None

    def __call__(self):
        if not os.path.isfile(self.replacefile):
            return self.rsrcs
        rsrcs = self._parse()
        return rsrcs

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
        Parse a line of rsrc replacement file.

        state:
            0: before the first line
            1: done reading the first line
            2: done reading the second line
        """
        line = line.strip()
        errormsg = "Can't parse replace.txt: [%d] %s" % (i, line or "''")
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
        newrsrcs = []
        for rsrc in self.rsrcs:
            for regex in self.result:
                rsrc = regex(rsrc)
            newrsrcs.append(rsrc)
        return newrsrcs
