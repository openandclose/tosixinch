
import os
import sys

import lxml.html
import pytest

import tosixinch.util as util

j = '\n'.join
fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


class TestLocalReference:

    def compare(self, url, local_url, fname):
        u, f = util.make_local_references(url)
        assert u == local_url
        assert f == fname

    def test(self):
        url, local_url, fname = (
            'https://aaa.org/bbb?cc',
            'https://aaa.org/bbb%3Fcc',
            'https://aaa.org/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'https://aaa.org/bbb%3Fcc',
            'https://aaa.org/bbb%3Fcc',
            'https://aaa.org/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb?cc',
            'aaa/bbb%3Fcc',
            'aaa/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb%3Fcc',
            'aaa/bbb%3Fcc',
            'aaa/bbb?cc')
        self.compare(url, local_url, fname)

    def test_unicode(self):
        url, local_url, fname = (
            'aaa/fran%C3%A7ais',
            'aaa/fran%C3%A7ais',
            'aaa/français')
        self.compare(url, local_url, fname)

        # url, local_url, fname = (
        #     'aaa/français',
        #     'aaa/fran%C3%A7ais',
        #     'aaa/français')
        # self.compare(url, local_url, fname)


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


class TestMakePath:

    def compare(self, url, fname, fnew):
        f = util.make_path(url)
        assert f == fname
        f = util.make_new_fname(f)
        assert f == fnew

    def test(self):
        url, fname, fnew = (
            'https://aaa.org/bbb.html',
            '_htmls/aaa.org/bbb.html',
            '_htmls/aaa.org/bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'https://aaa.org/bbb',
            # '_htmls/aaa.org/bbb',
            '_htmls/aaa.org/bbb/index--tosixinch',
            # '_htmls/aaa.org/bbb--extracted.html')
            '_htmls/aaa.org/bbb/index--tosixinch--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'https://aaa.org/bbb/',
            '_htmls/aaa.org/bbb/index--tosixinch',
            '_htmls/aaa.org/bbb/index--tosixinch--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            '/aaa.org/bbb.html',
            '/aaa.org/bbb.html',
            '_htmls/aaa.org/bbb--extracted.html')
        self.compare(url, fname, fnew)


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
