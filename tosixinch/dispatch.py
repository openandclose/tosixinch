
"""Dispath actions."""

import logging
import re

from tosixinch import system

logger = logging.getLogger(__name__)

_CLEANUP = []


def add_cleanup(f, *args, **kwargs):
    _CLEANUP.append([f, args, kwargs])


def _run_cleanup():
    global _CLEANUP

    for f, args, kwargs in _CLEANUP:
        f(*args, **kwargs)
    _CLEANUP = []


def _action_run(conf, command, precmd, postcmd):
    try:
        returncode = system.run_cmds(precmd, conf)
        if returncode not in (101, 102):
            command(conf)
        if returncode not in (102,):
            system.run_cmds(postcmd, conf)
    finally:
        _run_cleanup()


def _action_dispatch(conf, command,
        precmd, postcmd, pre_each_cmd, post_each_cmd):

    command = _sub_action_dispatch(conf, command, pre_each_cmd, post_each_cmd)
    _action_run(conf, command, precmd, postcmd)


def _sub_action_dispatch(conf, command, pre_each_cmd, post_each_cmd):

    def _runner(conf):
        for site in conf.sites:
            returncode = system.run_cmds(pre_each_cmd, conf, site)
            if returncode not in (101, 102):
                command(conf, site)
            if returncode not in (102,):
                returncode = system.run_cmds(post_each_cmd, conf, site)

    return _runner


def _download(conf):
    _action_dispatch(conf, _get_downloader(conf),
        conf.general.precmd1, conf.general.postcmd1,
        conf.general.pre_each_cmd1, conf.general.post_each_cmd1)


def _get_downloader(conf):
    from tosixinch import download
    return download.run


_COMMENT = r'\s*(<!--.+?-->\s*)*'
_XMLDECL = r'(<\?xml version.+?\?>)?'
_DOCTYPE = r'(<!doctype\s+.+?>)?'
_HTMLFILE = re.compile(
    '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + r'<html(|\s.+?)>',
    flags=re.IGNORECASE | re.DOTALL)


def _is_html(dfile, text, max_chars=4096):
    if _HTMLFILE.match(text[:max_chars]):
        return True
    return False


def _set_ftypes(conf):
    for site in conf.sites:
        site.ftype = site.general.ftype.lower()
        if site.ftype:
            continue

        if _is_html(site.dfile, site.text):
            site.ftype = 'html'


def _extract(conf):
    _set_ftypes(conf)

    _action_dispatch(conf, _get_extractor(conf),
        conf.general.precmd2, conf.general.postcmd2,
        conf.general.pre_each_cmd2, conf.general.post_each_cmd2)


def _get_extractor(conf):

    def _runner(conf, site):
        if site.ftype == 'html':
            from tosixinch import extract
            return extract.run(conf, site)
        else:
            from tosixinch import textformat
            return textformat.run(conf, site)

    return _runner


def _convert(conf):
    _action_run(conf, _get_converter(conf),
        conf.general.precmd3, conf.general.postcmd3)


def _get_converter(conf):
    from tosixinch import convert
    return convert.run


def main_dispatch(conf, args):

    def _toc(conf):
        from tosixinch import toc
        toc.run(conf)

    def _view(conf):
        system.run_cmds(conf.general.viewcmd, conf)

    if args.download:
        _download(conf)
    if args.extract:
        _extract(conf)
    if args.toc:
        _toc(conf)
    if args.convert:
        _convert(conf)
    if args.view:
        _view(conf)
