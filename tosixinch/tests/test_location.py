
import io
import os
import sys

import pytest

from tosixinch import location

dirname = os.path.dirname
abspath = os.path.abspath


# based from: django/tests/utils_tests/test_text.py
def test_slugify():
    items = (
        # given - expected - Unicode?
        ('Hello, World!', 'hello-world', False),
        ('spam & eggs', 'spam-eggs', False),
        (' multiple---dash and  space ', 'multiple-dash-and-space', False),
        ('\t whitespace-in-value \n', 'whitespace-in-value', False),
        ('underscore_in-value', 'underscore_in-value', False),
        ('__strip__underscore-value___', 'strip__underscore-value', False),
        ('--strip-dash-value---', 'strip-dash-value', False),
        ('__strip-mixed-value---', 'strip-mixed-value', False),
        ('_ -strip-mixed-value _-', 'strip-mixed-value', False),
        ('spam & ıçüş', 'spam-ıçüş', True),
        ('foo ıç bar', 'foo-ıç-bar', True),
        ('    foo ıç bar', 'foo-ıç-bar', True),
        ('你好', '你好', True),
        ('İstanbul', 'istanbul', True),

        ('user=john&lang=en', 'user-john-lang-en', False),
    )
    for value, output, is_unicode in items:
        assert location.slugify(value, allow_unicode=is_unicode) == output


class TestMakePath:

    def compare(self, url, fname, fnew):
        loc= location.Location(url)
        assert loc.fname == fname
        assert loc.fnew == fnew

    def test(self):
        url, fname, fnew = (
            'https://aaa.org/bbb.html',
            '_htmls/aaa.org/bbb.html',
            '_htmls/aaa.org/bbb~.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'https://aaa.org/bbb',
            '_htmls/aaa.org/bbb/_',
            '_htmls/aaa.org/bbb/_~.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            'aaa/bbb.html',
            abspath('.') + '/aaa/bbb.html',
            '_htmls' + abspath('.') + '/aaa/bbb~.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            '../../aaa/bbb.html',
            abspath('../../') + '/aaa/bbb.html',
            '_htmls' + abspath('../..') + '/aaa/bbb~.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            '/aaa/bbb.html',
            '/aaa/bbb.html',
            '_htmls/aaa/bbb~.html')
        self.compare(url, fname, fnew)

    def test_filescheme(self):
        fname = '/aaa/bbb.html'
        fnew = '_htmls/aaa/bbb~.html'

        url = 'file:/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file:///aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file://localhost/aaa/bbb.html'
        self.compare(url, fname, fnew)

        url = 'file://aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)
        url = 'file:////aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)


    def test_rootpath(self):
        fname = '/aaa/bbb.html'
        fnew = '_htmls/aaa/bbb~.html'

        url = '/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = '//aaa/bbb.html'
        self.compare(url, url, fnew)  # note arguments: url, url, fnew
        url = '///aaa/bbb.html'
        self.compare(url, fname, fnew)


class TestLocalReference:

    def compare(self, url, fname, ref):
        baseurl = 'http://aaa.org'
        component = location.Component(url, baseurl)
        assert component.fname == fname
        assert component.relative_reference == ref

    def test(self):
        # No extension
        url, fname, ref = (
            'https://aaa.org/bbb',
            '_htmls/aaa.org/bbb/_',
            'bbb/_')
        self.compare(url, fname, ref)

        url, fname, ref = (
            'aaa/bbb',
            '_htmls/aaa.org/aaa/bbb/_',
            'aaa/bbb/_')
        self.compare(url, fname, ref)

        # With extension
        url, fname, ref = (
            'https://aaa.org/bbb.jpg',
            '_htmls/aaa.org/bbb.jpg',
            'bbb.jpg')
        self.compare(url, fname, ref)

        url, fname, ref = (
            'aaa/bbb.jpg',
            '_htmls/aaa.org/aaa/bbb.jpg',
            'aaa/bbb.jpg')
        self.compare(url, fname, ref)

        # With query
        url, fname, ref = (
            'https://aaa.org/bbb?cc',
            '_htmls/aaa.org/bbb?cc',
            'bbb%3Fcc')
        self.compare(url, fname, ref)

        # 2022/05
        # commented out following '_add_index' moving
        # I plan to reintroduce them
        # url, fname, ref = (
        #     'https://aaa.org/bbb%3Fcc',
        #     '_htmls/aaa.org/bbb?cc/_',
        #     'bbb%3Fcc/_')
        # self.compare(url, fname, ref)

        url, fname, ref = (
            'aaa/bbb?cc',
            '_htmls/aaa.org/aaa/bbb?cc',
            'aaa/bbb%3Fcc')
        self.compare(url, fname, ref)

        # 2022/05
        # commented out following '_add_index' moving
        # I plan to reintroduce them
        # url, fname, ref = (
        #     'aaa/bbb%3Fcc',
        #     '_htmls/aaa.org/aaa/bbb?cc/_',
        #     'aaa/bbb%3Fcc/_')
        # self.compare(url, fname, ref)

        # With unquoted characters
        url, fname, ref = (
            'https://aaa.org/bbb 1.jpg',
            '_htmls/aaa.org/bbb 1.jpg',
            'bbb%201.jpg')
        self.compare(url, fname, ref)

        url, fname, ref = (
            'aaa/bbb 1.jpg',
            '_htmls/aaa.org/aaa/bbb 1.jpg',
            'aaa/bbb%201.jpg')
        self.compare(url, fname, ref)

        # colon in relative reference
        url, fname, ref = (
            'https://aaa.org/bbb:cc',
            '_htmls/aaa.org/bbb:cc/_',
            'bbb%3Acc/_')
        self.compare(url, fname, ref)

    def test_relative_reference(self):
        url, fname, ref = (
            '//aaa.org/bbb?cc',
            '_htmls/aaa.org/bbb?cc',
            'bbb%3Fcc')
        self.compare(url, fname, ref)

        url, fname, ref = (
            '/bbb/cc.jpg',
            '_htmls/aaa.org/bbb/cc.jpg',
            'bbb/cc.jpg')
        self.compare(url, fname, ref)


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
