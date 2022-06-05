
"""Module for html content nmanipulations."""

import logging
import posixpath
import re
import zlib

from tosixinch import location
from tosixinch import lxml_html
from tosixinch import imagesize

from tosixinch.urlmap import _split_fragment, _add_fragment

import tosixinch.process.sample as process_sample

logger = logging.getLogger(__name__)

ABS_URL_RE = re.compile('^https?://', flags=re.IGNORECASE)

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
COMP_ATTRS = (  # tuple of tag-attribute tuples
    ('link', 'href'),
    ('img', 'src'),
)


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


def is_abs_url(path):
    if ABS_URL_RE.match(path):
        return True
    return False


def rel2cur(basepath, path):
    # transform 'path' against base path directory,
    # to 'path' against current directory.
    if is_abs_url(path):
        return path
    if path == '':
        return basepath
    po = posixpath
    return po.normpath(po.join(po.dirname(basepath), path))


def cur2rel(basepath, path):
    # transform 'path' against current directory,
    # to 'path' against base path directory.
    if is_abs_url(path):
        return path
    if path == basepath:
        return ''
    po = posixpath
    return po.normpath(po.relpath(path, start=po.dirname(basepath)))


class Resolver(object):
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

    def __init__(self, doc, root, children, table=None,
            hashid=False, codings=None, errors='strict'):
        self.doc = doc
        self.root = root  # root file name
        self.children = children  # list of child file names
        self.table = IDTable(table, hashid=hashid)
        self.hashid = hashid
        self.codings = codings
        self.errors = errors

        self._h1 = self.check_heading()
        self._css_cache = []

    def check_heading(self):
        if self.doc.xpath('//h1'):
            return True
        return False

    def iterate_doc(self, doc):
        for el in doc.iter(lxml_html.etree.Element):
            yield el

    def merge(self):
        self.table.id_cache = {}  # intialization
        codings, errors = self.codings, self.errors
        docs = []
        for child in self.children:
            doc = lxml_html.read(child, codings=codings, errors=errors)
            for el in self.iterate_doc(doc):
                self.relink_id_ref(child, el)
            docs.append(doc)

        for child, doc in zip(self.children, docs):
            self.append_css(child, doc)
            self.append_body(child, doc)

        self.write()

    def append_css(self, child, doc):
        for el in doc.xpath('//head/link[@rel="stylesheet"]'):
            href = el.get('href') or ''
            if href:
                href = rel2cur(child, href)
                if href not in self._css_cache:
                    self._css_cache.append(href)

                    href = cur2rel(self.root, href)
                    el.set('href', href)
                    self.doc.head.append(el)

    def append_body(self, child, doc):
        for b in doc.xpath('//body'):
            if self._h1:
                process_sample.lower_heading(b)
            for el in self.iterate_doc(b):
                self.relink_component(el, self.root, child)
                self.relink_id(child, el)
            b.tag = 'div'
            b.set('id', self.table.path2id(child))
            b.set('class', 'tsi-body-merged')
            self.doc.body.append(b)

    def relink_component(self, el, root, child):
        for tag, attr in COMP_ATTRS:
            if el.tag == tag and attr in el.attrib:
                url = el.attrib[attr].strip()
                url = rel2cur(child, url)
                url = cur2rel(root, url)
                el.attrib[attr] = url

    def relink_id_ref(self, child, el):
        for attr in LINK_ATTRS:
            if attr in el.attrib:
                url = el.attrib[attr].strip()
                new = self.table.get(child, url)  # filling id_cache
                el.attrib[attr] = new

    def relink_id(self, child, el):
        if not self.table.id_cache:
            return
        id_ = el.get('id')
        if not id_:
            return
        new = self.table.id_cache.get((child, id_.strip()))
        if new:
            el['id'] = new

    def write(self):
        lxml_html.write(self.root, doc=self.doc)


class IDTable(object):
    """Process id attributes (fragment links) for merged htmls.

    Receive ``table`` argument,
    which is actually a tuple of tuple (root, children).
    """

    def __init__(self, table, hashid=False):
        self.udict = self.create_dict(table)
        self.hashid = hashid
        self.id_cache = {}

    def create_dict(self, table):
        t = {}
        if table is None:
            return t
        for tup in table:
            root, children = tup
            t[root] = root
            for child in children:
                t[child] = root
        return t

    def get(self, child, url):
        src, fragment = _split_fragment(url)
        if src == '':
            src = child
        else:
            src = rel2cur(child, src)

        dest = self.udict.get(src)
        if dest is None:
            return url

        if not fragment:
            fragment = self.path2id(src)

        child_dest = self.udict.get(child)
        dest = cur2rel(child_dest, dest)

        if not self.hashid or dest == src:
            return _add_fragment(dest, fragment)

        hash_ = self.get_checksum(src)
        new = self.format_hash_frag(src, fragment, hash_)
        self.id_cache[(src, fragment)] = new
        return _add_fragment(dest, new)

    def path2id(self, path):
        return location.slugify(path.split('/')[-1])

    def get_checksum(self, url):
        data = url.encode('utf-8')
        return '%08x' % (zlib.crc32(data) & 0xffffffff)

    def format_hash_frag(self, src, fragment, hash_):
        return '%s-%s' % (fragment, hash_)
