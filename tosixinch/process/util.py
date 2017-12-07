
"""Utility functions to use in other modules in ``process`` directory.

Supposed to be imported by ``from tosixinch.process.util import *``.

---

Naming Conventions:

doc: relatively large element, mostly, but not necessarily, complete html.

el: selected element(s), mostly from 'doc.xpath()'.

element or elements: more smaller element(s),
if you need to select parts in 'el'.

tag: newly created, relatively simple element, to edit 'el'.

The aim is to keep the best name 'el' for main target or main concern.
"""


from copy import deepcopy
import logging

import lxml.html

from tosixinch.util import KEEP_STYLE  # noqa: F401

_logger = logging.getLogger(__name__)

# lxml.html.defs.empty_tags (only for html4)
# http://xahlee.info/js/html5_non-closing_tag.html
self_closing_tags = (
    'area', 'base', 'basefont', 'br', 'col', 'command', 'embed', 'frame',
    'hr', 'img', 'input', 'isindex', 'keygen', 'link', 'meta', 'param',
    'source', 'track', 'wbr',
)

# These short forms are used only in ``process`` package.
# 'tostring' is perhaps only in doctests.
# Other modules use longer 'lxml.html...' form.
fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


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

    See `process.gen.add_hr` for doctest example.
    """
    parent = el.getparent()
    assert parent is not None
    num = parent.index(el)
    if not before:
        num = num + 1
    parent.insert(num, add)


def check_parents_tag(el, tag='div', generation=2):
    """Check existance of tag in an element's parent elements.

    And returns it if found.

    >>> doc = fromstring('<table><tr><td>aaa</td></tr></table>')
    >>> el = doc.xpath('//td')[0]
    >>> el = check_parents_tag(el, 'table')
    >>> el.tag
    'table'
    """
    parents = []
    for i in range(int(generation)):
        el = el.getparent()
        parents.append(el)
    for parent in parents:
        if parent is not None and parent.tag == tag:
            return parent


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
