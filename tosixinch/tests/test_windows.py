
import ntpath
import os
import sys

import pytest

import tosixinch.util as util


@pytest.fixture(autouse=True)
def use_ntpath(monkeypatch):
    monkeypatch.setattr(os, 'path', ntpath)


class TestWindowsLocalReference:

    def compare(self, url, local_url, fname):
        u, f = util.make_local_references(url, platform='win32')
        assert u == local_url
        assert f == fname

    def test(self):
        url, local_url, fname = (
            'aaa/bbb?cc',
            'aaa/bbb_cc',
            r'aaa\bbb_cc')
        self.compare(url, local_url, fname)


class TestWindowsMakePath:

    def compare(self, url, fname, fnew):
        f = util.make_path(url, platform='win32')
        assert f == fname
        f = util.make_new_fname(f, platform='win32')
        assert f == fnew
        
    def test(self):
        url, fname, fnew = (
            'https://aaa.org/bbb.html',
            r'_htmls\aaa.org\bbb.html',
            r'_htmls\aaa.org\bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            r'C:\aaa.org\bbb.html',
            r'C:\aaa.org\bbb.html',
            r'_htmls\C\aaa.org\bbb--extracted.html')
        self.compare(url, fname, fnew)
