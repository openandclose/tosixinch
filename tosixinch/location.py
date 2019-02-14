
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

COMMENT_PREFIX = (';',)
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


def _is_local(url):
    if SCHEMES.match(url):
        return False
    # m = OTHER_SCHEMES.match(url)
    # if m:
    #     msg = 'Only http, https and file schemes are supported, got %r'
    #     raise ValueError(msg % m.group(1))
    return True


class Directive(object):
    """Represent a special line that is not a url, in ufile.

    They are usually ignored (skipped in urls iteration).
    """

    def __init__(self, line):
        self.line = line


class Locations(object):
    """Make ``Location`` object and implement iteration."""

    def __init__(self, urls=None, ufile=None):
        if not (urls or ufile):
            fmt = ('Either urls or ufile must be provided. '
                'Got urls: %r, ufile: %r.')
            raise ValueError(fmt % (urls, ufile))

        if not urls:
            with open(ufile) as f:
                urls = [url.strip() for url in f if url.strip()]

        self._ufile = ufile
        self._urls = urls

        self._iterobj = (Location,)

    def _parse_url(self, url):
        if _is_local(url):
            url = os.path.expanduser(url)
            url = os.path.expandvars(url)
            url = os.path.abspath(url)
            if not os.path.exists(url):
                raise FileNotFoundError('File not found: %r' % url)
            if os.path.isdir(url):
                raise IsADirectoryError('Got directory name: %r' % url)
        return url

    def _iterate(self, with_directive=False):
        for url in self._urls:
            if url.startswith(COMMENT_PREFIX):
                continue
            if url.startswith(DIRECTIVE_PREFIX):
                if with_directive:
                    yield Directive(url)
                continue

            obj = self._iterobj
            url = self._parse_url(url)
            yield obj[0](url, *obj[1:])

    def __iter__(self):
        return self._iterate()


class _Location(object):
    """Calculate filepaths."""

    def __init__(self, url):
        self.url = url

    def _make_directories(self, fname):
        if not self._in_current_dir(fname):
            msg = 'filename path is outside of current dir: %r' % fname
            logger.error(msg)
            sys.exit(1)
        dname = os.path.abspath(os.path.dirname(fname))
        os.makedirs(dname, exist_ok=True)

    def _in_current_dir(self, fname, base=os.curdir):
        current = os.path.abspath(base)
        filepath = os.path.abspath(fname)
        if filepath.startswith(current):
            return True
        else:
            return False

    def _make_path(self, url, ext='html', platform=sys.platform):
        if _is_local(url):
            return url
        fname = SCHEMES.sub('', url)
        fname = fname.split('#', 1)[0]
        if '/' not in fname:
            fname += '/'
        root, ext = posixpath.splitext(fname)
        if not ext:
            fname = posixpath.join(fname, 'index--tosixinch')
        if platform == 'win32':
            fname = fname.replace('/', '\\')
        fname = os.path.join(DOWNLOAD_DIR, fname)
        return fname

    def _make_new_fname(self,
            fname, appendix='--extracted', ext='html', platform=sys.platform):
        base = os.path.join(os.curdir, DOWNLOAD_DIR)
        if not self._in_current_dir(fname, base=base):
            fname = self._strip_root(fname, platform)
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

    def _strip_root(self, fname, platform):
        if platform == 'win32':
            drive = None
            m = WINROOTPATH.match(fname)
            # cf. 'C:aaa.txt' means 'aaa.txt' in current directory.
            if m.group(2):
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
    def fname(self):
        return self._make_path(self.url)

    @property
    def fnew(self):
        return self._make_new_fname(self.fname)

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


# MEMO:

# url is:
#     scheme://authority/path;parameters?query#fragment
# Authority is:
#     user:password@host:port

# Reserved characters are:
#     gen-delims:  #/:?@[]
#     sub-delims:  !$&'()*+,;=

# Allowed characters for each url components are:
# (This is a simplified version of RFC3986 one.)
#     userinfo  = *( unreserved / pct-encoded / sub-delims / ":" )
#     host      = *( unreserved / pct-encoded / sub-delims / "[" / "]" )
#     port      = *DIGIT
#     path      = *( unreserved / pct-encoded / sub-delims / ":" / "@")
#     query     = *( unreserved / pct-encoded / sub-delims / ":" / "@" / "/" / "?" )  # noqa: E501
#     fragment  = *( unreserved / pct-encoded / sub-delims / ":" / "@" / "/" / "?" )  # noqa: E501

# https://msdn.microsoft.com/en-us/library/aa365247
# https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words
# Windows illigal filename characters are:
#     /:?*\"<>|

# Note:

# Even princexml began escaping '?' arround 2015.
# https://www.princexml.com/forum/topic/2914/svg-filenames-with-special-characters  # noqa: E501


# URL Quoting Rules:

# In some places in the script,
# We rewrite ``src`` or ``href`` links to refer to downloaded new local files.

# The general principle is that
# for local filenames, we unquote all characters in urls,
# because human readability is more important.

# It is 'lossy' conversion,
# e.g. filename 'aaa?bbb' might have been url 'aaa?bbb' or 'aaa%3Fbbb'.

# Link urls are made using original urls as much as possible.
# Only delimiters for the specific url components are newly quoted
# (A very limited set of reserved characters).

# Note that link urls are always scheme-less and authority-less,
# because they refer to 'our' local files.
# Local files are made from
# stripping scheme and turning authority to the first path.

# So path component now might have special characters for authority.
# Which is '@:[]', in which '[]' have special meaning for path,
# which is 'Error' (illegal characters), so we have to quote them.

# Query delimiter is first '?',
# and query and fragment can have second and third '?',
# so we have to quote all occurences of '?'.

# Query and fragment can also have '/',
# and seem to do some special things.
# For querry, we change it to some other nonspecial character,
# because otherwise it might make too many directories.
# For fragment, we keep it as it is.

# According to RFC, parameters are not used, password is deprecated.
# So we ignore ';', but consider ':', respectively.

# For Windows, illigal filename characters are all changed to '_'.
# More semantic changing may be possible (e.g. '<' to '['),
# but the selecting the right ones is rahter difficult.

# For now, we are ignoring ascii control characters.


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
    '%': '%25',
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

    def __init__(self, url, base, platform=None):
        if not platform:
            self.platform = sys.platform

        if isinstance(base, str):
            base = Location(base)
        self.base = base

        if self.platform == 'win32':
            url = self._remove_windows_chars(url)
        url = self._normalize_source_url(url, base.url)
        url = urllib.parse.urljoin(base.url, url)
        self.url = url

    def _normalize_source_url(self, url, base):
        # It seems relative references are not uniformly handled by libraries.
        # So we'd better manually expand them.
        # cf. https://tools.ietf.org/html/rfc3986#section-4.2
        if url.startswith('//'):
            url = urllib.parse.urlsplit(base)[0] + ':' + url
        elif url.startswith('/'):
            url = '://'.join(urllib.parse.urlsplit(base)[0:2]) + url
        return url

    def make_local_references(self):
        return self._make_local_references(self.fname)

    def _make_local_references(self, url):
        local_url = self._make_local_url(url)
        fname = self._make_filename(url, self.platform)
        return local_url, fname

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

    def _make_filename(self, url, platform=sys.platform):
        parts = urllib.parse.urlsplit(url)
        newparts = []
        for part, delimiters in zip(parts, _delimiters):
            for delim in delimiters.change:
                part = part.replace(delim, _changes[delim])
            newparts.append(part)
        url = urllib.parse.urlunsplit(newparts)

        fname = urllib.parse.unquote(url)
        if platform == 'win32':
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
    def components(self):
        return self.make_local_references()

    @property
    def component_url(self):
        pass

    @property
    def component_fname(self):
        pass

    @property
    def relative_component_fname(self):
        pass
