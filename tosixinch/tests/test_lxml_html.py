
import io
import textwrap

import lxml.etree
import pytest

from tosixinch import lxml_html

TEXT = """
    <html>
      <head>
        <meta charset="utf-8">
      </head>
      <body>
        <h1>h1 text</h1>
        <p class="aaa bbb">p text</p>
      </body>
    </html>
"""

MIN_TEXT = """<html></html>"""


def _get_root_from_parser(text):
    f = io.StringIO(text)
    tree = lxml.etree.parse(f, parser=lxml_html.HTMLParser())
    return tree.getroot()

def _check_elements(root):
    assert root.head.tag == 'head'
    assert root.body.tag == 'body'
    el = root.xpath('//p[@class=="bbb"]')
    assert el[0].text == 'p text'


def test_htmlparser():
    root = _get_root_from_parser(TEXT)
    _check_elements(root)


def test_no_head_no_body():
    root = _get_root_from_parser(MIN_TEXT)
    assert root.head == None
    assert root.body == None


def test_fromstring():
    root = lxml_html.document_fromstring(TEXT)
    _check_elements(root)
    root = lxml_html.fragments_fromstring(TEXT)[0]
    _check_elements(root)
    # lxml.etree.ParserError: Multiple elements found (h1, p)
    # root = lxml_html.fragment_fromstring(TEXT)
    # _check_elements(root)
    root = lxml_html.fromstring(TEXT)
    _check_elements(root)


def test_error_message():
    msg = """
        //div[@class==="aaa"
                    ^
    """
    msg = textwrap.dedent(msg)

    root = _get_root_from_parser(TEXT)
    with pytest.raises(lxml_html.XPathEvalError) as excinfo:
        el = root.xpath('//div[@class==="aaa"')

    assert msg in str(excinfo.value)
