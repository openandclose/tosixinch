
"""Collect functions including site specific logic.

The purpose is to not clutter `gen` module.
The boundary may not be clear-cut.
"""

import logging

from tosixinch.process.util import *

logger = logging.getLogger(__name__)


def convert_permalink_sign(doc, repl=''):
    r"""Change permalink sign to some text (``'repl'``).

    Most python documents use this (``U+00B6`` or ``pilcrow sign`` or '¶').
    On pdf, these marks are always visible, rather noisy.

    cf. in sample css, 'headerlink' is already made invisible ('display:none;').

    >>> el = fromstring(r'<div><h1>tosixinch<a class="headerlink">¶</a></h1></div>')  # noqa: E501
    >>> convert_permalink_sign(el, '\u2026')
    >>> tostring(el)
    '<div><h1>tosixinch<a class="headerlink">…</a></h1></div>'
    """
    for el in doc.xpath('//a[@class="headerlink"]'):
        if el.text == '\u00B6':
            el.text = repl


def hackernews_indent(doc):
    """Narrow default indent widths, they are too wide for e-readers."""
    for t in doc.xpath('//*[@width]'):
        if not t.xpath('../img[@src="s.gif"]'):
            t.attrib.pop('width')

    for d in doc.xpath('//td[@class="ind"]'):
        width = d.xpath('./img/@width')[0]
        dd = d.getparent()
        comhead = dd.xpath('.//span[@class="comhead"]')[0]
        newcomhead = make_tag('strong')
        newcomhead.append(comhead)
        comhead = newcomhead
        comment = dd.xpath('.//div[@class="comment"]')[0]
        # changing image width (px) to padding-left (px),
        # dividing number arbitrarily.
        block = fromstring(
            # '<div class = "%s" style="padding-left:%dpx;"></div>' % (
            '<div class = "%s" style="margin-bottom:1em;padding-left:%dpx;"></div>' % (  # noqa: E501
                KEEP_STYLE, int(int(width) / 4)))
        block.append(comhead)
        block.append(comment)
        ddd = dd.getparent()
        ddd.replace(dd, block)

    # different for /item? and /threads? urls
    if doc.xpath('./body/table[1]'):
        table = doc.xpath('./body/table[1]')[0]
        wrap_tag(table, 'p')


def reddit_indent(doc):
    """Render reddit.com's comment indent styles.

    They are in the site's external css.
    So we have to insert inline css made from it.
    """
    for el in doc.xpath('//div[contains(@class, " comment ")]'):
        el.attrib["style"] = 'margin-left: 8px;'
        el.classes |= (KEEP_STYLE,)


def github_self_ancohr(doc):
    """Discard self anchors in <h3>.

    We stripped referents, and weasyprint warns it.
    """
    for el in doc.xpath('(//h1|//h2|//h3|//h4)/a'):
        if 'anchor' in el.classes:
            # When setting 'href="#", weasyprint warns
            # 'WARNING: No anchor # for internal URI reference at line None'
            el.set('href', '')


def github_issues_comment_header(doc):
    """Change comment header blocks from <h3> to <div>.

    <h3> is too big here, clutters TOC.

    Also discard self anchors in date part of headers
    e.g. 'href="#issuecomment-223857939"'.
    We stripped referents, and weasyprint warns it.
    """
    for el in doc.xpath('//h3'):
        if 'timeline-comment-header-text' in el.classes:
            el.tag = 'div'

            for element in el.xpath('.//a'):
                if 'timestamp' in element.classes:
                    element.set('href', '')
