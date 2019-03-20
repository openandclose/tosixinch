
import os
import sys

import lxml.html
import pytest

import tosixinch.util as util
from tosixinch import location

j = '\n'.join
fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


class TestFilteredIter:

    def test(self):
        data = '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>'
        expected = [
            '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>',
            '<h3>aaa</h3>',
            '<div><p>bbb<span>ccc</span></p></div>']

        def is_not_p(el):
            if el.tag == 'p':
                return False
            return True

        doc = fromstring(data)
        output = []
        for el in util.conditioned_iter(doc, is_not_p):
            output.append(tostring(el))
        assert list(output) == expected


class TestBlankHtml:

    def test(self):
        expected = '<!DOCTYPE html>\n<html><body></body></html>'
        html = util.build_blank_html()
        assert tostring(html.getroottree()) == expected


class TestXpath:

    def test(self):
        before = '//div[@class=="main-article"]'
        after = '//div[contains(concat(" ", normalize-space(@class), " "), " main-article ")]'
        assert util.transform_xpath(before) == after


class TestRelinkComponent:
    fname = 'aaa/bb/cc'
    base = 'xxx/yy'

    def run(self, url):
        doc = fromstring('<body><img src=%s></body>' % url)
        util._relink_component(doc, self.base, self.fname)
        return doc

    def test(self):
        url = '../ss/tt'
        doc = self.run(url)
        assert doc.get('src') == '../aaa/ss/tt'

    def test_external_domain(self):
        url = '../../sss/tt/uu'
        doc = self.run(url)
        assert doc.get('src') == '../sss/tt/uu'
