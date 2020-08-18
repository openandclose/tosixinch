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

from tosixinch import _set_logger
from tosixinch import action
from tosixinch import configfetch
from tosixinch import settings
from tosixinch.system import run_cmds

logger = logging.getLogger(__name__)

ENVS = {'userdir': 'TOSIXINCH_USERDIR'}

DEFAULT_UFILE = 'urls.txt'


# For argument parser object:

# To pass only config-related arguments on to `configfetch`,
# the object is divided in commandline part and configuration part.
# To display arguments in more meaningful grouping,
# the parts are also divided in multiple argument groups.

# With 'allow_abbrev=False',
# it cannot parse concatenated short options. (e.g. '-123')
# http://bugs.python.org/issue26967

# And when 'allow_abbrev=True',
# argparse tries to partial match arguments,
# and registers them if they are 'unambiguous'.
# It is inconvenient when you want to filter options
# (using ``.parse_known_args``).

def _build_cmd_parser(conf):
    parser = argparse.ArgumentParser(prog='tosixinch-cmd', add_help=False)
    build_arguments = conf._appconf.build_arguments

    general = parser.add_argument_group('general')
    build_arguments(general, '_generic')

    actions = parser.add_argument_group('actions')
    build_arguments(actions, '_action')

    return parser


def _build_conf_parser(conf):
    parser = argparse.ArgumentParser(
        prog='tosixinch-conf', allow_abbrev=False, add_help=False)
    build_arguments = conf._appconf.build_arguments

    programs = parser.add_argument_group('programs')
    build_arguments(programs, '_program')

    configs = parser.add_argument_group('configs')
    build_arguments(configs, 'general')

    styles = parser.add_argument_group('styles')
    build_arguments(styles, 'style')

    return parser


def _build_parser(conf):
    # Build `argparse.ArgumentParser` object.
    parsers = (_build_cmd_parser(conf), _build_conf_parser(conf))
    parser = argparse.ArgumentParser(
        prog='tosixinch', description=__doc__,
        add_help=False, parents=parsers,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    return parser


def _get_parser(conf=None):
    # Build `argparse.ArgumentParser` arguments.
    if conf is None:
        conf = settings.Conf(envs=ENVS)
    parser = _build_parser(conf)
    return conf, parser


def _get_conf(args, conf=None):
    # Parse commandline arguments.
    conf, parser = _get_parser(conf)

    if not args:
        usage(parser)

    _args = configfetch.minusadapter(parser, matcher='--add-.+', args=args)
    args = parser.parse_args(_args)

    conf_parser = _build_conf_parser(conf)
    confargs, _ = conf_parser.parse_known_args(_args)
    conf._appconf.set_arguments(confargs)
    conf.user_init(args)

    return conf, parser, args


def _main(args=sys.argv[1:], conf=None):
    conf, parser, args = _get_conf(args, conf)

    if args.version:
        print_version()

    if args.help:
        usage(parser)

    if args.verbose:
        _set_logger('debug')
    elif args.quiet:
        _set_logger('warning')
    else:
        _set_logger('info')

    # (to debug logging messages)
    # import logging_tree
    # logging_tree.printout()
    # return

    urls = args.input
    ufile = None if urls else args.file

    settings.ReplaceURLLoader(conf, urls=urls, ufile=ufile)()

    if args.appcheck:
        conf.print_appconf()
        return
    elif args.news:
        from tosixinch import news
        ret = news.socialnews(args.news)
        print(ret)
        return

    if not conf.sites.urls:
        if ufile == DEFAULT_UFILE:
            fmt = ('urls are not supplied. '
                'use --input, --file or %r (default ufile).')
            raise ValueError(fmt % DEFAULT_UFILE)
        else:
            raise ValueError('File not found: %r' % ufile)

    if args.browser:
        open_browser(conf)
        return
    if args.check:
        conf.print_siteconf()
        return
    if args.printout:
        conf.print_files(args.printout)
        return
    if args.link:
        from tosixinch import link
        link.print_links(conf)
        return

    action.main_dispatch(conf, args)

    return conf


def main():
    ret = _main()  # noqa F841 variable not used


def usage(parser):
    parser.print_help()
    sys.exit()


def print_version():
    vfile = os.path.join(settings._get_configdir(), '..', '..', 'VERSION')
    vfile = os.path.abspath(vfile)
    with open(vfile) as f:
        print(f.read().strip())
    sys.exit()


def open_browser(conf):
    site = list(conf.sites)[0]
    if not os.path.exists(site.fnew):
        FileNotFoundError('No extracted html to open: %r' % site.fnew)

    url = site.slash_fnew
    cmd = conf.general.browsercmd
    if cmd:
        returncode = run_cmds([cmd], conf, site)
    else:
        ret = webbrowser.open(url)
        # ret is True or False
        returncode = int(not ret)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
