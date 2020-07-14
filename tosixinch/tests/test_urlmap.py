
import os
import posixpath
import sys

import pytest

from tosixinch import urlmap


def test_split_fragment():
    tests = (
        ('http://h',        'http://h',     None),
        ('http://h#',       'http://h',     ''),
        ('http://h/',       'http://h/',    None),
        ('http://h/#',      'http://h/',    ''),
        ('http://h#f',      'http://h',     'f'),
        ('http://h/#f',     'http://h/',    'f'),
        ('http://h/?q',     'http://h/?q',  None),
        ('http://h/p?q',    'http://h/p?q', None),
        ('http://h/p#f',    'http://h/p',   'f'),
        ('http://h/?q#f',   'http://h/?q',  'f'),

        ('h',               'h',            None),
        ('#',               '',             ''),
        ('#f',              '',             'f'),
        ('h#f',             'h',            'f'),
    )
    for input, url, fragment in tests:
        assert url == urlmap._split_fragment(input)[0]
        assert fragment == urlmap._split_fragment(input)[1]
        assert input == urlmap._add_fragment(*urlmap._split_fragment(input))


def test_url2path():
    tests = (
        ('a/b?q#f',         'a/b?q#f'),
        ('a/b/?q',          'a/b/?q'),
        ('a/b?q/r',         'a/b?q_r'),
        ('a/b?q?r',         'a/b?q?r'),
        ('a/b%3Fq',         'a/b?q'),
        ('a/b%3Fq%3Fr',     'a/b?q?r'),
        ('a/fran%C3%A7ais', 'a/français'),

        ('a//b',            'a/_blank_/b'),
        ('a///b',           'a/_blank_/_blank_/b'),
    )
    for url, path in tests:
        assert urlmap._url2path(url, platform='linux') == path


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
        assert urlmap._url2path(url, platform='win32') == expected


def test_path2url():
    tests = (
        ('a/b?q#f',     'a/b%3Fq%23f'),
        ('a/b/?q',      'a/b/%3Fq'),
        ('a/b?q_r',     'a/b%3Fq_r'),
        ('a/b?q?r',     'a/b%3Fq%3Fr'),
        ('a/b%3Fq',     'a/b%253Fq'),
        ('a/b%3Fq%3Fr', 'a/b%253Fq%253Fr'),
        ('a/français',  'a/fran%C3%A7ais'),
    )
    for path, expected in tests:
        assert urlmap._path2url(path, platform='linux') == expected


def test_path2url_on_windows():
    tests = (
        (r'a\b#f',          'a/b%23f'),
        (r'a\b%3Fq',        'a/b%253Fq'),
        (r'a\b%3Fq%3Fr',    'a/b%253Fq%253Fr'),
        (r'a\français',     'a/fran%C3%A7ais'),
    )
    for path, expected in tests:
        assert urlmap._path2url(path, platform='win32') == expected


def test_path2ref():

    if sys.platform == 'win32':
        return

    pwd = posixpath.abspath('.')
    climbs = len(pwd.split('/'))

    basepath = 'x/y'

    tests = (
        ('a/b',         '../a/b'),
        ('a/b?q#f',     '../a/b%3Fq%23f'),
        ('/a/b',        '../' * climbs + 'a/b'),
    )

    for path, expected in tests:
        ref = urlmap._path2ref(path, basepath, platform='linux')
        assert ref == expected

    basepath = '/x/y'

    tests = (
        ('a/b',         '..' + pwd + '/a/b'),
        ('a/b?q#f',     '..' + pwd + '/a/b%3Fq%23f'),
        ('/a/b',        '../a/b'),
    )

    for path, expected in tests:
        ref = urlmap._path2ref(path, basepath, platform='linux')
        assert ref == expected


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
        ref = urlmap._path2ref(path, basepath, platform='win32')
        assert ref == expected

    basepath = r'c:\x\y'

    tests = (
        (r'a\b',         '../s/t/a/b'),
        (r'a\b?q#f',     '../s/t/a/b%3Fq%23f'),
        (r'c:\a\b',      '../a/b'),
    )

    for path, expected in tests:
        ref = urlmap._path2ref(path, basepath, platform='win32')
        assert ref == expected


class TestURL:

    def test_unroot(self):
        tests = (
            ('http://h/p.html',     'h/p.html'),
            ('http://h/p',          'h/p/_'),
            ('http://h/p?q',        'h/p?q'),
            ('http://h/p%3Fq',      'h/p?q/_'),
            ('http://h/p#f',        'h/p/_'),
        )

        for url, expected in tests:
            assert urlmap.URL(url, platform='linux').unroot() == expected


class TestFileURL:

    def test_unroot(self):

        tests = (
            ('file:///p.html',          'p.html'),
            ('file://localhost/p.html', 'p.html'),
            # Note: FileURL doesn't add index.
            ('file:///p',               'p'),
        )

        for url, expected in tests:
            u = urlmap.FileURL(url, platform='linux')
            assert u.unroot() == expected

    def test_unroot_error(self):

        tests = (
            ('file://p.html',           'p.html'),
            ('file://host/p.html',      'p.html'),
        )

        for url, expected in tests:
            u = urlmap.FileURL(url, platform='linux')
            with pytest.raises(ValueError):
                assert u.unroot() == expected


class TestFileURLOnWindows:

    def test_unroot(self):

        tests = (
            ('file:///C:/p.html',       r'c:\p.html',   r'c\p.html'),
            ('file:///C:/p',            r'c:\p',        r'c\p'),
            ('file:///C:p.html',        r'c:p.html',    r'c\p.html'),  # OK?
            ('file:///C:/p.html?q',     r'c:\p.html_q', r'c\p.html_q'),
        )

        for url, path, expected in tests:
            u = urlmap.FileURL(url, platform='win32')
            assert u.absolute_path == path
            assert u.unroot() == expected


class TestPath:

    def test_unroot(self):

        pwd = posixpath.abspath('.')

        tests = (
            ('a/b',         pwd + '/a/b',   pwd[1:] + '/a/b'),
            ('/a/b',        '/a/b',         'a/b'),
        )

        for path, normalized, unrooted in tests:
            p = urlmap.Path(path, platform='linux')
            assert p.absolute_path == normalized
            assert p.unroot() == unrooted


class TestPathOnWindows:

    def test_unroot(self, monkeypatch):

        # ntpath._abspath_fallback uses this 'getcwd'.
        monkeypatch.setattr(os, 'getcwd', lambda: r'c:\s\t')

        tests = (
            (r'a\b',        r'c:\s\t\a\b',      r'c\s\t\a\b'),
            (r'c:\a\b',     r'c:\a\b',          r'c\a\b'),
        )

        for path, normalized, unrooted in tests:
            p = urlmap.Path(path, platform='win32')
            assert p.absolute_path == normalized
            assert p.unroot() == unrooted


class TestMap:

    def test_names(self):

        tests = (
            ('http://a/b',      'http://a/b',       'a/b/_'),
            ('file:///a/b',     '/a/b',             'a/b'),
            ('/a/b',            '/a/b',             'a/b'),
        )

        for src, input_name, mapped_name in tests:
            m = urlmap.Map(src, platform='linux')
            assert m.input_name == input_name
            assert m.mapped_name == mapped_name


class TestMapOnWindows:

    def test_names(self):

        tests = (
            ('http://a/b',      'http://a/b',       r'a\b\_'),
            ('file:///c:a/b',   r'c:a\b',           r'c\a\b'),
            (r'c:a\b',          r'c:a\b',           r'c\a\b'),
        )

        for src, input_name, mapped_name in tests:
            m = urlmap.Map(src, platform='win32')
            assert m.input_name == input_name
            assert m.mapped_name == mapped_name


class TestRef:

    def test_names(self):

        baseurl = 'http://x/y/z'

        tests = (
            ('',                    ''),
            ('#',                   ''),
            ('#f',                  '#f'),
            ('z',                   ''),
            ('../y/z',              ''),

            # strange, but it is alright. fnames are: 'x/y/z/_' and 'x/y/a/_'
            ('a',                   '../a/_'),
            ('a/b',                 '../a/b/_'),

            ('http://x/y/z',        ''),
            ('http://x/y/z#f',      '#f'),

            # strange, but it is alright. fnames are: 'x/y/z/_' and 'x/y/c/_'
            ('http://x/y/c',        '../c/_'),

            ('http://a/b/c',        '../../../a/b/c/_'),
        )

        for url, ref in tests:
            m = urlmap.Map(baseurl, input_type='url')
            assert m.get_relative_reference(url) == ref

            r = urlmap.Ref(url, baseurl)
            assert r.relative_reference == ref

        baseurl = 'http://x/y/z.html'

        tests = (
            ('a.html',              'a.html'),
            ('a.html#f',            'a.html#f'),
            ('../a.html',           '../a.html'),

            ('a.html?q',            'a.html%3Fq'),
            ('a.html?q#f',          'a.html%3Fq#f'),
        )

        for url, ref in tests:
            m = urlmap.Map(baseurl, input_type='url')
            assert m.get_relative_reference(url) == ref

            r = urlmap.Ref(url, baseurl)
            assert r.relative_reference == ref
