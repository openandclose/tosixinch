
"""Provide abstract action processes and classes."""

import logging
import re

from tosixinch import cached_property
from tosixinch import location
from tosixinch import lxml_html
from tosixinch import stylesheet
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


def _action_run(conf, command, precomd, postcmd):
    try:
        returncode = system.run_cmds(precomd, conf)
        if returncode not in (101, 102):
            command(conf)
        if returncode not in (102,):
            system.run_cmds(postcmd, conf)
    finally:
        _run_cleanup()


def _action_dispatch(conf, command,
        precomd, postcmd, pre_each_cmd, post_each_cmd):

    command = _sub_action_dispatch(conf, command, pre_each_cmd, post_each_cmd)
    _action_run(conf, command, precomd, postcmd)


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


def _is_html(fname, text, max_chars=4096):
    if _HTMLFILE.match(text[:max_chars]):
        return True
    return False


def _get_ftypes(conf):
    for site in conf.sites:
        site.ftype = site.general.ftype.lower()
        if site.ftype:
            continue

        if _is_html(site.fname, site.text):
            site.ftype = 'html'


def _extract(conf):
    _get_ftypes(conf)

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


class Action(object):
    """Provide basic attributes and methods for action type."""

    def __init__(self, conf, site):
        self._conf = conf
        self._site = site

        self.url = site.url
        self.fname = site.fname
        self.fnew = site.fnew

        self.codings = site.general.encoding
        self.errors = site.general.encoding_errors

    def _read(self, name, text=None):
        return system.read(
            name, text, codings=self.codings, errors=self.errors)

    def _parse(self, name, text=None):
        return lxml_html.read(
            name, text, codings=self.codings, errors=self.errors)

    def _write(self, name, text):
        return system.write(name, text)


class Downloader(Action):
    """Provide basic downloading capability."""

    def _check_fname(self, site):
        force = self._site.general.force_download
        cache = self._conf._cache.download

        return site.check_fname(force=force, cache=cache)

    def request(self, site, on_error_exit=True):
        user_agent = self._site.general.user_agent
        cookies = self._site.cookie

        url = site.idna_url

        self.agent = system.request(
            url, user_agent=user_agent, cookies=cookies,
            on_error_exit=on_error_exit)

    def process(self):
        for p in self._site.general.dprocess:
            system.run_function(self._conf._userdir, 'dprocess', self.agent, p)

    def retrieve(self, on_error_exit=True):
        self.text = system.retrieve(self.agent, on_error_exit=on_error_exit)

    def download(self):
        if self._check_fname(self._site):
            return

        self.request(self._site)
        self.process()
        self.retrieve()
        self._write(self.fname, self.text)


class CompDownloader(Downloader):
    """Provide component downloading capability."""

    def download(self, comp):
        if self._check_fname(comp):
            return

        self.request(comp, on_error_exit=False)
        if self.agent is None:  # URLError or HTTPError
            return
        self.retrieve(on_error_exit=False)
        if self.text:
            self._write(comp.fname, self.text)


class TextFormatter(Action):
    """Provide common extraction methods for html and non-html."""

    # c.f. 'media="print"' does't work for wkhtmltopdf.
    CSS_REF = '<link class="tsi-css" href="%s" rel="stylesheet">'

    @property
    def text(self):
        return self._site.text

    def read(self):
        return self.text

    @cached_property
    def stylesheets(self):
        sheets = []
        cssfiles = stylesheet.StyleSheet(self._conf, self._site).stylesheets
        for cssfile in cssfiles:
            url = location.path2ref(cssfile, self.fnew)
            sheets.append(url)
        return sheets

    def get_css_reference(self):
        for sheet in self.stylesheets:
            yield self.CSS_REF % sheet


class Extractor(TextFormatter):
    """Provide basic extraction methods for html."""

    def parse(self):
        return lxml_html.read(
            self.fname, text=self.text,
            codings=self.codings, errors=self.errors)

    def _add_css_elememnt(self, doc):
        for url in self.get_css_reference():
            el = lxml_html.fragment_fromstring(url)
            doc.head.append(el)

    def add_css_elememnt(self):
        self._add_css_elememnt(self.doc)

    def write(self, doc):
        return lxml_html.write(self.fnew, doc=doc)


class CSSWriter(Extractor):
    """Open html file and add css reference."""

    def read_and_write(self):
        doc = self._parse(self.fnew)
        self._add_css_elememnt(doc)
        self.write(doc=doc)
