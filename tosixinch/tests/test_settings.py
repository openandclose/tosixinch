
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
        assert conf.pdfname == 'xxx.pdf'

    def test_parse_fnew(self, site):
        # fnew_value = '_htmls/bbb.com/ttt/xxx#yyy--extracted.html'
        fnew_value = '_htmls/bbb.com/ttt/xxx/index--tosixinch--extracted.html'
        assert site.fnew == fnew_value

    def test_parse_select(self, site):
        select_value = '//div[@id="title"]|//div[@id="article"]'
        assert site.select == select_value

    def test_parse_exclude(self, site):
        exclude_value = '//div[@class="side"]'
        assert site.exclude == exclude_value

    def test_parse_css(self, conf):
        css_value = ['base.css', 'pconv.css']
        assert conf.converter.css == css_value

    def test_parse_cnvopts(self, conf):
        opts = ['--javascript', '--font', 'DejaVu Sans Mono', '-A', '1', '-B', '2']
        assert conf.converter.cnvopts == opts
