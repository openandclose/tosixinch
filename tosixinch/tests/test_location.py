
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

    def compare(self, url, dfile, efile):
        loc= location.Location(url)
        assert loc.dfile == dfile
        assert loc.efile == efile

    def test(self):
        url, dfile, efile = (
            'https://aaa.org/bbb.html',
            '_htmls/aaa.org/bbb.html',
            '_htmls/aaa.org/bbb.html')
        self.compare(url, dfile, efile)

        url, dfile, efile = (
            'https://aaa.org/bbb',
            '_htmls/aaa.org/bbb',
            '_htmls/aaa.org/bbb')
        self.compare(url, dfile, efile)

        url, dfile, efile = (
            'aaa/bbb.html',
            abspath('.') + '/aaa/bbb.html',
            '_htmls' + abspath('.') + '/aaa/bbb.html')
        self.compare(url, dfile, efile)

        url, dfile, efile = (
            '../../aaa/bbb.html',
            abspath('../../') + '/aaa/bbb.html',
            '_htmls' + abspath('../..') + '/aaa/bbb.html')
        self.compare(url, dfile, efile)

        url, dfile, efile = (
            '/aaa/bbb.html',
            '/aaa/bbb.html',
            '_htmls/aaa/bbb.html')
        self.compare(url, dfile, efile)

    def test_filescheme(self):
        dfile = '/aaa/bbb.html'
        efile = '_htmls/aaa/bbb.html'

        url = 'file:/aaa/bbb.html'
        self.compare(url, dfile, efile)
        url = 'file:///aaa/bbb.html'
        self.compare(url, dfile, efile)
        url = 'file://localhost/aaa/bbb.html'
        self.compare(url, dfile, efile)

        url = 'file://aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, dfile, efile)
        url = 'file:////aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, dfile, efile)


    def test_rootpath(self):
        dfile = '/aaa/bbb.html'
        efile = '_htmls/aaa/bbb.html'

        url = '/aaa/bbb.html'
        self.compare(url, dfile, efile)
        url = '//aaa/bbb.html'
        self.compare(url, url, efile)  # note arguments: url, url, efile
        url = '///aaa/bbb.html'
        self.compare(url, dfile, efile)


class TestLocalReference:

    def compare(self, url, dfile, ref):
        baseurl = 'http://aaa.org'
        component = location.Component(url, baseurl)
        assert component.dfile == dfile
        assert component.relative_reference == ref

    def test(self):
        # No extension
        url, dfile, ref = (
            'https://aaa.org/bbb',
            '_htmls/aaa.org/bbb',
            'bbb')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'aaa/bbb',
            '_htmls/aaa.org/aaa/bbb',
            'aaa/bbb')
        self.compare(url, dfile, ref)

        # With extension
        url, dfile, ref = (
            'https://aaa.org/bbb.jpg',
            '_htmls/aaa.org/bbb.jpg',
            'bbb.jpg')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'aaa/bbb.jpg',
            '_htmls/aaa.org/aaa/bbb.jpg',
            'aaa/bbb.jpg')
        self.compare(url, dfile, ref)

        # With query
        url, dfile, ref = (
            'https://aaa.org/bbb?cc',
            '_htmls/aaa.org/bbb?cc',
            'bbb%3Fcc')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'https://aaa.org/bbb%3Fcc',
            '_htmls/aaa.org/bbb?cc',
            'bbb%3Fcc')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'aaa/bbb?cc',
            '_htmls/aaa.org/aaa/bbb?cc',
            'aaa/bbb%3Fcc')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'aaa/bbb%3Fcc',
            '_htmls/aaa.org/aaa/bbb?cc',
            'aaa/bbb%3Fcc')
        self.compare(url, dfile, ref)

        # With unquoted characters
        url, dfile, ref = (
            'https://aaa.org/bbb 1.jpg',
            '_htmls/aaa.org/bbb 1.jpg',
            'bbb%201.jpg')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            'aaa/bbb 1.jpg',
            '_htmls/aaa.org/aaa/bbb 1.jpg',
            'aaa/bbb%201.jpg')
        self.compare(url, dfile, ref)

        # colon in relative reference
        url, dfile, ref = (
            'https://aaa.org/bbb:cc',
            '_htmls/aaa.org/bbb:cc',
            'bbb%3Acc')
        self.compare(url, dfile, ref)

    def test_relative_reference(self):
        url, dfile, ref = (
            '//aaa.org/bbb?cc',
            '_htmls/aaa.org/bbb?cc',
            'bbb%3Fcc')
        self.compare(url, dfile, ref)

        url, dfile, ref = (
            '/bbb/cc.jpg',
            '_htmls/aaa.org/bbb/cc.jpg',
            'bbb/cc.jpg')
        self.compare(url, dfile, ref)


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
