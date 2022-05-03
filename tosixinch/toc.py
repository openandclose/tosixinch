
"""Merging extracted files and make new 'urls.txt' ('utls-toc.txt').

Use comment structure in 'urls.txt' as directive.
"""

import logging
import os
import re
import urllib.parse

from tosixinch import location
from tosixinch import lxml_html
from tosixinch.content import (
    build_new_html, _relink_component, _relink)

import tosixinch.process.sample as process_sample

logger = logging.getLogger(__name__)

DIRECTIVE_PREFIX = '#'
COMMENT_PREFIX = ';'

TOCDOMAIN = 'http://tosixinch.example.com'


def get_tocfile(ufile):
    if ufile:
        root, ext = os.path.splitext(os.path.basename(ufile))
        return root + '-toc' + ext


def _create_toc_url(title):
    """Create toc root url, from html title string."""
    t = location.slugify(title, allow_unicode=True)
    return '%s/%s' % (TOCDOMAIN, urllib.parse.quote(t))


class Node(object):
    """Represent one non-blank line in ufile."""

    def __init__(self, level, url, title, root=None):
        self._loc = location.Location(url)

        self.url = self._loc.url
        self.fnew = self._loc.fnew
        self.slash_fnew = self._loc.slash_fnew

        self.level = level
        self.title = title
        self.root = root or self

        self.last = False
        self._doc = None
        self.cssfiles = []

    @property
    def doc(self):
        if self._doc is None:
            self._create_doc()
        return self._doc

    def _make_toc_html(self):
        content = '<h1>%s</h1>' % self.title
        return build_new_html(title=self.title, content=content)

    def _create_doc(self):
        if self.title:
            self._doc = self._make_toc_html()
        else:
            self._doc = lxml_html.read(self.fnew)

    def _append_css(self):
        for el in self.doc.xpath('//head/link[@class="tsi-css"]'):
            href = el.get('href') or ''
            if href:
                if href in self.root.cssfiles:
                    continue
                href = _relink(href, self.slash_fnew, self.root.slash_fnew)
                el.set('href', href)
                self.root.doc.head.append(el)
                self.root.cssfiles.append(href)

    # TODO: consider using content.merge_htmls().
    def _append_body(self):
        for t in self.doc.xpath('//body'):
            process_sample.lower_heading(t)
            _relink_component(t, self.root.fnew, self.fnew)
            t.tag = 'div'
            t.set('class', 'tsi-body-merged')
            self.root.doc.body.append(t)

    def write(self):
        if self.root is not self:
            self._append_css()
            self._append_body()

        if self.last:
            lxml_html.write(self.root.fnew, doc=self.root.doc)


class Nodes(object):
    """Represent ufile."""

    _COMMENT = COMMENT_PREFIX
    _DIRECTIVE_RE = re.compile(
        r'^\s*(%s+?)?\s*(.+)?\s*$' % DIRECTIVE_PREFIX)

    def __init__(self, urls, ufile, tocfile):
        self.urls = urls
        self.ufile = ufile
        self.tocfile = tocfile
        self.nodes = self.parse()

    def _parse_toc_url(self, url):
        m = self._DIRECTIVE_RE.match(url)
        if m.group(1):
            cnt = len(m.group(1))
        else:
            cnt = 0
        line = m.group(2)
        if cnt and line:
            title = line
            url = _create_toc_url(title)
        elif cnt and not line:
            title = None
            url = None
        else:
            title = None
            url = line

        return cnt, url, title

    def parse(self):
        nodes = []
        level = 0
        node = None
        root = None
        for url in self.urls:
            if url.startswith(self._COMMENT):
                continue
            cnt, url, title = self._parse_toc_url(url)
            if cnt:
                if url is None:
                    level -= 1
                    continue
                if cnt == 1:
                    if node:
                        node.last = True
                level = cnt
            else:
                if level == 0:
                    if node:
                        node.last = True

            if not node or node.last:
                root = node = Node(level, url, title, None)
            else:
                node = Node(level, url, title, root)
            nodes.append(node)

        node.last = True
        return nodes

    def write(self):
        for node in self.nodes:
            node.write()

        ufile = '%s %s\n' % (COMMENT_PREFIX, os.path.abspath(self.ufile))
        urls = '\n'.join([node.url for node in self.nodes
            if node.root is node])
        with open(self.tocfile, 'w') as f:
            f.write(ufile)
            f.write(urls)


def run(conf):
    urls = conf.sites._urls
    ufile = conf._ufile
    if not ufile:
        msg = ("To run '--toc', you can not use '--input'. "
            "Use either '--file', or implicit 'urls.txt'.")
        raise ValueError(msg)
    tocfile = get_tocfile(ufile)

    nodes = Nodes(urls=urls, ufile=ufile, tocfile=tocfile)
    nodes.write()
