
"""Module for html content nmanipulations."""

import logging
import posixpath
import re

from tosixinch import _ImportError
from tosixinch import clean
from tosixinch import location
from tosixinch import imagesize
from tosixinch import system

import tosixinch.process.sample as process_sample

from tosixinch.urlmap import _split_fragment, _add_fragment

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
_DOCTYPE = r'(<!doctype\s+.+?>)?'
HTMLFILE = re.compile(
    '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + r'<html(|\s.+?)>',
    flags=re.IGNORECASE | re.DOTALL)

HTML_TEMPLATE = """{doctype}
<html>
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
  </head>
  <body>
{content}
  </body>
</html>
"""

HTML_TEXT_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    {csslinks}
</head>
  <body>
    <h1 class="{textclass}">{title}</h1>
    <pre class="{textclass}">
{content}
    </pre>
  </body>
</html>"""

BLANK_HTML = '%s<html><body></body></html>'

DEFAULT_DOCTYPE = '<!DOCTYPE html>'
DEFAULT_TITLE = 'notitle'

# c.f. 'media="print"' does't work for wkhtmltopdf.
EXTERNAL_CSS = '<link class="tsi-css" href="%s" rel="stylesheet">'


def is_html(fname, text, min_chars=4096):
    if HTMLFILE.match(text[:min_chars]):
        return True
    return False


def build_new_html(doctype=None, title=None, content=None):
    """Build minimal html to further edit."""
    fdict = {
        'doctype': doctype or DEFAULT_DOCTYPE,
        'title': title or DEFAULT_TITLE,
        'content': content or ''
    }
    html = HTML_TEMPLATE.format(**fdict)
    root = lxml.html.document_fromstring(html)
    return root


def build_blank_html(doctype=None):
    """Build 'more' minimal html."""
    html = BLANK_HTML % (doctype or DEFAULT_DOCTYPE)
    root = lxml.html.document_fromstring(html)
    return root


def build_external_css(html_path, cssfile_path):
    """Build external css tag (link) string, resolving the paths."""
    url = location.path2ref(cssfile_path, html_path)
    return EXTERNAL_CSS % url


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
        fmt = ("Xpath error occured probably at column %d "
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
    except OSError:  # 'File name too long' etc.
        return None, None
    except ValueError:  # imagesize failed to guess
        return None, None


# https://github.com/django/django/blob/master/django/utils/text.py
def slugify(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None, errors='strict'):
    if len(paths) > 1:
        hname = pdfname.replace('.pdf', '.html')
        root = build_blank_html()
        _append_bodies(root, hname, paths, codings, errors)
        system.HtmlWriter(hname, doc=root).write()
        return hname
    else:
        return paths[0]


def _append_bodies(root, rootname, fnames, codings, errors):
    for fname in fnames:
        reader = system.HtmlReader(fname, codings=codings, errors=errors)
        bodies = reader.read().xpath('//body')
        for b in bodies:
            _relink_component(b, rootname, fname)
            b.tag = 'div'
            b.set('class', 'tsi-body-merged')
            root.body.append(b)


def _relink_component(doc, rootname, fname):
    for el, url in iter_component(doc):
        url = _relink(url, fname, rootname)
        el.attrib['src'] = url


def _relink(url, prev_base, new_base):
    url = posixpath.join(posixpath.dirname(prev_base), url)
    url = posixpath.relpath(url, start=posixpath.dirname(new_base))
    url = posixpath.normpath(url)
    return url


class _Content(object):
    """Represent general content."""

    def __init__(self, loc, text=None, codings=None, errors='strict'):
        if isinstance(loc, str):
            loc = location.Location(loc, input_type='url')

        self._loc = loc
        self.url = loc.url
        self.fname = loc.fname
        self.fnew = loc.fnew

        self.text = text
        self.codings = codings
        self.errors = errors


class SimpleHtmlContent(_Content):
    """Define basic (non-extract) HtmlElement manupulations."""

    def read(self, fname, text):
        reader = system.HtmlReader(fname, text,
            codings=self.codings, errors=self.errors)
        return reader.read()

    def load(self):
        self.doc = self.read(fname=self.fnew, text=None)

    def add_css(self, cssfiles):
        for cssfile in cssfiles:
            url = build_external_css(self.fnew, cssfile)
            el = lxml.html.fragment_fromstring(url)
            self.doc.head.append(el)

    def write(self):
        writer = system.HtmlWriter(self.fnew, doc=self.doc)
        writer.write()


class HtmlContent(SimpleHtmlContent):
    """Define HtmlElement manupulations for extraction."""

    def load(self):
        self.root = self.read(fname=self.fname, text=self.text)

        doctype = self.root.getroottree().docinfo.doctype or DEFAULT_DOCTYPE
        self.doctype = doctype

    def build(self):
        title = self.root.xpath('//title/text()')
        title = title[0] if title else DEFAULT_TITLE
        baseurl = self.root.base or self.url
        logger.debug('[base url] %s', baseurl)

        doc = build_new_html(doctype=self.doctype, title=title)

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

    def clean(self, tags, attrs):
        cleaner = clean.Clean(self.doc, tags, attrs)
        cleaner.run()


class ReadabilityHtmlContent(HtmlContent):
    """Define methods only for readability."""

    def build(self):
        title = readability.Document(self.text).title()
        content = readability.Document(self.text).summary(html_partial=True)

        # ``Readability`` generally does not care about main headings.
        # So we manually insert a probable ``title``.
        doc = build_new_html(title=title, content=content)
        heading = doc.xpath('//h1')
        if len(heading) == 0:
            process_sample.add_h1(doc)
        if len(heading) > 1:
            process_sample.lower_heading(doc)
            process_sample.add_h1(doc)

        self.doc = doc


class BaseResolver(object):
    """Rewrite relative references in html doc."""

    LINK_ATTRS = ('cite', 'href', 'src')
    COMP_ATTRS = (('img', 'src'),)  # tuple of tag-attribute tuples

    def __init__(self, doc, loc, locs):
        self.doc = doc
        self.loc = loc
        self.sibling_urls = {k: v for k, v in self._build_sibling_urls(locs)}
        self._comp_cache = {}

    def _build_sibling_urls(self, locs):
        for loc in locs:
            ref = self.loc.get_relative_reference_fnew(loc)
            yield loc.url, ref

    def _get_comp_cache(self, url):
        if not self._comp_cache.get(url):
            self._comp_cache[url] = location.Component(url, self.loc)
        return self._comp_cache[url]

    def _get_url_data(self, el, attr):
        url = el.attrib[attr].strip()
        url, fragment = _split_fragment(url)
        comp = self._get_comp_cache(url)
        return comp, url, fragment

    def resolve(self):
        for el in self.doc.iter(lxml.etree.Element):
            self.get_component(el)
            self._resolve(el)

    def get_component(self, el):
        for tag, attr in self.COMP_ATTRS:
            if el.tag == tag and attr in el.attrib:
                comp, url, fragment = self._get_url_data(el, attr)
                self._get_component(el, comp)
                self._set_component(comp)

    def _get_component(self, el, comp):
        pass

    def _set_component(self, comp):
        self.sibling_urls[comp.url] = comp.relative_reference

    def _resolve(self, el):
        for attr in self.LINK_ATTRS:
            if attr in el.attrib:
                comp, url, fragment = self._get_url_data(el, attr)
                url = comp.url
                if url in self.sibling_urls:
                    ref = _add_fragment(self.sibling_urls[url], fragment)
                else:
                    ref = _add_fragment(url, fragment)
                el.attrib[attr] = ref
