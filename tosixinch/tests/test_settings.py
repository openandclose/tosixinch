
import argparse
import os
import sys

# sys.path.insert(0, os.path.abspath(__file__ + '/../..'))
# print(sys.path)

import pytest  # noqa: F401

import tosixinch.settings


class TestParse:

    @pytest.fixture(scope='class')
    def conf(self):
        test_dir = os.path.dirname(__file__)
        test_dir = os.path.join(test_dir, 'res', 'config')
        # os.environ['TOSIXINCH_USERDIR'] = test_dir
        args = argparse.Namespace()
        args.userdir = test_dir
        urls = (
            'http://bbb.com/ttt/xxx#yyy',
            )
        return tosixinch.settings.Conf(urls, args=args)

    @pytest.fixture(scope='class')
    def site(self, conf):
        return [site for site in conf.sites][0]

    def test_parse_encode(self, conf):
        encode_value = ['aaa', 'bbb', 'ccc']
        assert conf.general.encoding == encode_value

    def test_parse_pdfname(self, conf):
        assert conf.pdfname == 'bbb-xxx.pdf'

    def test_parse_fnew(self, site):
        # fnew_value = '_htmls/bbb.com/ttt/xxx#yyy~.html'
        fnew_value = '_htmls/bbb.com/ttt/xxx/_~.html'
        assert site.fnew == fnew_value

    def test_parse_select(self, site):
        select_value = '//div[@id="title"]|//div[@id="article"]'
        assert site.select == select_value

    def test_parse_exclude(self, site):
        exclude_value = '//div[@class="side"]'
        assert site.exclude == exclude_value

    def test_parse_cnvopts(self, conf):
        opts = ['--javascript', '--font', 'DejaVu Sans Mono', '-A', '1', '-B', '2']
        assert conf.converter.cnvopts == opts


class TestPDFName:

    def compare(self, url, section, length, pdfname):
        f = tosixinch.settings._getpdf
        assert f(url, section, length) == pdfname

    def test(self):
        # for pdfname, we assume an url always has top level domain.
        url = 'https://aaa'
        with pytest.raises(ValueError):
            self.compare(url, 'x', 1, 'x-aaa.pdf')

        url = 'https://aaa.com'
        self.compare(url, 'x', 1, 'x-aaa.pdf')
        url = 'https://aaa.com/'
        self.compare(url, 'x', 1, 'x-aaa.pdf')
        url = 'https://aaa.com//'
        self.compare(url, 'x', 1, 'x-aaa.pdf')
        url = 'https://aaa.com/bbb.txt'
        self.compare(url, 'x', 1, 'x-bbb.txt.pdf')
        url = 'https://aaa.com/bbb.txt'
        self.compare(url, 'x', 2, 'x.pdf')

        # with querry
        url = 'https://aaa.com/bbb?s=3+t=5&u=7+8'
        self.compare(url, 'x', 1, 'x-bbb-s3t5u78.pdf')
