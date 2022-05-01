
import re
import urllib.parse

from tosixinch import urlno

rfc3986_baseurl = 'http://a/b/c/d;p?q'

rfc3986_normal_examples = """
    "g:h"           =  "g:h"
    "g"             =  "http://a/b/c/g"
    "./g"           =  "http://a/b/c/g"
    "g/"            =  "http://a/b/c/g/"
    "/g"            =  "http://a/g"
    "//g"           =  "http://g"
    "?y"            =  "http://a/b/c/d;p?y"
    "g?y"           =  "http://a/b/c/g?y"
    "#s"            =  "http://a/b/c/d;p?q#s"
    "g#s"           =  "http://a/b/c/g#s"
    "g?y#s"         =  "http://a/b/c/g?y#s"
    ";x"            =  "http://a/b/c/;x"
    "g;x"           =  "http://a/b/c/g;x"
    "g;x?y#s"       =  "http://a/b/c/g;x?y#s"
    ""              =  "http://a/b/c/d;p?q"
    "."             =  "http://a/b/c/"
    "./"            =  "http://a/b/c/"
    ".."            =  "http://a/b/"
    "../"           =  "http://a/b/"
    "../g"          =  "http://a/b/g"
    "../.."         =  "http://a/"
    "../../"        =  "http://a/"
    "../../g"       =  "http://a/g"
"""

rfc3986_abnormal_examples = """
    "../../../g"    =  "http://a/g"
    "../../../../g" =  "http://a/g"

    "/./g"          =  "http://a/g"
    "/../g"         =  "http://a/g"
    "g."            =  "http://a/b/c/g."
    ".g"            =  "http://a/b/c/.g"
    "g.."           =  "http://a/b/c/g.."
    "..g"           =  "http://a/b/c/..g"

    "./../g"        =  "http://a/b/g"
    "./g/."         =  "http://a/b/c/g/"
    "g/./h"         =  "http://a/b/c/g/h"
    "g/../h"        =  "http://a/b/c/h"
    "g;x=1/./y"     =  "http://a/b/c/g;x=1/y"
    "g;x=1/../y"    =  "http://a/b/c/y"

    "g?y/./x"       =  "http://a/b/c/g?y/./x"
    "g?y/../x"      =  "http://a/b/c/g?y/../x"
    "g#s/./x"       =  "http://a/b/c/g#s/./x"
    "g#s/../x"      =  "http://a/b/c/g#s/../x"

    # urllib.parse has a problem with this.
    # >>> urlunsplit(urlsplit('http:g'))
    # 'http:///g'
    # https://bugs.python.org/issue40938
    # "http:g"        =  "http:g"         ; for strict parsers
    # "http:g"        =  "http://a/b/c/g" ; for backward compatibility
"""


def _iterate(text):
    urls_re = re.compile(r'^\s*"(.*?)"\s*=\s*"(.*?)".*$')

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        yield urls_re.match(line)


rfc3986_normal_examples = _iterate(rfc3986_normal_examples)
rfc3986_abnormal_examples = _iterate(rfc3986_abnormal_examples)
del _iterate


def test_requote():
    tests = (
        ('',                        ''),
        (' ',                       '%20'),
        ('\n',                      '%0A'),

        ('abcde',                   'abcde'),
        ('%61%62%63%64%65',         'abcde'),
        ('%2561%2562%2563%2564%2565',         '%2561%2562%2563%2564%2565'),

        # unreserved
        ('-._~',                    '-._~'),
        ('%2D%2E%5F%7E',            '-._~'),
        ('%2d%2e%5f%7e',            '-._~'),
        ('%252D%252E%255F%257E',    '%252D%252E%255F%257E'),
        # here, case normalization doesn't run
        ('%252d%252e%255f%257e',    '%252d%252e%255f%257e'),

        # reserved
        ("!#$&'()*+,/:;=?@[]",      "!#$&'()*+,/:;=?@[]"),
        ("%21%23%24%26%27%28%29%2A%2B%2C%2F%3A%3B%3D%3F%40%5B%5D",
            "%21%23%24%26%27%28%29%2A%2B%2C%2F%3A%3B%3D%3F%40%5B%5D"),
        ("%21%23%24%26%27%28%29%2a%2b%2c%2f%3a%3b%3d%3f%40%5b%5d",
            "%21%23%24%26%27%28%29%2A%2B%2C%2F%3A%3B%3D%3F%40%5B%5D"),
    
        # not defined ascii printable characters in RFC 3986
        (r'"%<>\^`{|}',                     '%22%25%3C%3E%5C%5E%60%7B%7C%7D'),
        ('%22%25%3C%3E%5C%5E%60%7B%7C%7D',  '%22%25%3C%3E%5C%5E%60%7B%7C%7D'),
        ('%22%25%3c%3e%5c%5e%60%7b%7c%7d',  '%22%25%3C%3E%5C%5E%60%7B%7C%7D'),

        ('£',                               '%C2%A3'),
        ('%C2%A3',                          '%C2%A3'),
        ('%c2%a3',                          '%C2%A3'),

        ('あ',                              '%E3%81%82'),
        ('%E3%81%82',                       '%E3%81%82'),
        ('%e3%81%82',                       '%E3%81%82'),

        # invalid percent encoding characters
        ('%pp',                             '%25pp'),
        ('%25pp',                           '%25pp'),
        ('%--',                             '%25--'),
        ('%25--',                           '%25--'),
        ('%<<',                             '%25%3C%3C'),
        ('%25%3C%3C',                       '%25%3C%3C'),
        ('%%%',                             '%25%25%25'),
        ('%25%25%25',                       '%25%25%25'),

        # RFC 6874 (nothing special)
        ('[fe80::a%en1]',                   '[fe80::a%25en1]'),
        ('[fe80::a%25en1]',                 '[fe80::a%25en1]'),
    )
    for url, expected in tests:
        assert urlno.requote(url) == expected


def test_get_relative_reference():
    tests = (
        ('http://h/',       'http://h/',        ''),

        ('http://h/p',      'http://h/',        'p'),
        ('http://h/p/',     'http://h/',        'p/'),

        ('http://h/',       'http://h/p',       '.'),
        ('http://h/',       'http://h/p/',      '../'),

        ('http://h/p',      'http://h/p',       ''),
        ('http://h/p',      'http://h/p/',      '../p'),  # gray zone
        ('http://h/p/',     'http://h/p',       'p/'),
        ('http://h/p/',     'http://h/p/',      ''),

        ('http://h/p',      'http://h/p2',      'p'),
        ('http://h/p',      'http://h/p2/',     '../p'),
        ('http://h/p/',     'http://h/p2',      'p/'),
        ('http://h/p/',     'http://h/p2/',     '../p/'),

        ('http://h/p/p1',   'http://h/p',       'p/p1'),
        ('http://h/p/p1',   'http://h/p/',      'p1'),
        ('http://h/p/p1/',  'http://h/p',       'p/p1/'),
        ('http://h/p/p1/',  'http://h/p/',      'p1/'),

        ('http://h/p',      'http://h/p/p2',    '../p'),  # gray zone
        ('http://h/p',      'http://h/p/p2/',   '../../p'),  # gray zone
        ('http://h/p/',     'http://h/p/p2',    '.'),
        ('http://h/p/',     'http://h/p/p2/',   '../'),

        ('http://h/p/p1',   'http://h/p/p2',    'p1'),
        ('http://h/p/p1',   'http://h/p/p2/',   '../p1'),
        ('http://h/p/p1/',  'http://h/p/p2',    'p1/'),
        ('http://h/p/p1/',  'http://h/p/p2/',   '../p1/'),
    )
    # verify using 'urllib.parse.urljoin'
    for url, baseurl, expected in tests:
        ret =  urllib.parse.urljoin(baseurl, expected)
        assert ret == url

    # test
    for url, baseurl, expected in tests:
        assert urlno.get_relative_reference(url, baseurl) == expected


def test_get_relative_reference_from_rfc3986_normal_examples():
    # the examples are not supposed to be used this way (opposite direction),
    # so we need to cheat a bit.
    def normalize(url, expected):
        if expected.startswith('//'):
            expected = 'http:' + expected
        if expected.startswith('/'):
            expected = '../..' + expected
        if expected == './g':
            expected = 'g'
        # Last segments ('.' and './') and ('..' and '../') are equivalent.
        # So we need to 'normalize' in one way or the other.
        if url.endswith('./'):
            url = url[:-1]
        if expected.endswith('./'):
            expected = expected[:-1]
        return url, expected

    baseurl = rfc3986_baseurl
    for m in rfc3986_normal_examples:
        url = m.group(2)
        expected = m.group(1)
        url = urlno.get_relative_reference(url, baseurl)
        url, expected = normalize(url, expected)
        assert url == expected


def test_remove_dot_segments():
    tests = (
        ('',                    ''),
        ('.',                   ''),
        ('..',                  ''),
        ('...',                 '...'),

        ('/',                   '/'),
        ('./',                  ''),
        ('../',                 ''),
        ('.../',                '.../'),

        ('/./',                 '/'),
        ('/../',                '/'),
        ('/.../',               '/.../'),

        ('./.',                 ''),
        ('./..',                ''),
        ('../.',                ''),
        ('../..',               ''),
        ('././',                ''),
        ('./../',               ''),
        ('.././',               ''),
        ('../../',              ''),

        ('/./.',                '/'),
        ('/./..',               '/'),
        ('/../.',               '/'),
        ('/../..',              '/'),
        ('/././',               '/'),
        ('/./../',              '/'),
        ('/.././',              '/'),
        ('/../../',             '/'),

        ('./foo',               'foo'),
        ('../foo',              'foo'),
        ('/./foo',              '/foo'),
        ('/../foo',             '/foo'),

        ('/foo/.',              '/foo/'),
        ('/foo/..',             '/'),
        ('/foo/./',             '/foo/'),
        ('/foo/../',            '/'),

        ('/foo/./.',            '/foo/'),
        ('/foo/./..',           '/'),
        ('/foo/../.',           '/'),
        ('/foo/../..',          '/'),
        ('/foo/././',           '/foo/'),
        ('/foo/./../',          '/'),
        ('/foo/.././',          '/'),
        ('/foo/../../',         '/'),

        ('/foo/./bar',          '/foo/bar'),
        ('/foo/../bar',         '/bar'),

        ('/.foo',               '/.foo'),
        ('/..foo',              '/..foo'),
        ('/foo.',               '/foo.'),
        ('/foo..',              '/foo..'),

        # urlsplit('//') -> ('', '', '', '', '')
        # ('//',                  '//'),

        ('//foo/bar',           '//foo/bar'),
        ('foo//bar',            'foo//bar'),
        ('foo/bar//',           'foo/bar//'),

        # ('///foo/bar',          '///foo/bar'),  # -> '/foo/bar'
        ('foo///bar',           'foo///bar'),
        ('foo/bar///',          'foo/bar///'),

        ('foo/.',               'foo/'),
        ('foo/./',              'foo/'),
        ('foo//.',              'foo//'),
        ('foo//./',             'foo//'),

        # TODO: investigate
        ('foo/..',              '/'),
        ('foo/../',             '/'),
    )

    for path, expected in tests:
        assert urlno.remove_dot_segments(path) == expected


class Test_URLNormalization:

    def compare(self, url, expected):
        u = urlno.URL(url)
        assert u.url == expected

    def test_case_normalization(self):
        tests = (
            ('http://example.com/%3a',      'http://example.com/%3A'),
            ('HTTP://WWW.EXAMPLE.COM/',     'http://www.example.com/'),
            ('http://User@example.com/',    'http://User@example.com/'),
            # ('http://[fe80::a%25En1]/',      'http://[fe80::a%25En1]/'),
            ('http://example.com/A',        'http://example.com/A'),
        )

        for url, expected in tests:
            self.compare(url, expected)

    def test_http_scheme_normalization(self):
        tests = {
            ('http://@example.com/',        'http://@example.com/'),
            ('http://example.com',          'http://example.com/'),
            ('http://example.com:/',        'http://example.com/'),
            ('http://example.com:80/',      'http://example.com/'),
            ('http://example.com:8000/',    'http://example.com:8000/'),

            # https://bugs.python.org/issue22852
            # ('http://example.com/?',        'http://example.com/?'),
            # ('http://example.com/#',        'http://example.com/#'),
        }

        for url, expected in tests:
            self.compare(url, expected)
