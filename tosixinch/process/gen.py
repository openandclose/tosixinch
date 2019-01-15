
"""Collect general functions applicable for many sites."""

import logging
import re

from tosixinch.process.util import *

logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Default or default candidates are collected in this section.
# They should run only one argument (required 'doc').


def add_title(doc, force=False):
    """If there is no ``<h1>``, make ``<h1>`` from ``<title>`` tag text.

    >>> s = '<html><head><title>aaa</title></head><body></body></html>'
    >>> doc = fromstring(s)
    >>> add_title(doc)
    >>> tostring(doc)
    '<html><head><title>aaa</title></head><body><h1>aaa</h1></body></html>'
    """
    if doc.xpath('//h1'):
        if force is False:
            return
    if not doc.xpath('//title/text()'):
        return

    text = doc.xpath('//title/text()')[0]
    el = make_tag('h1', text)
    doc.body.insert(0, el)


def add_title_force(doc):
    """Add title even if there are ``<h1>`` s already."""
    add_title(doc, True)


# http://stackoverflow.com/questions/4085717/xslt-remove-duplicate-br-tags-from-running-text  # noqa: E501
def delete_duplicate_br(doc):
    """Continuous ``<br>`` tags to one ``<br>``, to save display space.

    >>> el = fromstring('<div>aaa<br><br><br>bbb</div>')
    >>> delete_duplicate_br(el)
    >>> tostring(el)
    '<div>aaa<br>bbb</div>'
    """
    for el in doc.xpath('//br[following-sibling::node()[not(self::text() and normalize-space(.) = "")][1][self::br]]'):  # noqa: E501
        remove_tag(el)


def youtube_video_to_thumbnail(doc):
    """Change embeded youtube video object to thumbnail image.

    | from: ``https://www.youtube.com/embed/(id)?feature=oembed``
    | to:   ``http://img.youtube.com/vi/(id)/hqdefault.jpg``
    """
    for el in doc.xpath('//iframe[contains(@src, "www.youtube.com/embed/")]'):
        m = re.match(
            r'https?://www\.youtube\.com/embed/([^/?]+)',
            el.get("src"))
        itagfmt = '<img src="http://img.youtube.com/vi/%s/hqdefault.jpg">'
        itagstr = itagfmt % m.group(1)
        itag = fromstring(itagstr)
        replace_tag(el, itag)


# ----------------------------------------------------------
# General functions


def make_ahref_visible(doc):
    r"""Make ``<a href=...>`` links to visible text.

    >>> el = fromstring('<div><a href="aaa">bbb</a></div>')
    >>> make_ahref_visible(el)
    >>> tostring(el)
    '<div><a href="aaa">bbb</a><span class="tsi-href-visible">\xa0 [[aaa]] \xa0</span></div>'
    """  # noqa: E501
    classname = 'tsi-href-visible'
    for el in doc.xpath('//a[@href]'):
        linkstr = '<span class="%s">&nbsp; [[%s]] &nbsp;</span>' % (
            classname, el.get('href'))
        link = fromstring(linkstr)
        el.addnext(link)


def decrease_heading(doc, path=None):
    """Decrease heading number except specified element (by xpath).

    That is, ``<h1>`` becomes ``<h2>``, ... ``<h5>`` becomes ``<h6>``.
    (``<h6>`` is kept as is).
    It is for prettier Table of Contents,
    TOC is usually copied from heading structure.
    A basic use case is when the document has multiple ``<h1>``.
    You don't want those to clutter TOC tree,
    want only one of them on top.

    >>> el = fromstring('<div><h1>aaa</h1><h1 class="b">bbb</h1><h2>ccc</h2></div>')  # noqa: E501
    >>> decrease_heading(el, './@class="b"')
    >>> tostring(el)
    '<div><h2>aaa</h2><h1 class="b">bbb</h1><h3>ccc</h3></div>'
    """
    for i in range(5, 0, -1):
        for el in doc.xpath('//h' + str(i)):
            el.tag = 'h' + str(i + 1)

    if not path:
        return

    for i in range(2, 7):
        for el in doc.xpath('//h' + str(i)):
            if el.xpath(path):
                el.tag = 'h1'
                return


def decrease_heading_order(doc, tag=1, order=1):
    """Decrease heading number except specified element (by order).

    The purpose is the same as `decrease_heading`,
    except you designate keep-element by heading number and order.
    So e.g. argument ``'tag=2, order=3'`` means
    third ``<h2>`` tag element in the document.

    >>> el = fromstring('<div><h1>aaa</h1><h1>bbb</h1><h2>ccc</h2></div>')
    >>> decrease_heading_order(el, 1, 2)
    >>> tostring(el)
    '<div><h2>aaa</h2><h1>bbb</h1><h3>ccc</h3></div>'
    """
    for i in range(5, 0, -1):
        for j, el in enumerate(doc.xpath('//h' + str(i))):
            if i == int(tag) and j + 1 == int(order):
                continue
            el.tag = 'h' + str(i + 1)


def split_h1_string(doc, seps=None, part='1'):
    """Remove unwanted parts from h1 string.

    Headings or titles are often composed of multiple items,
    like 'Murder! - Domestic News - The Local Paper'.
    You want just 'Murder!'.

    Selected items are whitespace stripped.

    :param seps: strings by which heading is separated.
                 if ``None``, default ``' - ', ' : ', ' | '`` is used.

    :param part: which part to select. '1' means first, or index 0.
                 special number '-1' selects last item.

    >>> el = fromstring('<h1>aaa ~ bbb</h1>')
    >>> split_h1_string(el, '~', '2')
    >>> tostring(el)
    '<h1>bbb</h1>'
    >>> el = fromstring('<h1>aaa ~ bbb</h1>')
    >>> split_h1_string(el, '~', '-1')
    >>> tostring(el)
    '<h1>bbb</h1>'
    """
    el = doc.xpath('//h1')[0]
    if seps is None:
        seps = [' - ', ' : ', ' | ']
    if isinstance(seps, str):
        seps = [seps]
    if part == '-1':
        part = '0'
    for sep in seps:
        if sep in el.text:
            el.text = el.text.split(sep)[int(part) - 1].strip()
            break


def replace_h1_string(el, pat, repl=''):
    """Change ``<h1>`` string by regular expression, ``pat`` to ``repl``.

    >>> el = fromstring('<h1>A boring article</h1>')
    >>> replace_h1_string(el, 'A boring', 'An exciting')
    >>> tostring(el)
    '<h1>An exciting article</h1>'
    """
    for h in el.xpath('//h1'):
        h.text = re.sub(pat, repl, h.text)


def code_to_pre_code(doc):
    r"""Wrap ``<code>`` with ``<pre>``, when text includes newlines.

    Sample css adds thin border style to ``<pre>``, and not to ``<code>``,
    which is to make multiline code marked out a little,
    and inline code not looking cluttered,
    in small black and white ebooks.
    But some sites use ``<code>`` indefinitely, also for multiline codes.
    in these cases,
    adding ``<pre>`` rather unconditionally is one of the solution.

    As an arbirtary precaution,
    if parent or grandparent element tag is ``<pre>``,
    adding another ``<pre>`` is skipped.

    >>> el = fromstring('<code>aaabbb</code>')
    >>> parent = el.getparent()
    >>> code_to_pre_code(el)
    >>> tostring(parent[0])
    '<code>aaabbb</code>'
    >>> el = fromstring(r'<code>aaa\nbbb</code>')
    >>> parent = el.getparent()
    >>> code_to_pre_code(el)
    >>> tostring(parent[0])
    '<pre><code>aaa\\nbbb</code></pre>'
    """
    for el in doc.xpath('//code'):
        if r'\n' in el.text_content():
            if check_parents_tag(el, 'pre') is not None:
                continue
            wrap_tag(el, 'pre')


def add_hr(doc, path):
    """Add ``<hr>`` tag before some xpath element (``'path'``) in the document.

    >>> el = fromstring('<div><p>aaa</p><p>bbb</p></div>')
    >>> path = '(//p)[2]'
    >>> add_hr(el, path)
    >>> tostring(el)
    '<div><p>aaa</p><hr><p>bbb</p></div>'
    """
    for el in doc.xpath(path):
        tag = make_tag('hr', '')
        insert_tag(el, tag)


def add_description(doc):
    """Add description from ``<meta>``."""
    description = get_metadata(doc)['description']
    desc = make_tag('p', '[ %s ]' % description)
    doc.body.insert(0, desc)


def add_style(doc, path, style):
    """Add inline style strings ('style') to each xpath element ('path').

    >>> el = fromstring('<div><p>aaa</p></div>')
    >>> add_style(el, '//p', 'text-decoration:line-through;')
    >>> tostring(el)
    '<div><p class="tsi-keep-style" style="text-decoration:line-through;">aaa</p></div>'
    """  # noqa: E501
    for el in doc.xpath(path):
        el.classes |= (KEEP_STYLE,)
        el.set('style', style)


def change_tagname(doc, path, tag='div'):
    """Change just the tagname while keeping anything inside.

    >>> doc = fromstring('<div><p>aaa</p>bbb</div>')
    >>> change_tagname(doc, '//div', 'h3')
    >>> tostring(doc)
    '<h3><p>aaa</p>bbb</h3>'
    """
    for el in doc.xpath(path):
        el.tag = tag
