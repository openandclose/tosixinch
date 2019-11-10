
import io
import os
import sys

import pytest

from tosixinch import location

dirname = os.path.dirname
abspath = os.path.abspath


class TestMakePath:

    def compare(self, url, fname, fnew):
        loc= location.Location(url, platform='linux')
        assert loc.fname == fname
        assert loc.fnew == fnew

    def test(self):
        url, fname, fnew = (
            'https://aaa.org/bbb.html',
            '_htmls/aaa.org/bbb.html',
            '_htmls/aaa.org/bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'https://aaa.org/bbb',
            '_htmls/aaa.org/bbb/index--tosixinch',
            '_htmls/aaa.org/bbb/index--tosixinch--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'aaa/bbb.html',
            abspath('.') + '/aaa/bbb.html',
            '_htmls' + abspath('.') + '/aaa/bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            '../../aaa/bbb.html',
            abspath('../../') + '/aaa/bbb.html',
            '_htmls' + abspath('../..') + '/aaa/bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            '/aaa/bbb.html',
            '/aaa/bbb.html',
            '_htmls/aaa/bbb--extracted.html')
        self.compare(url, fname, fnew)

    def test_filescheme(self):
        fname = '/aaa/bbb.html'
        fnew = '_htmls/aaa/bbb--extracted.html'

        url = 'file:/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file://aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)
        url = 'file:///aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file://localhost/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file:////aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)


    def test_rootpath(self):
        fname = '/aaa/bbb.html'
        fnew = '_htmls/aaa/bbb--extracted.html'

        url = '/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = '//aaa/bbb.html'
        self.compare(url, url, fnew)  # note arguments: url, url, fnew
        url = '///aaa/bbb.html'
        self.compare(url, fname, fnew)


class TestLocalReferenceRaw:

    def compare(self, url, local_url, fname):
        base = 'http://aaa.org'
        component = location.Component(url, base, platform='linux')
        assert component._escape_fname_reference(url) == local_url
        assert location._url2path(url, platform='linux') == fname

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


class TestLocalReference:

    def compare(self, url, local_url, fname):
        base = 'http://aaa.org'
        component = location.Component(url, base, platform='linux')
        assert component.fname_reference == local_url
        assert component.fname == fname

    def test(self):
        # No extension
        url, local_url, fname = (
            'https://aaa.org/bbb',
            'bbb/index--tosixinch',
            '_htmls/aaa.org/bbb/index--tosixinch')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb',
            'aaa/bbb/index--tosixinch',
            '_htmls/aaa.org/aaa/bbb/index--tosixinch')
        self.compare(url, local_url, fname)

        # With extension
        url, local_url, fname = (
            'https://aaa.org/bbb.jpg',
            'bbb.jpg',
            '_htmls/aaa.org/bbb.jpg')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb.jpg',
            'aaa/bbb.jpg',
            '_htmls/aaa.org/aaa/bbb.jpg')
        self.compare(url, local_url, fname)

        # With query
        url, local_url, fname = (
            'https://aaa.org/bbb?cc',
            'bbb%3Fcc',
            '_htmls/aaa.org/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'https://aaa.org/bbb%3Fcc',
            'bbb%3Fcc/index--tosixinch',
            '_htmls/aaa.org/bbb?cc/index--tosixinch')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb?cc',
            'aaa/bbb%3Fcc',
            '_htmls/aaa.org/aaa/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb%3Fcc',
            'aaa/bbb%3Fcc/index--tosixinch',
            '_htmls/aaa.org/aaa/bbb?cc/index--tosixinch')
        self.compare(url, local_url, fname)

        # With unquoted characters
        url, local_url, fname = (
            'https://aaa.org/bbb 1.jpg',
            'bbb%201.jpg',
            # 'bbb 1.jpg',
            '_htmls/aaa.org/bbb 1.jpg')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            'aaa/bbb 1.jpg',
            'aaa/bbb%201.jpg',
            # 'aaa/bbb 1.jpg',
            '_htmls/aaa.org/aaa/bbb 1.jpg')
        self.compare(url, local_url, fname)

        # colon in relative url
        url, local_url, fname = (
            'https://aaa.org/bbb:cc',
            './bbb:cc/index--tosixinch',
            '_htmls/aaa.org/bbb:cc/index--tosixinch')
        self.compare(url, local_url, fname)

    def test_relative_reference(self):
        url, local_url, fname = (
            '//aaa.org/bbb?cc',
            'bbb%3Fcc',
            '_htmls/aaa.org/bbb?cc')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            '/bbb/cc.jpg',
            'bbb/cc.jpg',
            '_htmls/aaa.org/bbb/cc.jpg')
        self.compare(url, local_url, fname)


class TestReplacementParser:

    URLS = ['https://www.reddit.com/aaa', 'https://www.reddit.com/bbb']

    def compare(self, text, urls):
        f = io.StringIO(text)
        parser = location.ReplacementParser(f, self.URLS)
        assert urls == parser._parse()

    def compare_bad(self, text):
        f = io.StringIO(text)
        parser = location.ReplacementParser(f, self.URLS)
        with pytest.raises(ValueError):
            parser._parse()

    def test(self):
        text = r"""
            https://www\.reddit\.com/
            https://old.reddit.com/

        """
        urls = ['https://old.reddit.com/aaa', 'https://old.reddit.com/bbb']
        self.compare(text, urls)

        text = r"""


            https://www\.reddit\.com/
            https://old.reddit.com/"""
        self.compare(text, urls)

        text = r"""
            # xxx
            https://www\.reddit\.com/
            # xxx
            https://old.reddit.com/

            # xxx
        """
        self.compare(text, urls)

        text = r"""
            (?<!\\)\.c\w+/
            .org/
        """
        urls = ['https://www.reddit.org/aaa', 'https://www.reddit.org/bbb']
        self.compare(text, urls)

    def test_bad(self):
        text = r"""
            https://www\.reddit\.com/

            https://old.reddit.com/
        """
        self.compare_bad(text)

        text = r"""
            https://www\.reddit\.com/
            https://old.reddit.com/
            xxx

        """
        self.compare_bad(text)
