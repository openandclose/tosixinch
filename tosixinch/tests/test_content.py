
import lxml.html
import pytest

from tosixinch import content

fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


class TestBlankHtml:

    def test(self):
        expected = '<!DOCTYPE html>\n<html><body></body></html>'
        html = content.build_blank_html()
        assert tostring(html.getroottree()) == expected


class TestXpath:

    def test(self):
        before = '//div[@class=="main-article"]'
        after = '//div[contains(concat(" ", normalize-space(@class), " "), " main-article ")]'
        assert content.transform_xpath(before) == after


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
