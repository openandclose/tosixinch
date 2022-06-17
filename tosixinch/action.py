
"""Provide abstract action processes and classes."""

import logging
import os
import random
import time

from tosixinch import cached_property
from tosixinch import location
from tosixinch import lxml_html
from tosixinch import stylesheet
from tosixinch import system

logger = logging.getLogger(__name__)


class _File(object):
    """Common object for Reader and Writer."""

    SUFFIX_ORIG = '.orig'


class DownloadWriter(_File, system.DownloadWriter):
    """Forward to dfile."""

    def get_filename(self):
        fname = self.fname
        orig = fname + self.SUFFIX_ORIG
        if os.path.isfile(orig):
            return orig
        return fname

    def write(self):
        fname = self.get_filename()
        super().write(fname)


class ExtractReader(_File, system.Reader):
    """Forward to dfile."""

    def get_filename(self):
        fname = self.fname
        orig = fname + self.SUFFIX_ORIG
        if os.path.isfile(orig):
            return orig
        return super().get_filename()


class _ExtractWriter(_File):
    """Base class of ExtractWriter and HtmlExtractWriter."""

    def set_filename(self):
        fname = self.fname
        orig = fname + self.SUFFIX_ORIG
        if os.path.isfile(fname) and not os.path.isfile(orig):
            os.replace(fname, orig)


class ExtractWriter(_ExtractWriter, system.Writer):
    """Move dfile, before writing."""

    def _prepare(self):
        super()._prepare()
        self.set_filename()


class HtmlExtractWriter(_ExtractWriter, lxml_html.HtmlWriter):
    """Use lxml_html.Writer."""

    def _prepare(self):
        super()._prepare()
        self.set_filename()


class Action(object):
    """Provide basic attributes and methods for action type."""

    def __init__(self, conf, site):
        self._conf = conf
        self._site = site

        self.url = site.url
        self.dfile = site.dfile
        self.efile = site.efile

        self.codings = site.general.encoding
        self.errors = site.general.encoding_errors

    def _parse(self, name, text=None):
        return lxml_html.read(
            name, text, codings=self.codings, errors=self.errors)


class Downloader(Action):
    """Provide basic downloading capability."""

    def check_url(self, site):
        if site.is_local:
            url = site.url
            if not os.path.exists(url):
                raise FileNotFoundError('[url] File not found: %r' % url)
            if os.path.isdir(url):
                raise IsADirectoryError('[url] Got directory name: %r' % url)
            return True
        return False

    def check_dfile(self, site):
        """Check if downloading is necessary (done).

        True:  not necessary
        False: necessary
        """
        if self.check_url(site):
            return True

        dfile = site.dfile
        force = self._site.general.force_download
        cache = self._conf._cache.download

        if os.path.exists(dfile):
            if not force:
                return True
            else:
                if cache and cache.get(dfile):
                    return True

        if cache:
            cache[dfile] = 1
        return False

    def request(self, site, on_error_exit=True):
        url = site.idna_url
        user_agent = self._site.general.user_agent
        cookies = self._site.cookie
        timeout = self._site.general.timeout

        self.agent = system.request(
            url, user_agent=user_agent, cookies=cookies,
            timeout=timeout, on_error_exit=on_error_exit)

    def process(self):
        for p in self._site.general.dprocess:
            system.run_function(self._conf._userdir, 'dprocess', self.agent, p)

    def retrieve(self, on_error_exit=True):
        self.text = system.retrieve(self.agent, on_error_exit=on_error_exit)

    def sleep(self, site):
        i = site.general.interval
        i = i * (1 + 0.5 * random.random() ** 2)
        time.sleep(i)

    def write(self, name, text):
        return DownloadWriter(name, text).write()

    def download(self):
        if self.check_dfile(self._site):
            return

        self.request(self._site)
        self.process()
        self.retrieve()
        self.write(self.dfile, self.text)
        self.sleep(self._site)


class CompDownloader(Downloader):
    """Provide component downloading capability."""

    def write(self, name, text):
        return system.DownloadWriter(name, text).write()  # no Forwarding

    def download(self, comp):
        if self.check_dfile(comp._cls):
            return

        self.request(comp, on_error_exit=False)
        if self.agent is None:  # URLError or HTTPError
            return
        self.retrieve(on_error_exit=False)
        if self.text:
            self.write(comp.dfile, self.text)
            self.sleep(comp._parent_cls)


class TextFormatter(Action):
    """Provide common extraction methods for html and non-html."""

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
            url = location.path2ref(cssfile, self.efile)
            sheets.append(url)
        return sheets

    def get_css_reference(self):
        for sheet in self.stylesheets:
            yield self.CSS_REF % sheet

    def write(self, name, text):
        return ExtractWriter(name, text).write()


class Extractor(TextFormatter):
    """Provide basic extraction methods for html."""

    def parse(self):
        return lxml_html.read(
            self.dfile, self.text, codings=self.codings, errors=self.errors)

    def _add_css_elememnt(self, doc):
        for url in self.get_css_reference():
            el = lxml_html.fragment_fromstring(url)
            doc.head.append(el)

    def add_css_elememnt(self):
        self._add_css_elememnt(self.doc)

    def write(self, doc):
        overwrite = self._conf.general.overwrite_html
        if overwrite:
            return lxml_html.HtmlWriter(self.efile, doc).write()
        else:
            return HtmlExtractWriter(self.efile, doc).write()


class CSSWriter(Extractor):
    """Open html file and add css reference."""

    def read_and_write(self):
        doc = self._parse(self.efile)
        self._add_css_elememnt(doc)
        self.write(doc=doc)
