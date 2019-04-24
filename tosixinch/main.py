#!/usr/bin/env python

"""A Python3 script to help convert html to pdf.

Example:
$ tosixinch -i https://en.wikipedia.org/wiki/Xpath -1
    download(1) (i)nput url.

$ tosixinch -123
    download(1), extract(2), and convert(3) urls,
    reading from 'urls.txt' in current directory.
    no '--input' and no '--file' defaults to this file.
"""


import argparse
import logging
import os
import sys
import webbrowser

from tosixinch import _set_verbose
from tosixinch import configfetch
from tosixinch import download
from tosixinch import extract
from tosixinch import convert
from tosixinch import link
from tosixinch import news
from tosixinch import settings
from tosixinch import toc
from tosixinch.util import runcmd

logger = logging.getLogger(__name__)

ENVS = {'userdir': 'TOSIXINCH_USERDIR'}

DEFAULT_UFILE = 'urls.txt'


# For argument parser object:
# To pass only config-related arguments on to `configfetch`,
# the object is divided in commandline part and configuration part.
# To display arguments in more meaningful grouping,
# the parts are also divided in multiple argument groups.

def _build_cmd_parser():
    parser = argparse.ArgumentParser(prog='tosixinch-cmd', add_help=False)
    general = parser.add_argument_group('general')
    actions = parser.add_argument_group('actions')

    # general group
    help = 'input url or file path. it can be specified multiple times'
    general.add_argument('-i', '--input', action='append', help=help)

    help = "file to read inputs. only one file"
    general.add_argument('-f', '--file', default=DEFAULT_UFILE, help=help)

    help = 'show this help message and exit'
    general.add_argument('-h', '--help', action='store_true', help=help)

    help = 'print out more detailed log messages'
    general.add_argument('-v', '--verbose', action='store_true', help=help)

    # actions group
    help = 'download by default downloader'
    actions.add_argument('-1', '--download', action='store_true', help=help)

    help = 'extract by default extractor'
    actions.add_argument('-2', '--extract', action='store_true', help=help)

    help = 'convert by default converter'
    actions.add_argument('-3', '--convert', action='store_true', help=help)

    help = 'open a pdf viewer if configured'
    actions.add_argument('-4', '--view', action='store_true', help=help)

    help = 'print application settings after command line evaluation, and exit'
    actions.add_argument('-a', '--appcheck', action='store_true', help=help)

    help = 'open (first) extracted html in browser and exit'
    actions.add_argument('-b', '--browser', action='store_true', help=help)

    help = ('print matched url settings and exit '
            '(so you have to supply url some way)')
    actions.add_argument('-c', '--check', action='store_true', help=help)

    help = "create toc htmls and a toc url list. conflicts with '--input'."
    actions.add_argument('--toc', action='store_true', help=help)

    help = 'get links in documents from urls (experimental)'
    actions.add_argument('--link', action='store_true', help=help)

    choices = ['hackernews']
    help = 'fetch urls from socialnews site (experimental)'
    actions.add_argument('--news', choices=choices, help=help)

    help = 'generate a sample pdf'
    actions.add_argument('--sample-pdf', action='store_true', help=help)

    # TODO: '--printout' prints urls, fnames, fnews etc...

    return parser


def _build_conf_parser():
    parser = argparse.ArgumentParser(
        prog='tosixinch-conf', allow_abbrev=False, add_help=False)
    programs = parser.add_argument_group('programs')
    configs = parser.add_argument_group('configs')
    styles = parser.add_argument_group('styles')

    # programs group
    help = 'download by urllib (default, and no other option)'
    programs.add_argument(
        '--urllib', action='store_const',
        const='urllib', dest='downloader', help=help)

    help = 'extract by lxml (default)'
    programs.add_argument(
        '--lxml', action='store_const',
        const='lxml', dest='extractor', help=help)

    help = 'extract by readability, if no settings matched'
    programs.add_argument(
        '--readability', action='store_const',
        const='readability', dest='extractor', help=help)

    help = 'extract by readability unconditionally'
    programs.add_argument(
        '--readability-only', action='store_const',
        const='readability_only', dest='extractor', help=help)

    help = 'convert by princexml'
    programs.add_argument(
        '--prince', action='store_const',
        const='prince', dest='converter', help=help)

    help = 'convert by weasyprint'
    programs.add_argument(
        '--weasyprint', action='store_const',
        const='weasyprint', dest='converter', help=help)

    help = 'convert by wkhtmltopdf'
    programs.add_argument(
        '--wkhtmltopdf', action='store_const',
        const='wkhtmltopdf', dest='converter', help=help)

    help = 'convert by ebook-convert'
    programs.add_argument(
        '--ebook-convert', action='store_const',
        const='ebook_convert', dest='converter', help=help)

    # configs group
    help = ('set http header user-agent when downloading by urllib '
            '(to see the default, run --appcheck)')
    configs.add_argument('--user-agent', help=help)

    choices = ['webengine', 'webkit']
    help = 'use either webengine or webkit (default) when running Qt'
    configs.add_argument(
        '--qt', choices=choices, help=help)

    help = ('if there is no matched url, '
            'use this xpath for content selection [LINE]')
    configs.add_argument('--guess', help=help)

    # Toggling is difficult, see Paul Jacobson (hpaulj)'s explanation.
    # https://stackoverflow.com/a/34750557
    help = (
        'download components (images etc.) '
        'before PDF conversion (default)')
    configs.add_argument(
        '--parts-download', action='store_const',
        const='yes', help=help)

    help = 'not download components before PDF conversion'
    configs.add_argument(
        '--no-parts-download', action='store_const',
        const='no', dest='parts_download', help=help)

    help = 'add or subtract to-skip-binaries-extension list [PLUS]'
    configs.add_argument('--add-binary-extensions', help=help)

    help = 'add or subtract to-delete-tag list [PLUS]'
    configs.add_argument('--add-clean-tags', help=help)

    help = 'add or subtract to-delete-attribute list [PLUS]'
    configs.add_argument('--add-clean-attrs', help=help)

    help = ('use input paths as is '
            '(no url transformation, and only for local files)')
    configs.add_argument(
        '--raw', action='store_const', const='yes', help=help)

    help = ('force --download or --parts-download '
            'even if the file already exists')
    configs.add_argument(
        '--force-download', action='store_const', const='yes', help=help)

    help = 'width (character numbers) for rendering non-prose text'
    configs.add_argument('--textwidth', help=help)

    help = 'line continuation marker for rendering non-prose text'
    configs.add_argument('--textindent', help=help)

    help = 'commandline string to open the pdf viewer [CMD]'
    configs.add_argument('--viewcmd', help=help)

    help = 'override user configuration directory'
    configs.add_argument('--userdir', help=help)

    help = 'do not parse user configuration (intended for testing)'
    configs.add_argument('--nouserdir', action='store_true', help=help)

    help = 'override pdf file name'
    configs.add_argument('--pdfname', help=help)

    help = ('override the converter executable path. '
            'you also need to set the converter itself')
    configs.add_argument('--cnvpath', help=help)

    # styles group
    choices = ['portrait', 'landscape']
    help = ('portrait(default) or landscape, determine which size data to use')
    styles.add_argument('--orientation', choices=choices, help=help)

    help = "portrait size for the css, e.g. '90mm 118mm'"
    styles.add_argument('--portrait-size', help=help)

    help = "landscape size for the css, e.g. '118mm 90mm'"
    styles.add_argument('--landscape-size', help=help)

    help = 'tree depth of table of contents (only for prince and weasyprint)'
    styles.add_argument('--toc-depth', help=help)

    help = """main font for the css, e.g. '"DejaVu Sans", sans-serif'"""
    styles.add_argument('--font-family', help=help)

    help = 'monospace font for the css'
    styles.add_argument('--font-mono', help=help)

    help = 'serif font for the css (not used by sample)'
    styles.add_argument('--font-serif', help=help)

    help = 'sans font for the css (not used by sample)'
    styles.add_argument('--font-sans', help=help)

    help = "main font size for the css, e.g. '9px'"
    styles.add_argument('--font-size', help=help)

    help = 'monospace font size for the css'
    styles.add_argument('--font-size-mono', help=help)

    help = "'adjust spaces between lines, number like '1.3'"
    styles.add_argument('--line-height', help=help)

    help = 'number like 1.5 to scale font sizes (not yet used by sample)'
    styles.add_argument('--font-scale', help=help)

    return parser


def _build_parser():
    """Build `argparse.ArgumentParser` object."""
    parsers = (_build_cmd_parser(), _build_conf_parser())
    parser = argparse.ArgumentParser(
        prog='tosixinch', description=__doc__,
        add_help=False, parents=parsers,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    return parser


def _main(args=sys.argv[1:], conf=None):
    """Parse commandline arguments and run accordingly.

    note:
        With 'allow_abbrev=False',
        it cannot parse concatenated short options. (e.g. '-123')
        http://bugs.python.org/issue26967

        And when 'allow_abbrev=True',
        you have to take care not to include similar named options
        in partial parsing, in which
        'unknown' options might be interpreted as 'unambiguous' options.
    """
    parser = _build_parser()

    if not args:
        usage(parser)

    _args = configfetch.minusadapter(parser, matcher='--add-.+', args=args)
    args = parser.parse_args(_args)

    conf_parser = _build_conf_parser()
    confargs, _ = conf_parser.parse_known_args(_args)

    if args.help:
        usage(parser)

    if args.verbose:
        _set_verbose()

    # (to debug logging messages)
    # import logging_tree
    # logging_tree.printout()
    # return

    # This script, by design, doesn't hold any state between each jobs
    # (download, extract, etc.).
    # As an compensation,
    # it may use the first line in 'urls.txt' for communication.
    # Some special magic words do some special things.
    # It is commented out, machine generated,
    # so users don't have to care most of the times.
    firstline = None

    urls = args.input
    ufile = None if urls else args.file

    if conf is None:
        conf = settings.Conf(urls, ufile, args=confargs, envs=ENVS)
    setv = conf.general.set_value

    # When handling urls the `news` module built,
    # (with various source sites and comments),
    # it is better to use `readability`.
    if firstline == news.FL_SOCIALNEWS:
        setv('extractor', 'readability')

    if args.appcheck:
        conf.print_appconf()
        return
    elif args.news:
        ret = news.socialnews(args.news)
        print(ret)
        return
    elif args.sample_pdf:
        import tosixinch.tests._test_actualrun2 as test_run
        test_run.sample_run(conf)
        return

    if not conf.sites.urls:
        if ufile == DEFAULT_UFILE:
            fmt = ('urls are not supplied. '
                'use --input, --file or %r (default ufile).')
            raise ValueError(fmt % DEFAULT_UFILE)
        else:
            raise ValueError('File not found: %r' % ufile)

    if args.browser:
        html = list(conf.sites)[0].fnew
        if not os.path.exists(html):
            logger.error(
                'File not found: no extracted html')
        else:
            webbrowser.open(html)
        return
    if args.check:
        conf.print_siteconf()
        return
    if args.link:
        link.print_links(conf)
        return

    if args.download:
        runcmd(conf, conf.general.precmd1)
        download.run(conf)
        runcmd(conf, conf.general.postcmd1)
    if args.extract:
        runcmd(conf, conf.general.precmd2)
        extract.run(conf)
        runcmd(conf, conf.general.postcmd2)
    if args.toc:
        toc.run(conf)
    if args.convert:
        runcmd(conf, conf.general.precmd3)
        convert.run(conf)
        runcmd(conf, conf.general.postcmd3)
    if args.view:
        runcmd(conf, conf.general.viewcmd)

    return conf


def main():
    ret = _main()  # noqa F841 variable not used


def usage(parser):
    parser.print_help()
    sys.exit()


if __name__ == "__main__":
    main()
