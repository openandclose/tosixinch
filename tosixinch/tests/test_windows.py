
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
            # r'_htmls\aaa.org\bbb.html',
            # r'_htmls\aaa.org\bbb--extracted.html')
            r'_htmls/aaa.org/bbb.html',
            r'_htmls/aaa.org/bbb--extracted.html')
        self.compare(url, fname, fnew)

        url, fname, fnew = (
            r'C:\aaa.org\bbb.html',
            # r'C:\aaa.org\bbb.html',
            # r'_htmls\C\aaa.org\bbb--extracted.html')
            r'c:/aaa.org/bbb.html',
            r'_htmls/c/aaa.org/bbb--extracted.html')
        self.compare(url, fname, fnew)


class TestWindowsLocalReferenceRaw:

    def compare(self, url, local_url, fname):
        comp = location.Component(url, '.', platform='win32')
        url = location._normalize_url(url, platform=comp.platform)
        assert comp._make_local_url(url) == local_url
        assert location._escape_filename(url) == fname

    def test(self):
        url, local_url, fname = (
            'aaa/bbb?cc',
            'aaa/bbb_cc',
            # r'aaa\bbb_cc')
            r'aaa/bbb_cc')
        self.compare(url, local_url, fname)
