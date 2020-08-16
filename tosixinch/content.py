
"""Module for html content nmanipulations."""

import logging
import posixpath
import re

from tosixinch import location
from tosixinch import lxml_html
from tosixinch import imagesize

from tosixinch.urlmap import _split_fragment, _add_fragment

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

BLANK_HTML = '%s<html><body></body></html>'

DEFAULT_DOCTYPE = '<!DOCTYPE html>'
DEFAULT_TITLE = 'notitle'


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


def build_blank_html(doctype=None):
    """Build 'more' minimal html."""
    html = BLANK_HTML % (doctype or DEFAULT_DOCTYPE)
    root = lxml_html.document_fromstring(html)
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


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None, errors='strict'):
    if len(paths) > 1:
        hname = pdfname.replace('.pdf', '.html')
        root = build_blank_html()
        _append_bodies(root, hname, paths, codings, errors)
        lxml_html.write(hname, doc=root)
        return hname
    else:
        return paths[0]


def _append_bodies(root, rootname, fnames, codings, errors):
    for fname in fnames:
        doc = lxml_html.read(fname, codings=codings, errors=errors)
        bodies = doc.xpath('//body')
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
        for el in self.doc.iter(lxml_html.etree.Element):
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
