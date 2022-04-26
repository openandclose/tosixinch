
import ntpath
import os
import sys

import pytest

from tosixinch import location


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

        url = r'\\?\aaa\bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, url, fnew)
        url = r'\\.\aaa\bbb.html'
        with pytest.raises(ValueError):
            self.compare(url, url, fnew)


class TestWindowsLocalReference:

    def compare(self, url, fname, ref):
        base = 'http://aaa.org'
        comp= location.Component(url, base, platform='win32')
        assert comp.fname == fname
        assert comp.relative_reference == ref

    def test(self):
        url, fname, ref  = (
            'https://aaa.org/bbb',
            r'_htmls\aaa.org\bbb\_',
            'bbb/_')
        self.compare(url, fname, ref)
