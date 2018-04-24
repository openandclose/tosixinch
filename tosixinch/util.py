
"""Collect utility functions to be used by other modules."""

import collections
import logging
import os
import posixpath
import re
import subprocess
import sys
import urllib.parse

from tosixinch import _ImportError
from tosixinch import imagesize
from tosixinch import manuopen
from tosixinch import templite

try:
    import lxml.etree
    import lxml.html
except ImportError:
    lxml = _ImportError('lxml')

logger = logging.getLogger(__name__)

PLATFORM = sys.platform

DOWNLOAD_DIR = '_htmls'

# Only http and https schemes are permitted.
SCHEMES = re.compile('^https?://', flags=re.IGNORECASE)
# Follows https://github.com/Kozea/WeasyPrint
# cf. urlsplit(r'c:\aaa\bb') returns
# SplitResult(scheme='c', netloc='', path='\\aaa\\bb')
OTHER_SCHEMES = re.compile('^([a-zA-Z][a-zA-Z0-9.+-]+):')

ROOTPATH = re.compile('^/+')
WINROOTPATH = re.compile(r'^(?:([a-zA-z]):([/\\]*)|[/?\\]+)')

HTMLEXT = ('htm', 'html')
_COMMENT = r'\s*(<!--.+?-->\s*)*'
_XMLDECL = r'(<\?xml version.+? \?>)?'
_DOCTYPE = '(<!doctype .+?>)?'
HTMLFILE = re.compile(
    '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + '<html(| .+?)>',
    flags=re.IGNORECASE | re.DOTALL)

PYTHONEXT = ('py',)
PYTHONFILE = re.compile((
    r'^(?:'
    r'#!.+python'
    r'|\s*import'
    ')'
))


_HTML_HEAD = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>%s</title>
  </head>
  <body>
"""

_HTML_TAIL = """  </body>
</html>"""

HTML_TEMPLATE = _HTML_HEAD + '%s' + _HTML_TAIL

BLANK_HTML = '%s<html><body></body></html>'

DEFAULT_DOCTYPE = '<!DOCTYPE html>'
DEFAULT_TITLE = 'notitle'

KEEP_STYLE = 'tsi-keep-style'

# https://github.com/sindresorhus/binary-extensions
BINARY_EXTENSIONS = """
    3ds 3g2 3gp 7z a aac adp ai aif aiff alz ape apk ar arj asf au avi bak bh
    bin bk bmp btif bz2 bzip2 cab caf cgm class cmx cpio cr2 csv cur dat deb
    dex djvu dll dmg dng doc docm docx dot dotm dra DS_Store dsk dts dtshd dvb
    dwg dxf ecelp4800 ecelp7470 ecelp9600 egg eol eot epub exe f4v fbs fh fla
    flac fli flv fpx fst fvt g3 gif graffle gz gzip h261 h263 h264 ico ief img
    ipa iso jar jpeg jpg jpgv jpm jxr key ktx lha lvp lz lzh lzma lzo m3u m4a
    m4v mar mdi mht mid midi mj2 mka mkv mmr mng mobi mov movie mp3 mp4 mp4a
    mpeg mpg mpga mxu nef npx numbers o oga ogg ogv otf pages pbm pcx pdf pea
    pgm pic png pnm pot potm potx ppa ppam ppm pps ppsm ppsx ppt pptm pptx psd
    pya pyc pyo pyv qt rar ras raw rgb rip rlc rmf rmvb rtf rz s3m s7z scpt sgi
    shar sil sketch slk smv so sub swf tar tbz tbz2 tga tgz thmx tif tiff tlz
    ttc ttf txz udf uvh uvi uvm uvp uvs uvu viv vob war wav wax wbmp wdp weba
    webm webp whl wim wm wma wmv wmx woff woff2 wvx xbm xif xla xlam xls xlsb
    xlsm xlsx xlt xltm xltx xm xmind xpi xpm xwd xz z zip zipx
""".split()


# (MEMO):

# url is:
#     scheme://authority/path;parameters?query#fragment
# Authority is:
#     user:password@host:port

# Reserved characters are:
#     gen-delims:  #/:?@[]
#     sub-delims:  !$&'()*+,;=

# Allowed characters foe each url components are:
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


# url quoting rules:

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


def make_local_references(url, platform=PLATFORM):
    if platform == 'win32':
        url = _remove_windows_chars(url)
    local_url = _make_local_url(url)
    fname = _make_filename(url, platform)
    return local_url, fname


def _make_local_url(url):
    parts = urllib.parse.urlsplit(url)
    newparts = []
    for part, delimiters in zip(parts, _delimiters):
        for delim in delimiters.quote:
            part = part.replace(delim, _quotes[delim])
        for delim in delimiters.change:
            part = part.replace(delim, _changes[delim])
        newparts.append(part)
    return _urlunsplit_no_query(newparts)


def _make_filename(url, platform=PLATFORM):
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


def _remove_windows_chars(url):
    for key, value in _win_changes.items():
        url = url.replace(key, value)
        url = url.replace(_quotes[key], value)
    return url


def _urlunsplit_no_query(parts):
    url = urllib.parse.urlunsplit((*parts[:3], '', ''))
    if parts[3]:
        url = '%3F'.join((url, parts[3]))
    if parts[4]:
        url = '%23'.join((url, parts[4]))
    return url


def parse_ufile(ufile):
    urls, dirs = _parse_ufile(ufile)
    return urls


def parse_tocfile(ufile):
    urls, dirs = _parse_ufile(ufile, is_toc=True)
    return urls


def parse_urls(urls):
    urls, dirs = _parse_urls(urls)
    return urls


def _parse_ufile(ufile, is_toc=False, dir_error=True):
    def is_comment(url):
        comment_prefix = (';',) if is_toc else ('#', ';')
        if url.startswith(comment_prefix):
            return True

    urls = []
    with open(ufile) as f:
        for url in f:
            url = url.strip()
            if not url:
                continue
            if is_comment(url):
                continue
            urls.append(url)
    urls, dirs = _parse_urls(urls, dir_error)
    return urls, dirs


def _parse_urls(urllist, dir_error=True):
    urls = []
    dirs = []
    for url in urllist:
        url, directory = _normalize_input_url(url, dir_error)
        if url:
            urls.append(url)
        else:
            dirs.append(directory)

    if urls and dirs:
        msg = 'You cannot mix directory names with file names or urls'
        raise ValueError(msg)

    return urls, dirs


def _normalize_input_url(url, dir_error=True):
    if is_local(url):
        url = os.path.expanduser(url)
        url = os.path.expandvars(url)
        url = os.path.abspath(url)
        if not os.path.exists(url):
            raise FileNotFoundError('File not found: %r' % url)
        if os.path.isdir(url):
            if dir_error:
                raise IsADirectoryError('Got directory name: %r' % url)
            return None, url
    return url, None


def is_local(url):
    if SCHEMES.match(url):
        return False
    if url.startswith('#'):
        return False
    # m = OTHER_SCHEMES.match(url)
    # if m:
    #     msg = 'Only http, https and file schemes are supported, got %r'
    #     raise ValueError(msg % m.group(1))
    return True


def idna_quote(url):
    # This is only used by `download` module internally.
    # So every other resource name representations are kept unicode.
    def to_ascii(s):
        # cf. https://github.com/kjd/idna implements newer idna spec.
        return s.encode('idna').decode('ascii')

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


def normalize_source_url(url, base_url):
    # It seems relative references are not uniformly handled by libraries.
    # So we'd better manually expand them.
    # cf. https://tools.ietf.org/html/rfc3986#section-4.2
    if url.startswith('//'):
        url = urllib.parse.urlsplit(base_url)[0] + ':' + url
    elif url.startswith('/'):
        url = '://'.join(urllib.parse.urlsplit(base_url)[0:2]) + url
    return url


def make_directories(fname):
    if not _in_current_dir(fname):
        msg = 'filename path is outside of current dir: %r' % fname
        logger.error(msg)
        sys.exit(1)
    dname = os.path.abspath(os.path.dirname(fname))
    os.makedirs(dname, exist_ok=True)


def _in_current_dir(fname, base=os.curdir):
    current = os.path.abspath(base)
    filepath = os.path.abspath(fname)
    if filepath.startswith(current):
        return True
    else:
        return False


def make_path(url, ext='html', platform=PLATFORM):
    if is_local(url):
        return url
    fname = SCHEMES.sub('', url)
    fname = fname.split('#', 1)[0]
    if '/' not in fname:
        fname += '/'
    # if fname.endswith('/'):
    #     fname = _edit_fname(fname, 'index--tosixinch')
    root, ext = posixpath.splitext(fname)
    if not ext:
        fname = posixpath.join(fname, 'index--tosixinch')
    if platform == 'win32':
        fname = fname.replace('/', '\\')
    fname = os.path.join(DOWNLOAD_DIR, fname)
    return fname


def _edit_fname(fname, appendix=None, default_ext=None):
    root, ext = os.path.splitext(fname)
    if appendix:
        root = root + appendix
    if default_ext:
        if ext and ext[1:] == default_ext:
            pass
        else:
            ext = ext + '.' + default_ext
    return root + ext


def make_new_fname(
        fname, appendix='--extracted', ext='html', platform=PLATFORM):
    base = os.path.join(os.curdir, DOWNLOAD_DIR)
    if not _in_current_dir(fname, base=base):
        fname = _strip_root(fname, platform)
        fname = os.path.join(DOWNLOAD_DIR, fname)
    return _edit_fname(fname, appendix, ext)


def _strip_root(fname, platform):
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


def check_ftype(fname, codings=None):
    """Open a file and detect file type.

    Return a tuple (ftype, kind, text)
    """
    text = manuopen.manuopen(fname, codings=codings)
    if is_html(text):
        return 'html', None, text
    elif is_prose(text):
        return 'prose', None, text
    else:
        if is_code(fname, text):
            return 'code', 'python', text
        else:
            return 'nonprose', None, text


def is_html(text):
    if len(text) > 1000 and HTMLFILE.match(text[:1000]):
        return True
    return False


def is_prose(text):
    """Check if text is prose or not.

    Here 'prose' means general texts
    other than non-prose (source code or poetry etc.).
    We want to separate them
    because the roles of newline are somewhat different between them.
    They require different text wrap strategies.
    """
    lines = text[:10000].split('\n')[:-1]
    counts = (len(line) for line in lines)
    if any((count > 400 for count in counts)):
        # If lines are unusually long, we give up.
        return True
    width = 0
    continuation = 0
    times = 0
    for count in counts:
        if count > width:
            width = count
            if count > width + 1:
                continuation = 0
        elif count in (width, width - 1):
            continuation += 1
        else:
            if continuation > 1:
                times += 1
            continuation = 0
        if times > 1:
            return True
    return False


def is_code(fname, text=None):
    # For now, only for python code
    ext = fname.rsplit('.', maxsplit=1)
    if len(ext) == 2 and ext[1] in PYTHONEXT:
        return True
    if PYTHONFILE.match(text):
        return True
    return False


def lxml_open(fname=None, text=None, codings=None):
    if not text:
        text = manuopen.manuopen(fname, codings=codings)
    parser = lxml.html.HTMLParser(encoding='utf-8')
    # For now, follows ``readability.htmls``,
    # in redundant utf-8 encoding-decoding.
    root = lxml.html.document_fromstring(
        text.encode('utf-8', 'replace'), parser=parser)
    return root


def lxml_write(fname, doc, doctype=DEFAULT_DOCTYPE):
    html = lxml.html.tostring(doc, encoding='unicode', doctype=doctype)
    if not os.path.exists(fname):
        make_directories(fname)
    with open(fname, 'w') as f:
        f.write(html)


def build_new_html(title=None, content=''):
    """Build minimal html to further edit."""
    if title is None:
        title = DEFAULT_TITLE
    html = HTML_TEMPLATE % (title, content)
    root = lxml.html.document_fromstring(html)
    return root


def build_blank_html(doctype=None):
    """Built 'more' minimal html, used in `extract.Extract._prepare`."""
    if doctype is None:
        doctype = DEFAULT_DOCTYPE
    html = BLANK_HTML % doctype
    root = lxml.html.document_fromstring(html)
    return root


def conditioned_iter(el, test):
    """Recursively iterate on an element, yield just matching ones.

    It is like ``element.iter(condition)``,
    but this one skips unmatched element as a tree,
    with its subelements all together.
    It seems lxml doesn't have this functionality, ``iter`` or otherwise.

    cf. ``.xpath()`` could do this kind of things,
    but not suited for more than simplest condition tests.

    Argument ``el`` is presupposed to be an single ``lxml.etree.element``.
    No checks are done.
    """
    if not test(el):
        return
    yield el
    if len(el) == 0:
        return
    for sub in el:
        yield from conditioned_iter(sub, test)


def iter_component(doc):
    """Get inner links needed to download or modify in a html.

    Used in extract.py and toc.py.
    """
    for el in doc.xpath('//img'):
        urls = el.xpath('./@src')
        if not urls:
            continue
        url = urls[0]

        # For data url (e.g. '<img src=data:image/png;base64,iVBORw0K...'),
        # just pass it on to pdf conversion libraries.
        if url.startswith('data:image/'):
            continue

        if _skip_sites(url):
            continue

        yield el, url


def xpath_select(el, string):
    try:
        return el.xpath(string)
    except lxml.etree.LxmlError as e:
        _e = e.error_log.last_error
        n = _e.column
        s = string[:n] + '^^^ ' + string[n] + ' ^^^' + string[n + 1:]
        fmt = ("Xpath error occured probably at column %s "
               "(find the mark '^^^'):\n%s\n")
        logger.error(fmt, n, s)
        raise


# experimental
def _skip_sites(url):
    sites = ()
    # sites = ('gravatar.com/', )
    for site in sites:
        if site in url:
            return True
    return False


def get_component_size(el, fname, stream=None):
    # Get size from html attributes (if any and the unit is no unit or 'px').
    w = el.get('width')
    h = el.get('height')
    if w and h:
        match = re.match('^([0-9.]+)(?:px)?$', w)
        w = int(match[1]) if match else None
        match = re.match('^([0-9.]+)(?:px)?$', h)
        h = int(match[1]) if match else None
    if w and h:
        return w, h

    # Get size from file header (if possible).
    try:
        mime, w, h = imagesize.get_size(fname, stream)
        return int(w), int(h)
    except FileNotFoundError:
        return None, None
    except ValueError:
        return None, None


def transform_xpath(path):
    pat = re.compile(r'([a-zA-Z]+|[hH][1-6]|\*)\[@class==([\'"]*)([a-zA-Z-_]+)\2\]')  # noqa: E501
    repl = r'\1[contains(concat(" ", normalize-space(@class), " "), " \3 ")]'
    return pat.sub(repl, path)


# https://github.com/django/django/blob/master/django/utils/text.py
def slugify(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return value


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None):
    if len(paths) > 1:
        hname = pdfname.replace('.pdf', '.html')
        root = build_blank_html()
        _append_bodies(root, hname, paths, codings)
        lxml_write(hname, root)
        return hname
    else:
        return paths[0]


def _append_bodies(root, rootname, fnames, codings=None):
    for fname in fnames:
        bodies = lxml_open(fname, codings=codings).xpath('//body')
        for b in bodies:
            _relink_component(b, rootname, fname)
            b.tag = 'div'
            b.set('class', 'tsi-body-merged')
            root.body.append(b)


def _relink_component(doc, rootname, fname):
    for el, url in iter_component(doc):
        # print(url)
        url = posixpath.join(posixpath.dirname(fname), url)
        # print(url, 'joined')
        url = posixpath.relpath(url, start=posixpath.dirname(rootname))
        url = posixpath.normpath(url)
        # print(url, 'relpathed')
        el.attrib['src'] = url


def render_template(csspath, new_csspath, context):
    with open(csspath) as f:
        template = f.read()
    template = templite.Templite(template)
    text = template.render(context)
    with open(new_csspath, 'w') as f:
        f.write(text)


def runcmd(conf, cmds):
    if cmds:
        cmds[:] = [_eval_conf(conf, word) for word in cmds]
        paths = _add_path_env(conf)

        # return subprocess.Popen(cmds).pid
        return subprocess.run(cmds, env=dict(os.environ, PATH=paths))


def _eval_conf(conf, word):
    if not word.startswith('conf.'):
        return word

    for w in word.split('.'):
        if not w.isidentifier():
            return word

    return str(eval(word, {'conf': conf}))


def _add_path_env(conf):
    psep = os.pathsep
    scriptdir = os.path.dirname(conf._configdir) + os.sep + 'script'
    paths = conf._userdir + psep + scriptdir + psep
    paths = paths + os.environ['PATH']
    paths = paths.rstrip(psep)
    return paths
