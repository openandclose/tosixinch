
"""Merging extracted files and make new 'urls.txt' ('utls-toc.txt').

Use comment structure in 'urls.txt' as directive.
"""

import logging
import re
import sys

from tosixinch import location
from tosixinch import lxml_html
from tosixinch.content import (
    build_new_html, _relink_component, _relink)

import tosixinch.process.sample as process_sample

logger = logging.getLogger(__name__)

DIRECTIVE_PREFIX = '#'

TOCDOMAIN = 'http://tosixinch.example.com'


class Node(location.Location):
    """Represent one non-blank line in ufile."""

    def __init__(self, level, url, title, root=None, platform=sys.platform):
        super().__init__(url, platform=platform)
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


class Nodes(location.Locations):
    """Represent ufile."""

    def __init__(self, urls, ufile):
        if not ufile:
            msg = ("To run '--toc', you can not use '--input'. "
                "Use either '--file', or implicit 'urls.txt'.")
            raise ValueError(msg)

        super().__init__(urls, ufile)

        # (';',)
        self._comment = tuple(set(self._comment) - set(DIRECTIVE_PREFIX))
        self._directive_re = re.compile(
            r'^\s*(%s+)?\s*(.+)?\s*$' % DIRECTIVE_PREFIX)

    def _parse_toc_url(self, url):
        m = self._directive_re.match(url)
        if m.group(1):
            cnt = len(m.group(1))
        else:
            cnt = 0
        line = m.group(2)
        if cnt and line:
            title = line
            url = '%s/%s' % (TOCDOMAIN, location.slugify(title))
        elif cnt and not line:
            title = None
            url = None
        else:
            title = None
            url = line

        return cnt, url, title

    def _iterate(self):
        nodes = []
        level = 0
        node = None
        root = None
        for url in self.urls:
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

    def __iter__(self):
        return self._iterate().__iter__()

    def write(self):
        for node in self:
            node.write()

        urls = '\n'.join([node.url for node in self if node.root is node])
        with open(self.get_tocfile(), 'w') as f:
            f.write(urls)


def run(conf):
    ufile = conf._ufile
    nodes = Nodes(urls=None, ufile=ufile)
    nodes.write()
