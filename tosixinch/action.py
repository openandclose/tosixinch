
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

    def _parse(self, name, text=None):
        return lxml_html.read(
            name, text, codings=self.codings, errors=self.errors)

    def write(self, name, text):
        return system.write(name, text)


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

    def check_fname(self, site):
        """Check if downloading is necessary (done).

        True:  not necessary
        False: necessary
        """
        if self.check_url(site):
            return True

        fname = site.fname
        force = self._site.general.force_download
        cache = self._conf._cache.download

        if os.path.exists(fname):
            if not force:
                return True
            else:
                if cache and cache.get(fname):
                    return True

        if cache:
            cache[fname] = 1
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
        return system.download_write(name, text)

    def download(self):
        if self.check_fname(self._site):
            return

        self.request(self._site)
        self.process()
        self.retrieve()
        self.write(self.fname, self.text)
        self.sleep(self._site)


class CompDownloader(Downloader):
    """Provide component downloading capability."""

    def download(self, comp):
        if self.check_fname(comp._cls):
            return

        self.request(comp, on_error_exit=False)
        if self.agent is None:  # URLError or HTTPError
            return
        self.retrieve(on_error_exit=False)
        if self.text:
            self.write(comp.fname, self.text)
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
            url = location.path2ref(cssfile, self.fnew)
            sheets.append(url)
        return sheets

    def get_css_reference(self):
        for sheet in self.stylesheets:
            yield self.CSS_REF % sheet


class Extractor(TextFormatter):
    """Provide basic extraction methods for html."""

    def parse(self):
        return self._parse(self.fname, text=self.text)

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
