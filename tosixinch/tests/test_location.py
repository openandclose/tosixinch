
import os
import sys

import pytest

import tosixinch.location as loc


class TestMakePath:

    def compare(self, url, fname, fnew):
        location = loc.Location(url)
        assert location.fname == fname
        assert location.fnew == fnew

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


class TestLocalReference:

    def compare(self, url, local_url, fname):
        base = 'http://aaa.org'
        component = loc.Component(url, base)
        u, f = component._make_local_references(url)
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
