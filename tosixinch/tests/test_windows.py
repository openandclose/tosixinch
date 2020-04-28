
import ntpath
import os
import sys

import pytest

from tosixinch import location

@pytest.fixture(autouse=True)
def use_ntpath(monkeypatch):
    monkeypatch.setattr(os, 'path', ntpath)


class TestWindowsMakePath:

    def compare(self, url, fname, fnew):
        loc = location.Location(url, platform='win32')
        assert loc.fname == fname
        assert loc.fnew == fnew
        
    def test(self):
        url, fname, fnew = (
            'https://aaa.org/bbb.html',
            r'_htmls\aaa.org\bbb.html',
            r'_htmls\aaa.org\bbb~.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            r'C:\aaa.org\bbb.html',
            r'c:\aaa.org\bbb.html',
            r'_htmls\c\aaa.org\bbb~.html')
        self.compare(url, fname, fnew)

    def test_filescheme(self):
        fname = r'c:\aaa\bbb.html'
        fnew = r'_htmls\c\aaa\bbb~.html'

        url = 'file:/c:/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file://c:/aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)
        url = 'file:///c:/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file://localhost/c:/aaa/bbb.html'
        self.compare(url, fname, fnew)
        url = 'file:////c:/aaa/bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, fname, fnew)

    def test_rootpath(self):
        fname = r'c:\aaa\bbb.html'
        fnew = r'_htmls\c\aaa\bbb~.html'

        url = r'c:\aaa\bbb.html'
        self.compare(url, fname, fnew)
        url = r'c:\\aaa\bbb.html'
        self.compare(url, fname, fnew)

        fnew = r'_htmls\aaa\bbb~.html'

        url = r'\\aaa\bbb.html'
        self.compare(url, url, fnew)  # note arguments: url, url, fnew

        url = r'\\?\aaa\bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, url, fnew)
        url = r'\\.\aaa\bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, url, fnew)


class TestWindowsLocalReferenceRaw:

    def compare(self, url, local_url, fname):
        comp = location.Component(url, '.', platform='win32')
        url = location._tamper_windows_fname(url)
        assert comp._escape_fname_reference(url) == local_url
        assert location._tamper_fname(url) == fname

    def test(self):
        url, local_url, fname = (
            'aaa/bbb?cc',
            r'aaa\bbb_cc',
            r'aaa\bbb_cc')
        self.compare(url, local_url, fname)


class TestWindowsLocalReference:

    def compare(self, url, local_url, fname):
        base = 'http://aaa.org'
        comp= location.Component(url, base, platform='win32')
        assert comp.fname_reference == local_url
        assert comp.fname == fname

    def test(self):
        url, local_url, fname = (
            'https://aaa.org/bbb',
            'bbb/_',
            r'_htmls\aaa.org\bbb\_')
        self.compare(url, local_url, fname)
