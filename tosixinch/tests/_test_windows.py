
import ntpath
import os
import sys

import pytest

from tosixinch import urlmap
from tosixinch import location

# urlmap -----------------------------------------

def test_url2path_on_windows():
    tests = (
        ('a/b?q#f',         r'a\b_q#f'),
        ('a/b/?q',          r'a\b\_q'),
        ('a/b?q/r',         r'a\b_q_r'),
        ('a/b?q?r',         r'a\b_q_r'),
        ('a/b%3Fq',         r'a\b_q'),
        ('a/b%3Fq%3Fr',     r'a\b_q_r'),
        ('a/fran%C3%A7ais', r'a\français'),
    )
    for url, expected in tests:
        assert urlmap._url2path(url) == expected


def test_path2url_on_windows():
    tests = (
        (r'a\b#f',          'a/b%23f'),
        (r'a\b%3Fq',        'a/b%253Fq'),
        (r'a\b%3Fq%3Fr',    'a/b%253Fq%253Fr'),
        (r'a\français',     'a/fran%C3%A7ais'),
    )
    for path, expected in tests:
        assert urlmap._path2url(path) == expected


def test_path2ref_on_windows(monkeypatch):

    # ntpath._abspath_fallback uses this 'getcwd'.
    monkeypatch.setattr(os, 'getcwd', lambda: r'c:\s\t')

    basepath = r'x\y'

    tests = (
        (r'a\b',         '../a/b'),
        (r'a\b?q#f',     '../a/b%3Fq%23f'),
        (r'c:\a\b',      '../../../a/b'),
    )

    for path, expected in tests:
        ref = urlmap._path2ref(path, basepath)
        assert ref == expected

    basepath = r'c:\x\y'

    tests = (
        (r'a\b',         '../s/t/a/b'),
        (r'a\b?q#f',     '../s/t/a/b%3Fq%23f'),
        (r'c:\a\b',      '../a/b'),
    )

    for path, expected in tests:
        ref = urlmap._path2ref(path, basepath)
        assert ref == expected


class TestFileURLOnWindows:

    def test_unroot(self):

        tests = (
            ('file:///C:/p.html',       r'c:\p.html',   r'c\p.html'),
            ('file:///C:/p',            r'c:\p',        r'c\p'),
            ('file:///C:p.html',        r'c:p.html',    r'c\p.html'),  # OK?
            ('file:///C:/p.html?q',     r'c:\p.html_q', r'c\p.html_q'),
        )

        for url, path, expected in tests:
            u = urlmap.FileURL(url)
            assert u.path == path
            assert u.unroot() == expected


class TestPathOnWindows:

    def test_unroot(self, monkeypatch):

        # ntpath._abspath_fallback uses this 'getcwd'.
        monkeypatch.setattr(os, 'getcwd', lambda: r'c:\s\t')

        tests = (
            (r'a\b',        r'c:\s\t\a\b',      r'c\s\t\a\b'),
            (r'c:\a\b',     r'c:\a\b',          r'c\a\b'),
        )

        for path, normalized, unrooted in tests:
            p = urlmap.Path(path)
            assert p.path == normalized
            assert p.unroot() == unrooted


class TestMapOnWindows:

    def test_names(self):

        tests = (
            ('http://a/b',      'http://a/b',       r'a\b\_'),
            ('file:///c:a/b',   r'c:a\b',           r'c\a\b'),
            (r'c:a\b',          r'c:a\b',           r'c\a\b'),
        )

        for src, input_name, mapped_name in tests:
            m = urlmap.Map(src)
            assert m.input_name == input_name
            assert m.mapped_name == mapped_name


# location ---------------------------------------

class TestWindowsMakePath:

    def compare(self, url, fname, fnew):
        loc = location.Location(url)
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
        comp= location.Component(url, base)
        assert comp.fname == fname
        assert comp.relative_reference == ref

    def test(self):
        url, fname, ref  = (
            'https://aaa.org/bbb',
            r'_htmls\aaa.org\bbb\_',
            'bbb/_')
        self.compare(url, fname, ref)
