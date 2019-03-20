
import os
import sys

import pytest

import tosixinch.location as loc

dirname = os.path.dirname
abspath = os.path.abspath


class TestMakePath:

    def compare(self, url, fname, fnew):
        location = loc.Location(url, platform='linux')
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


class TestLocalReferenceRaw:

    def compare(self, url, local_url, fname):
        base = 'http://aaa.org'
        component = loc.Component(url, base, platform='linux')
        assert component._make_local_url(url) == local_url
        assert component._make_filename(url) == fname

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
        component = loc.Component(url, base, platform='linux')
        assert component.component_url == local_url
        assert component.component_fname == fname

    def test_relative_reference(self):
        url, local_url, fname = (
            '//aaa.org/bbb?cc',
            '_htmls/aaa.org/bbb%3Fcc_index--tosixinch',
            '_htmls/aaa.org/bbb?cc_index--tosixinch')
        self.compare(url, local_url, fname)

        url, local_url, fname = (
            '/bbb/cc.jpg',
            '_htmls/aaa.org/bbb/cc.jpg',
            '_htmls/aaa.org/bbb/cc.jpg')
        self.compare(url, local_url, fname)
