
"""Module for content nmanipulations (html and text)."""

import copy
import logging
import posixpath
import re

from tosixinch import _ImportError
from tosixinch import clean
from tosixinch import download
from tosixinch import location
from tosixinch import imagesize
from tosixinch import manuopen
from tosixinch.process import gen
from tosixinch import system

try:
    import lxml.etree
    import lxml.html
except ImportError:
    lxml = _ImportError('lxml')

try:
    import readability
except ImportError:
    readability = _ImportError('readability')

logger = logging.getLogger(__name__)

HTMLEXT = ('htm', 'html')
_COMMENT = r'\s*(<!--.+?-->\s*)*'
_XMLDECL = r'(<\?xml version.+?\?>)?'
_DOCTYPE = '(<!doctype .+?>)?'
HTMLFILE = re.compile(
    '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + r'<html(|\s.+?)>',
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
    if len(text) > 4000 and HTMLFILE.match(text[:4000]):
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


def build_new_html(title=None, content=''):
    """Build minimal html to further edit."""
    title = title or DEFAULT_TITLE
    html = HTML_TEMPLATE % (title, content)
    root = lxml.html.document_fromstring(html)
    return root


def build_blank_html(doctype=None):
    """Build 'more' minimal html, used in `extract.Extract._prepare`."""
    doctype = doctype or DEFAULT_DOCTYPE
    html = BLANK_HTML % doctype
    root = lxml.html.document_fromstring(html)
    return root


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
    pat = r'([a-zA-Z]+|[hH][1-6]|\*)\[@class==([\'"])([_a-zA-Z0-9-]+)\2\]'
    pat = re.compile(pat)
    repl = r'\1[contains(concat(" ", normalize-space(@class), " "), " \3 ")]'
    return pat.sub(repl, path)


# https://github.com/django/django/blob/master/django/utils/text.py
def slugify(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None):
    if len(paths) > 1:
        hname = pdfname.replace('.pdf', '.html')
        root = build_blank_html()
        _append_bodies(root, hname, paths, codings)
        system.HtmlWriter(hname, doc=root).write()
        return hname
    else:
        return paths[0]


def _append_bodies(root, rootname, fnames, codings=None):
    for fname in fnames:
        reader = system.HtmlReader(fname, codings=codings)
        bodies = reader.read().xpath('//body')
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


class Content(object):
    """Represent general content."""

    def __init__(self, url, fname, fnew, text=None, codings=None):
        self.url = url
        self.fname = fname
        self.fnew = fnew
        self.text = text
        self.codings = codings


class HtmlContent(Content):
    """Represent html content. Define HtmlElement manupulations."""

    def load(self):
        reader = system.HtmlReader(
            self.fname, text=self.text, codings=self.codings)
        self.root = reader.read()

        doctype = self.root.getroottree().docinfo.doctype or DEFAULT_DOCTYPE
        self.doctype = doctype

    def build(self):
        title = self.root.xpath('//title/text()')
        title = title[0] if title else DEFAULT_TITLE
        baseurl = self.root.base or self.url
        logger.debug('[base url] %s', baseurl)

        doc = build_blank_html(self.doctype)
        head = self.root.head
        if head is not None:
            doc.insert(0, copy.deepcopy(head))
        # or...
        # doc = copy.deepcopy(self.root)
        # doc.body.clear()

        self.title = title
        self.baseurl = baseurl
        self.doc = doc

    def select(self, sel):
        for t in xpath_select(self.root.body, sel):
            self.doc.body.append(t)

    def exclude(self, sel):
        for t in xpath_select(self.doc.body, sel):
            if t.getparent() is not None:
                t.getparent().remove(t)

    def guess_selection(self, guesses):
        for guess in guesses:
            s = xpath_select(self.root, guess)
            if s and len(s) == 1:
                return guess
        return None

    def get_components(self):
        for el, url in iter_component(self.doc):
            self._get_component(el, url)

    def clean(self, tags, attrs):
        cleaner = clean.Clean(self.doc, tags, attrs)
        cleaner.run()

    def write(self):
        writer = system.HtmlWriter(
            self.fnew, doc=self.doc, doctype=self.doctype)
        writer.write()

    def _get_component(self, el, url):
        comp = location.Component(url, self)
        url = comp.url
        src = comp.component_url
        fname = comp.component_fname
        el.attrib['src'] = src
        self._download_component(url, fname)
        # self._add_component_attributes(el, fname)
        return comp

    def _download_component(self, url, fname):
        logger.info('[img] %s', url)
        system.make_directories(fname)
        download.download(url, fname, on_error_exit=False)


class ReadabilityHtmlContent(HtmlContent):
    """Define methods only for readability."""

    def build(self):
        title = readability.Document(self.text).title()
        content = readability.Document(self.text).summary(html_partial=True)

        # ``Readability`` generally does not care about main headings.
        # So we manually insert a probable ``title``.
        doc = build_new_html(title, content)
        heading = doc.xpath('//h1')
        if len(heading) == 0:
            gen.add_title(doc)
        if len(heading) > 1:
            gen.decrease_heading(doc)
            gen.add_title(doc)

        self.doc = doc
