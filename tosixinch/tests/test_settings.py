
import argparse
import os
import sys  # noqa: F401

import pytest

import tosixinch.settings


class TestParse:

    @pytest.fixture(scope='class')
    def conf(self):
        test_dir = os.path.dirname(__file__)
        config_dir = os.path.join(test_dir, 'res', 'config')
        # os.environ['TOSIXINCH_USERDIR'] = test_dir
        args = argparse.Namespace()
        args.nouserdir = None
        args.userdir = config_dir
        rsrcs = (
            'http://bbb.com/ttt/xxx#yyy',
        )
        return tosixinch.settings.Conf(rsrcs, args=args)

    @pytest.fixture(scope='class')
    def site(self, conf):
        return [site for site in conf.sites][0]

    def test_parse_encode(self, conf):
        encode_value = ['aaa', 'bbb', 'ccc']
        assert conf.general.encoding == encode_value

    def test_parse_pdfname(self, conf):
        assert conf.pdfname == 'bbb-xxx.pdf'

    def test_parse_efile(self, site):
        efile_value = '_htmls/bbb.com/ttt/xxx'
        assert site.efile == efile_value

    def test_parse_select(self, site):
        select_value = '//div[@id="title"]|//div[@id="article"]'
        assert site.select == select_value

    def test_parse_exclude(self, site):
        exclude_value = '//div[@class="side"]'
        assert site.exclude == exclude_value

    def test_parse_cnvopts(self, conf):
        opts = ['--javascript',
            '--font', 'DejaVu Sans Mono', '-A', '1', '-B', '2']
        assert conf.converter.cnvopts == opts


class TestPDFName:

    def compare(self, rsrc, section, length, pdfname):
        f = tosixinch.settings._getpdfname
        assert f(rsrc, section, length) == pdfname

    def test(self):
        # for pdfname, we assume an rsrc always has top level domain.
        rsrc = 'https://aaa'
        with pytest.raises(ValueError):
            self.compare(rsrc, 'x', 1, 'x-aaa.pdf')

        rsrc = 'https://aaa.com'
        self.compare(rsrc, 'x', 1, 'x-aaa.pdf')
        rsrc = 'https://aaa.com/'
        self.compare(rsrc, 'x', 1, 'x-aaa.pdf')
        rsrc = 'https://aaa.com//'
        self.compare(rsrc, 'x', 1, 'x-aaa.pdf')
        rsrc = 'https://aaa.com/bbb.txt'
        self.compare(rsrc, 'x', 1, 'x-bbb.txt.pdf')
        rsrc = 'https://aaa.com/bbb.txt'
        self.compare(rsrc, 'x', 2, 'x.pdf')

        # with querry
        rsrc = 'https://aaa.com/bbb?s=3+t=5&u=7+8'
        self.compare(rsrc, 'x', 1, 'x-bbb-s-3-t-5-u-7-8.pdf')
