
"""Merging extracted files and make new 'rsrcs.txt' ('utls-toc.txt').

Use comment structure in 'rsrcs.txt' as directive.
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


def get_tocfile(rfile):
    if rfile:
        root, ext = os.path.splitext(os.path.basename(rfile))
        return root + '-toc' + ext


def _create_toc_url(title):
    """Create toc root url, from html title string."""
    t = location.slugify(title, allow_unicode=True)
    return '%s/%s' % (TOCDOMAIN, urllib.parse.quote(t))


class Node(object):
    """Represent one non-blank line in rfile."""

    def __init__(self, root, children, title):
        self._root = root
        self._children = children
        self.title = title

        self.doc = self._make_toc_html()
        self._loc = location.Location(root)
        self.rsrc = self._loc.rsrc
        self.root = self._loc.efile
        self.children = [location.Location(child).efile for child in children]

    def _make_toc_html(self):
        title = self.title or content.DEFAULT_TITLE
        content_ = '<h1>%s</h1>' % title
        return content.build_new_html(title=title, content=content_)

    def merge(self, table):
        if not self.children:
            return
        content.Merger(self.doc, self.root, self.children, table).merge()


class Nodes(object):
    """Represent rfile."""

    COMMENT = COMMENT_PREFIX
    DIRECTIVE_RE = re.compile(
        r'^\s*(%s+?)?\s*(.+)?\s*$' % DIRECTIVE_PREFIX)

    def __init__(self, rsrcs, rfile, tocfile):
        self.rsrcs = rsrcs
        self.rfile = rfile
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

    def _parse_line(self, rsrc):
        m = self.DIRECTIVE_RE.match(rsrc)
        if m.group(1):
            cnt = 1
        else:
            cnt = 0
        line = m.group(2)
        if cnt:
            if line:
                title = line
                rsrc = self._create_toc_url(title)
            else:
                title = None
                rsrc = None
        else:
            title = None
            rsrc = line

        return cnt, rsrc, title

    def parse(self):
        nodes = []
        level = 0
        queue = []
        # adding one extra ('# aaa') to handle the last node
        for rsrc in self.rsrcs + ['# aaa']:
            if rsrc.startswith(self.COMMENT):
                continue
            first = False
            cnt, rsrc, title = self._parse_line(rsrc)
            if cnt:
                if rsrc is None:
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

            queue.append((rsrc, title))

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

        rfile = '%s %s\n' % (self.COMMENT, os.path.abspath(self.rfile))
        rsrcs = '\n'.join([node.rsrc for node in self.nodes])
        with open(self.tocfile, 'w') as f:
            f.write(rfile)
            f.write(rsrcs)


def run(conf):
    rsrcs = conf.sites._rsrcs
    rfile = conf._rfile
    if not rfile:
        msg = ("To run '--toc', you can not use '--input'. "
            "Use either '--file', or implicit 'rsrcs.txt'.")
        raise ValueError(msg)
    tocfile = get_tocfile(rfile)

    nodes = Nodes(rsrcs=rsrcs, rfile=rfile, tocfile=tocfile)
    nodes.merge()
