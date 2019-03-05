
"""Merging extracted files and make new 'urls.txt' ('utls-toc.txt').

Use comment structure in 'urls.txt' as directive.
"""

import logging
import os
import re

from tosixinch.process import gen
from tosixinch.util import (
    parse_tocfile, make_path, make_new_fname,
    build_new_html, lxml_open, lxml_write, slugify,
    _relink_component)

logger = logging.getLogger(__name__)

TOCDOMAIN = 'http://tosixinch.example.com'


class Node(object):
    """Represent one non-blank line in ufile."""

    def __init__(self, level, url, title, root=None):
        self.level = level
        self.url = url
        self.title = title
        if root is None:
            self.root = self
        else:
            self.root = root
        self.last = False
        self._doc = None

    @property
    def fnew(self):
        return make_new_fname(make_path(self.url))

    @property
    def doc(self):
        if self._doc is None:
            self._create_doc()
        return self._doc

    def _make_toc_html(self):
        content = '<h1>%s</h1>' % self.title
        return build_new_html(self.title, content)

    def _create_doc(self):
        if self.title:
            self._doc = self._make_toc_html()
        else:
            self._doc = lxml_open(self.fnew)

    # TODO: consider using util.merge_htmls().
    def _append_body(self):
        for t in self.doc.xpath('//body'):
            gen.decrease_heading(t)
            _relink_component(t, self.root.fnew, self.fnew)
            t.tag = 'div'
            t.set('class', 'tsi-body-merged')
            self.root.doc.body.append(t)

    def write(self):
        if self.root is not self:
            self._append_body()

        if self.last:
            lxml_write(self.root.fnew, self.root.doc)


class Nodes(object):
    """Represent ufile."""

    def __init__(self, urls, ufile):
        self.urls = urls
        self.ufile = ufile

    @property
    def toc_ufile(self):
        root, ext = os.path.splitext(self.ufile)
        return root + '-toc' + ext

    def _parse_url(self, url):
        m = re.match(r'^\s*(#+)?\s*(.+)?\s*$', url)
        if m.group(1):
            cnt = len(m.group(1))
        else:
            cnt = 0
        line = m.group(2)
        if cnt and line:
            title = line
            url = '%s/%s' % (TOCDOMAIN, slugify(title))
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
            cnt, url, title = self._parse_url(url)
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
        for node in self:
            node.write()

        urls = '\n'.join([node.url for node in self if node.root is node])
        with open(self.toc_ufile, 'w') as f:
            f.write(urls)

    def __iter__(self):
        return self.parse().__iter__()


def run(conf, ufile):
    urls = parse_tocfile(ufile)
    nodes = Nodes(urls, ufile)
    nodes.write()
