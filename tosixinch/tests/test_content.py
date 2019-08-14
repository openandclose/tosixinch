
import lxml.html
import pytest

from tosixinch import content

fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


# cf.
# https://bitbucket.org/ianb/formencode/src/tip/formencode/doctest_xml_compare.py
# https://github.com/formencode/formencode/blob/master/formencode/doctest_xml_compare.py
def compare_html(doc1, doc2):
    for x, y in zip(doc1.iter(), doc2.iter()):
        assert x.tag == y.tag
        assert (x.text or '').strip() == (y.text or '').strip()


class TestBlankHtml:

    def test(self):
        expected = '<!DOCTYPE html>\n<html><body></body></html>'
        html = content.build_blank_html()
        assert tostring(html.getroottree()) == expected


class TestRelinkComponent:
    fname = 'aaa/bb/cc'
    base = 'xxx/yy'

    def run(self, url):
        doc = fromstring('<body><img src=%s></body>' % url)
        content._relink_component(doc, self.base, self.fname)
        return doc

    def test(self):
        url = '../ss/tt'
        doc = self.run(url)
        assert doc.get('src') == '../aaa/ss/tt'

    def test_external_domain(self):
        url = '../../sss/tt/uu'
        doc = self.run(url)
        assert doc.get('src') == '../sss/tt/uu'


class TestReadabilityHtmlContent:

    def test_imports(self):
        text = """
        <html>
          <head>
            <title>aaa - bbb</title>
          </head>
          <body>
            <h1>xxx</h1>
            <h1>yyy</h1>
            <div>zzz</div>
          </body>
        </html>"""
        expected = """
        <html>
          <head>
            <meta charset="utf-8">
            <title>aaa - bbb</title>
          </head>
          <body>
            <h1>aaa - bbb</h1>
            <h2>xxx</h2>
            <h2>yyy</h2>
            <p>zzz</p>
          </body>
        </html>"""
        if content.readability:
            c = content.ReadabilityHtmlContent(
                    'url', 'fname', 'fnew', text)
            c.build()
            compare_html(c.doc, fromstring(expected))
