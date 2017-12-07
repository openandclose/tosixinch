
"""Merging extracted files and make new 'urls.txt' ('utls-toc.txt').

Use comment structure in 'urls.txt' as directive.
"""

import logging
import os

from tosixinch.process import gen
from tosixinch.util import (
    parse_tocfile, make_path, make_new_fname,
    build_new_html, lxml_open, lxml_write, slugify,
    _relink_component)

logger = logging.getLogger(__name__)

TOCDOMAIN = 'http://tosixinch.example.com'


def _make_toc_html(title):
    content = '<h1>%s</h1>' % title
    doc = build_new_html(title, content)
    return doc


def _make_toc_file(fname):
    root, ext = os.path.splitext(fname)
    return root + '-toc' + ext


# TODO: consider using util.merge_htmls().
# TODO: divide parsing and html building.
def run(conf, fname):
    urls = parse_tocfile(fname)
    newurls = []
    inside = False
    prev = None
    for url in urls:
        if not url.startswith('#'):
            if not inside:
                newurls.append(url)
            else:
                fnew = make_new_fname(make_path(url))
                tags = lxml_open(fnew).xpath('//body')
                for t in tags:
                    gen.decrease_heading(t)
                    _relink_component(t, prev, fnew)
                    t.tag = 'div'
                    t.set('class', 'tsi-body-merged')
                    doc.body.append(t)  # noqa: F821 (undefined name 'doc')
        else:
            if url.strip() == '#':
                lxml_write(prev, doc)  # noqa: F821
                inside = False
                continue
            title = url.split('#')[-1].strip()
            newurl = '%s/%s' % (TOCDOMAIN, slugify(title))
            newurls.append(newurl)
            fnew = make_new_fname(make_path(newurl))
            if not inside:
                inside = True
            else:
                lxml_write(prev, doc)  # noqa: F821
            prev = fnew
            doc = _make_toc_html(title)
    if inside:
        lxml_write(prev, doc)

    with open(_make_toc_file(fname), 'w') as f:
        f.write('\n'.join(newurls))
