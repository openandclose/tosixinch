
"""Merging extracted files and make new 'urls.txt' ('utls-toc.txt').

Use comment structure in 'urls.txt' as directive.
"""

import logging
import os
import re
import urllib.parse

from tosixinch import content
from tosixinch import location

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

    def __init__(self, root, children, title):
        self._root = root
        self._children = children
        self.title = title

        self.doc = self._make_toc_html()
        self._loc = location.Location(root)
        self.url = self._loc.url
        self.root = self._loc.fnew
        self.children = [location.Location(child).fnew for child in children]

    def _make_toc_html(self):
        title = self.title or content.DEFAULT_TITLE
        content_ = '<h1>%s</h1>' % title
        return content.build_new_html(title=title, content=content_)

    def merge(self, table):
        if not self.children:
            return
        content.Merger(self.doc, self.root, self.children, table).merge()


class Nodes(object):
    """Represent ufile."""

    COMMENT = COMMENT_PREFIX
    DIRECTIVE_RE = re.compile(
        r'^\s*(%s+?)?\s*(.+)?\s*$' % DIRECTIVE_PREFIX)

    def __init__(self, urls, ufile, tocfile):
        self.urls = urls
        self.ufile = ufile
        self.tocfile = tocfile
        self.cache = set()  # title cache
        self.nodes = self.parse()

    def _create_toc_url(self, title):
        num = 0
        while True:
            new = title if num == 0 else '%s-%d' % (title, num)
            if new in self.cache:
                num += 1
            else:
                self.cache.add(new)
                break

        return _create_toc_url(new)

    def _parse_line(self, url):
        m = self.DIRECTIVE_RE.match(url)
        if m.group(1):
            cnt = 1
        else:
            cnt = 0
        line = m.group(2)
        if cnt:
            if line:
                title = line
                url = self._create_toc_url(title)
            else:
                title = None
                url = None
        else:
            title = None
            url = line

        return cnt, url, title

    def parse(self):
        nodes = []
        level = 0
        queue = []
        # adding one extra ('# aaa') to handle the last node
        for url in self.urls + ['# aaa']:
            if url.startswith(self.COMMENT):
                continue
            first = False
            cnt, url, title = self._parse_line(url)
            if cnt:
                if url is None:
                    level = 0
                    continue

                first = True
                level = cnt
            else:
                if level == 0:
                    first = True

            if first and queue:
                root, title_ = queue[0]
                children = [q[0] for q in queue[1:]]
                nodes.append(Node(root, children, title_))
                queue = []

            queue.append((url, title))

        return nodes

    def create_table(self):
        t = []
        for node in self.nodes:
            t.append((node.root, node.children))
        return tuple(t)

    def merge(self):
        table = self.create_table()
        for node in self.nodes:
            node.merge(table)

        ufile = '%s %s\n' % (self.COMMENT, os.path.abspath(self.ufile))
        urls = '\n'.join([node.url for node in self.nodes])
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
    nodes.merge()
