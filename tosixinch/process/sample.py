
"""Sample functions to use in ``process`` option.

Divided in three parts:

    * Helper Functions
    * General Functions (applicable for many websites)
    * Site Specific Functions
"""

from copy import deepcopy
import logging
import re

from tosixinch import lxml_html
from tosixinch.clean import KEEP_STYLE  # noqa: F401

logger = logging.getLogger(__name__)

# lxml.html.defs.empty_tags (only for html4)
# http://xahlee.info/js/html5_non-closing_tag.html
self_closing_tags = (
    'area', 'base', 'basefont', 'br', 'col', 'command', 'embed', 'frame',
    'hr', 'img', 'input', 'isindex', 'keygen', 'link', 'meta', 'param',
    'source', 'track', 'wbr',
)

fromstring = lambda el: lxml_html.fromstring(el)
tostring = lambda el: lxml_html.tostring(el, encoding='unicode')


# lxml.html module's parsing functions are
# rather complex wrappers of lxml.etree ones,
# mainly designed to parse broken htmls.
# They are useful, but in testing situations, a little confusing.
# I need a memorandum somewhere.
def _fromstring_examples():
    """lxml.html module's fromstring examples.

    >>> el = fromstring('<p>aaa</p>')
    >>> tostring(el)
    '<p>aaa</p>'
    >>> tostring(el.getparent())
    '<body><p>aaa</p></body>'
    >>> el = fromstring('<p>aaa</p><p>bbb</p>')
    >>> tostring(el)
    '<div><p>aaa</p><p>bbb</p></div>'
    >>> tostring(el.getparent())
    '<html><div><p>aaa</p><p>bbb</p></div></html>'
    >>> el = fromstring('<code>aaa</code><code>bbb</code>')
    >>> tostring(el)
    '<span><code>aaa</code><code>bbb</code></span>'
    >>> el = fromstring('aaa<div>bbb</div>')
    >>> tostring(el)
    '<div><p>aaa</p><div>bbb</div></div>'
    """


# ----------------------------------------------------------
# Helper Functions


def make_tag(tag='div', text=''):
    """Make element (``HtmlElement``) from tag and string.

    >>> el = make_tag('p', 'aaa')
    >>> tostring(el)
    '<p>aaa</p>'
    """
    if tag in self_closing_tags:
        return fromstring('<%s %s />' % (tag, text))
    return fromstring('<%s>%s</%s>' % (tag, text, tag))


def wrap_tag(el, tag='div'):
    """Wrap element in a tag.

    >>> el = fromstring('<p>aaa</p>')
    >>> parent = el.getparent()
    >>> wrap_tag(el, 'div')
    >>> tostring(parent[0])
    '<div><p>aaa</p></div>'
    """
    parent = el.getparent()
    assert parent is not None
    tag = make_tag(tag, '')
    tag.append(deepcopy(el))
    replace_tag(el, tag)


def remove_tag(el):
    """Remove element (and subelements) from parent element.

    >>> doc = fromstring('<div><p>aaa</p><p>bbb</p></div>')
    >>> el = doc.xpath('//p')[1]
    >>> remove_tag(el)
    >>> tostring(doc)
    '<div><p>aaa</p></div>'
    """
    el.drop_tree()


def replace_tag(el, replace):
    """Replace element to another element.

    >>> doc = fromstring('<div><p>aaa</p></div>')
    >>> el = doc.xpath('//p')[0]
    >>> repl = make_tag('h3', 'bbb')
    >>> replace_tag(el, repl)
    >>> tostring(doc)
    '<div><h3>bbb</h3></div>'
    """
    parent = el.getparent()
    assert parent is not None
    parent.replace(el, replace)


def insert_tag(el, add, before=True):
    """Insert element ('add') before or after element ('el').

    See `add_hr` for doctest example.
    """
    parent = el.getparent()
    assert parent is not None
    num = parent.index(el)
    if not before:
        num = num + 1
    parent.insert(num, add)


def check_parent_tag(el, tag='div', generation=2):
    """Check existance of tag in an element's parent elements.

    And returns it if found.

    >>> doc = fromstring('<table><tr><td>aaa</td></tr></table>')
    >>> el = doc.xpath('//td')[0]
    >>> el = check_parent_tag(el, 'table')
    >>> el.tag
    'table'
    """
    for i in range(int(generation)):
        el = el.getparent()
        if el is None:
            return
        if el.tag == tag:
            return el


# ``HtmlElement.text_content()``, or ```etree.tostring(el, method="text")``
# seems to do the same thing.
def get_element_text(el, path='.'):
    """Return all texts in an element or elements.

    :param el: main elemant to search
    :param path: xpath string for the element(s) you want

    >>> el = fromstring('<h2>aaa<div>bbb</div></h2>')
    >>> get_element_text(el, '//h2')
    'aaabbb'
    >>> el = fromstring('<div>no<h2>aaa<div>bbb</div><div>ccc<p>ddd</p></div></h2><h2>xxx</h2></div>')  # noqa: E501
    >>> get_element_text(el, '//h2')
    'aaabbbcccdddxxx'
    """
    elements = el.xpath(path)
    if len(elements) == 1:
        return el.xpath('string(%s)' % path)

    text = []
    for element in elements:
        text.append(get_element_text(element, '.'))
    return ''.join(text)


def get_metadata(el):
    """Get basic metadata from ``<meta name=... content=...>``."""
    # Borrowing codes from:
    # https://github.com/Kozea/WeasyPrint/blob/master/weasyprint/html.py
    root = el.getroottree()

    authors = []
    description = None
    generator = None
    keywords = []
    created = None
    modified = None
    for element in root.iter('meta'):
        name = element.get('name', '')
        content = element.get('content', '')
        if name == 'author':
            authors.append(content)
        elif name == 'description' and description is None:
            description = content
        elif name == 'generator' and generator is None:
            generator = content
        elif name == 'keywords':
            for keyword in content.split(','):
                keyword = keyword.strip()
                if keyword not in keywords:
                    keywords.append(keyword)
        elif name == 'dcterms.created' and created is None:
            created = content
        elif name == 'dcterms.modified' and modified is None:
            modified = content

    return dict(authors=authors, description=description,
        generator=generator, keywords=keywords,
        created=created, modified=modified)


# ----------------------------------------------------------
# General Functions


def add_h1(doc, force=False):
    """If there is no ``<h1>``, make ``<h1>`` from ``<title>`` tag text.

    >>> s = '<html><head><title>aaa</title></head><body></body></html>'
    >>> doc = fromstring(s)
    >>> add_h1(doc)
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


def add_h1_force(doc):
    """Add title even if there are ``<h1>`` s already."""
    add_h1(doc, True)


def delete_duplicate_br(doc, maxnum=2):
    """Continuous ``<br>`` tags to maximum ``<br>``, to save display space.

    >>> el = fromstring('<div>aaa<br><br>  <br><br/><br>bbb<br><br></div>')
    >>> delete_duplicate_br(el)
    >>> tostring(el)
    '<div>aaa<br><br>  bbb<br><br></div>'
    """
    num = 0
    _remove = []

    for el in doc.iter():
        if el.tag == 'br':
            num += 1
            if num > maxnum:
                _remove.append(el)
            if el.tail is None or el.tail.strip() == '':
                num = min(num, maxnum)
            else:
                num = 0
        else:
            num = 0

    for el in list(_remove):
        el.drop_tag()


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


def show_href(doc):
    r"""Make ``<a href=...>`` links to visible text.

    >>> el = fromstring('<div><a href="aaa">bbb</a></div>')
    >>> show_href(el)
    >>> tostring(el)
    '<div><a href="aaa">bbb</a><span class="tsi-href-visible">\xa0 [[aaa]] \xa0</span></div>'
    """  # noqa: E501
    classname = 'tsi-href-visible'
    for el in doc.xpath('//a[@href]'):
        linkstr = '<span class="%s">&nbsp; [[%s]] &nbsp;</span>' % (
            classname, el.get('href'))
        link = fromstring(linkstr)
        el.addnext(link)


def lower_heading(doc, path=None):
    """Decrease heading number except specified element (by xpath).

    That is, ``<h1>`` becomes ``<h2>``, ... ``<h5>`` becomes ``<h6>``.
    (``<h6>`` is kept as is).
    It is for prettier Table of Contents,
    TOC is usually copied from heading structure.
    A basic use case is when the document has multiple ``<h1>``.
    You don't want those to clutter TOC tree,
    want only one of them on top.

    >>> el = fromstring('<div><h1>aaa</h1><h1 class="b">bbb</h1><h2>ccc</h2></div>')  # noqa: E501
    >>> lower_heading(el, './@class="b"')
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


def lower_heading_from_order(doc, tag=1, order=1):
    """Decrease heading number except specified element (by order).

    The purpose is the same as `lower_heading`,
    except you specify keep-element by heading number and order.
    So e.g. argument ``'tag=2, order=3'`` means
    third ``<h2>`` tag element in the document.

    >>> el = fromstring('<div><h1>aaa</h1><h1>bbb</h1><h2>ccc</h2></div>')
    >>> lower_heading_from_order(el, 1, 2)
    >>> tostring(el)
    '<div><h2>aaa</h2><h1>bbb</h1><h3>ccc</h3></div>'
    """
    for i in range(5, 0, -1):
        for j, el in enumerate(doc.xpath('//h' + str(i))):
            if i == int(tag) and j + 1 == int(order):
                continue
            el.tag = 'h' + str(i + 1)


def split_h1(doc, seps=None, part='1'):
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
    >>> split_h1(el, '~', '2')
    >>> tostring(el)
    '<h1>bbb</h1>'
    >>> el = fromstring('<h1>aaa ~ bbb</h1>')
    >>> split_h1(el, '~', '-1')
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


def replace_h1(el, pat, repl=''):
    """Change ``<h1>`` string by regular expression, ``pat`` to ``repl``.

    >>> el = fromstring('<h1>A boring article</h1>')
    >>> replace_h1(el, 'A boring', 'An exciting')
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
            if check_parent_tag(el, 'pre') is not None:
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


def replace_tags(doc, path, tag='div'):
    """Change just the tagname while keeping anything inside.

    >>> doc = fromstring('<div><p>aaa</p>bbb</div>')
    >>> replace_tags(doc, '//div', 'h3')
    >>> tostring(doc)
    '<h3><p>aaa</p>bbb</h3>'
    """
    for el in doc.xpath(path):
        el.tag = tag


def add_noscript_image(doc):
    """Move element inside <noscript> to outside.

    >>> doc = fromstring('<h3><noscript><div><img src="a.jpg"></div></noscript></h3>')  # noqa: E501
    >>> add_noscript_image(doc)
    >>> tostring(doc)
    '<h3><noscript><div></div></noscript><img src="a.jpg"></h3>'
    """
    for el in doc.xpath('//noscript'):
        for element in el.iter(tag='img'):
            if 'src' in element.attrib:
                el.addnext(element)


# ----------------------------------------------------------
# Site Specific Functions


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
        width = d.xpath('./img/@width')
        width = width[0] if width else '0'
        dd = d.getparent()
        comhead = dd.xpath('.//span[@class="comhead"]')[0]
        comhead.classes.add(KEEP_STYLE)
        comhead.set('style', 'font-weight:bold;')
        comment = dd.xpath('.//div[@class="comment"]')
        # sometimes comment is '[]' (javascript folded)
        if comment != []:
            comment = comment[0]
        # changing image width (px) to padding-left (px),
        # dividing number arbitrarily.
        block = fromstring(
            # '<div class="%s" style="padding-left:%dpx;"></div>' % (
            '<div class="%s" style="margin-bottom:1em;padding-left:%dpx;"></div>' % (  # noqa: E501
                KEEP_STYLE, int(int(width) / 4)))
        block.append(comhead)
        if comment != []:
            block.append(comment)
        ddd = dd.getparent()
        ddd.replace(dd, block)

    # /item? and /threads? urls are different
    if doc.xpath('./body/table[1]'):
        table = doc.xpath('./body/table[1]')[0]
        wrap_tag(table, 'p')

    # Add sitename hint to h1
    h1 = doc.xpath('./body/h1')[0]
    h1.text = 'hn - ' + h1.text.split(' | ')[0]


def reddit_indent(doc):
    """Render reddit.com's comment indent styles.

    They are in the site's external css.
    So we have to insert inline css made from it.
    """
    for el in doc.xpath('//div[@class=="comment"]'):
        el.set('style', 'margin-left:8px;')
        el.classes.add(KEEP_STYLE)
        path = './/p[@class="tagline"]/a[@class=="author"]'
        for e in el.xpath(path):
            e.set('style', 'font-weight:bold;')
            e.classes.add(KEEP_STYLE)

    # Add sitename to h1
    h1 = doc.xpath('./body/h1')[0]
    h1.text = 'reddit - ' + h1.text


def github_self_anchor(doc):
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

    Also delete the repetetive sentence 'This comment...' (display: none).
    """
    for el in doc.xpath('//h3'):
        if 'timeline-comment-header-text' in el.classes:
            el.tag = 'div'

            for element in el.xpath('.//a'):
                if 'timestamp' in element.classes:
                    element.set('href', '')

            if 'This comment has been minimized.' in el.text:
                if 'text-gray' in el.classes:
                    el.text = ''
