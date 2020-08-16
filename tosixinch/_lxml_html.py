
"""Add a few utilities to lxml.html."""

import logging
import re
import sys

from tosixinch import system

import lxml.etree as etree
import lxml.html
import lxml.html.clean as clean  # noqa: F401 (imported but unused)

tostring = lxml.html.tostring

logger = logging.getLogger(__name__)


class XPathEvalError(etree.XPathEvalError):
    """Wrap the Error."""


def _build_xpath_class(path):
    """Change a custom xpath syntax (double equals) to normal xpath.

    from: '//div[@class=="main"]' (note '==')
    to: '//div[contains(concat(" ", normalize-space(@class), " "), " main ")]'
    """
    pat = re.compile(
        r'([a-zA-Z]+|[hH][1-6]|\*)\[@class==([\'"])([_a-zA-Z0-9-]+)\2\]')
    repl = r'\1[contains(concat(" ", normalize-space(@class), " "), " \3 ")]'
    return pat.sub(repl, path)


def _wrap_xpath_error(path, e):
    n = e.column
    s = ' ' * (n - 1) + '^'
    s = path + '\n' + s
    fmt = ("xpath error occured probably at column %d "
           "(at the mark '^'):\n\n%s\n")
    return fmt % (n, s)


class HtmlElement(lxml.html.HtmlElement):
    """Add a few utilities to lxml.html.HtmlElement."""

    def xpath(self, _path, **kwargs):
        path = _build_xpath_class(_path)
        try:
            return super().xpath(path, **kwargs)
        except etree.XPathEvalError as _e:
            e = _e.error_log.last_error
            msg = _wrap_xpath_error(path, e)
            raise XPathEvalError(msg) from None

    @property
    def head(self):
        """Wrap the method not to raise Error when there is no <head>."""
        XHTML_NAMESPACE = lxml.html.XHTML_NAMESPACE
        elms = self.xpath('//head|//x:head', namespaces={'x': XHTML_NAMESPACE})
        if elms:
            return elms[0]

    @property
    def body(self):
        """Wrap the method not to raise Error when there is no <body>."""
        XHTML_NAMESPACE = lxml.html.XHTML_NAMESPACE
        elms = self.xpath('//body|//x:body', namespaces={'x': XHTML_NAMESPACE})
        if elms:
            return elms[0]


# cf. lxml.html.HtmlElement dependencies
# HtmlMixin(object)
# -> HtmlElement(etree.ElementBase, HtmlMixin)
#    -> HtmlElementClassLookup(etree.CustomElementClassLookup)
#       -> HTMLParser(etree.HTMLParser)

class HtmlElementClassLookup(etree.CustomElementClassLookup):
    """Wrap the class to use this module's HtmlElement."""

    def lookup(self, node_type, document, namespace, name):
        if node_type == 'element':
            return HtmlElement
        elif node_type == 'comment':
            return lxml.html.HtmlComment
        elif node_type == 'PI':
            return lxml.html.HtmlProcessingInstruction
        elif node_type == 'entity':
            return lxml.html.HtmlEntity


class HTMLParser(etree.HTMLParser):
    """Wrap the class to use this module's HtmlElementClassLookup."""

    def __init__(self, **kwargs):
        if 'encoding' in kwargs:
            super().__init__(**kwargs)
        else:
            super().__init__(encoding='utf-8', **kwargs)
        self.set_element_class_lookup(HtmlElementClassLookup())


# Wrap the functions to use this module's HTMLParser.
# Use keyword arguments except for first 'html' argument.

def document_fromstring(html, **kw):
    return lxml.html.document_fromstring(html, parser=HTMLParser(), **kw)


def fragments_fromstring(html, **kw):
    return lxml.html.fragments_fromstring(html, parser=HTMLParser(), **kw)


def fragment_fromstring(html, **kw):
    return lxml.html.fragment_fromstring(html, parser=HTMLParser(), **kw)


def fromstring(html, **kw):
    return lxml.html.fromstring(html, parser=HTMLParser(), **kw)


# read and write utility functions

class HtmlReader(system.Reader):
    """html reader object.

    From fname or text, return document object (lxml_html.HtmlElement).
    """

    def _parse(self):
        self.doc = document_fromstring(self.text.encode('utf-8'))

    def read(self):
        self._prepare()
        self._parse()
        return self.doc


class HtmlWriter(system.Writer):
    """html writer object.

    From document object, write serialized text to fname.
    """

    def __init__(self, fname, doc=None, text=None, platform=sys.platform):
        super().__init__(fname, text, platform)
        self.doc = doc

    def _serialize(self):
        if self.text:
            return
        tree = self.doc.getroottree()
        self.text = tostring(tree, encoding='unicode')

    def _prepare(self):
        self._serialize()
        system.make_directories(self.fname)


def read_text(fname, text=None, codings=None,
        errors='strict', platform=sys.platform):
    """Return raw html text. Just exposing system.Reader.read()."""
    reader = HtmlReader(fname, text, codings, errors, platform)
    reader._prepare()
    return reader.text


def read(fname, text=None, codings=None,
        errors='strict', platform=sys.platform):
    return HtmlReader(fname, text, codings, errors, platform).read()


def write(fname, doc=None, text=None, platform=sys.platform):
    return HtmlWriter(fname, doc, text, platform).write()
