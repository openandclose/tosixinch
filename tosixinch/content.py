
"""Module for html content nmanipulations."""

import logging
import posixpath
import re

from tosixinch import location
from tosixinch import lxml_html
from tosixinch import imagesize

from tosixinch.urlmap import _split_fragment, _add_fragment

import tosixinch.process.sample as process_sample

logger = logging.getLogger(__name__)

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

DEFAULT_DOCTYPE = '<!DOCTYPE html>'
DEFAULT_TITLE = 'notitle'

LINK_ATTRS = lxml_html.link_attrs
COMP_ATTRS = (('img', 'src'),)  # tuple of tag-attribute tuples


def build_new_html(doctype=None, title=None, content=None):
    """Build minimal html to further edit."""
    fdict = {
        'doctype': doctype or DEFAULT_DOCTYPE,
        'title': title or DEFAULT_TITLE,
        'content': content or ''
    }
    html = HTML_TEMPLATE.format(**fdict)
    root = lxml_html.document_fromstring(html)
    return root


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


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None, errors='strict'):
    if len(paths) > 1:
        if pdfname[-4:].lower() == '.pdf':
            hname = pdfname[:-4] + '.html'
        else:
            hname = pdfname + '.html'
        root = build_new_html()
        Merger(root, hname, paths, codings, errors).merge()
        return hname
    else:
        return paths[0]


def _relink_component(doc, rootname, fname):
    for el in doc.iter(lxml_html.etree.Element):
        for tag, attr in COMP_ATTRS:
            if el.tag == tag and attr in el.attrib:
                url = el.attrib[attr].strip()
                url = _relink(url, fname, rootname)
                el.attrib['src'] = url


def _relink(url, prev_base, new_base):
    url = posixpath.join(posixpath.dirname(prev_base), url)
    url = posixpath.relpath(url, start=posixpath.dirname(new_base))
    url = posixpath.normpath(url)
    return url


class BaseResolver(object):
    """Rewrite relative references in html doc."""

    def __init__(self, doc, loc, locs, baseurl=None):
        self.doc = doc
        self.loc = loc
        self.sibling_urls = {k: v for k, v in self._build_sibling_urls(locs)}
        self.baseurl = baseurl
        self._comp_cache = {}

    def _build_sibling_urls(self, locs):
        for loc in locs:
            path, basepath, url = loc.fnew, self.loc.fnew, loc.url
            ref = location.get_relative_reference(path, basepath, url)
            yield loc.url, ref

    def _get_comp_cache(self, url):
        if not self._comp_cache.get(url):
            comp = location.Component(url, self.loc, baseurl=self.baseurl)
            self._comp_cache[url] = comp
        return self._comp_cache[url]

    def _get_url_data(self, el, attr):
        url = el.attrib[attr].strip()
        url, fragment = _split_fragment(url)
        comp = self._get_comp_cache(url)
        return comp, url, fragment

    def resolve(self):
        for el in self.doc.iter(lxml_html.etree.Element):
            self.get_component(el)
            self._resolve(el)

    def get_component(self, el):
        for tag, attr in COMP_ATTRS:
            if el.tag == tag and attr in el.attrib:
                comp, url, fragment = self._get_url_data(el, attr)
                self._get_component(el, comp)
                self._set_component(comp)

    def _get_component(self, el, comp):
        pass

    def _set_component(self, comp):
        self.sibling_urls[comp.url] = comp.relative_reference

    def _resolve(self, el):
        for attr in LINK_ATTRS:
            if attr in el.attrib:
                comp, url, fragment = self._get_url_data(el, attr)
                url = comp.url
                if url in self.sibling_urls:
                    ref = _add_fragment(self.sibling_urls[url], fragment)
                else:
                    ref = _add_fragment(url, fragment)
                el.attrib[attr] = ref


class Merger(object):
    """Merge htmls (toc, and weasyprint)."""

    def __init__(self, doc, root, children, codings=None, errors='strict'):
        self.doc = doc
        self.root = root  # root file name
        self.children = children  # list of child file names
        self.codings = codings
        self.errors = errors

        self._h1 = self.check_heading()
        self._css_cache = []

    def check_heading(self):
        if self.doc.xpath('//h1'):
            return True
        return False

    def merge(self):
        codings, errors = self.codings, self.errors
        for child in self.children:
            doc = lxml_html.read(child, codings=codings, errors=errors)
            self.append_css(child, doc)
            self.append_body(child, doc)

        self.write()

    # Note: omitting 'ref -> path ->ref' transformations below

    def append_css(self, child, doc):
        for el in doc.xpath('//head/link[@rel="stylesheet"]'):
            href = el.get('href') or ''
            if href and href not in self._css_cache:
                self._css_cache.append(href)

                href = _relink(href, child, self.root)
                el.set('href', href)
                self.doc.head.append(el)

    def append_body(self, child, doc):
        for b in doc.xpath('//body'):
            if self._h1:
                process_sample.lower_heading(b)
            _relink_component(b, self.root, child)
            b.tag = 'div'
            b.set('class', 'tsi-body-merged')
            self.doc.body.append(b)

    def write(self):
        lxml_html.write(self.root, doc=self.doc)
