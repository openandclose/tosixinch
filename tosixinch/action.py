
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


class _File(system._File):
    """Manage dfile and efile translation."""

    SUFFIX_ORIG = '.orig'

    def get_dfile(self, dfile):
        orig = dfile + self.SUFFIX_ORIG
        if os.path.isfile(orig):
            return orig
        return dfile

    def _set_dfile(self, efile):
        orig = efile + self.SUFFIX_ORIG
        efile = self.get_filename(efile)
        if os.path.isfile(efile) and not os.path.isfile(orig):
            return (efile, orig)

    def set_dfile(self, efile):
        ret = self._set_dfile(efile)
        if ret:
            efile, orig = ret
            os.replace(efile, orig)


def read(dfile, text=None, codings=None, errors='strict'):
    dfile = _File().get_dfile(dfile)
    return system.read(dfile, text, codings, errors)


class Action(_File):
    """Provide basic attributes and methods for action type."""

    def __init__(self, conf, site):
        self._conf = conf
        self._site = site

        self.rsrc = site.rsrc
        self.dfile = site.dfile
        self.efile = site.efile

        self.codings = site.general.encoding
        self.errors = site.general.encoding_errors

    def _parse(self, name, text=None):
        return lxml_html.read(
            name, text, codings=self.codings, errors=self.errors)


class Downloader(Action):
    """Provide basic downloading capability."""

    def check_rsrc(self, site):
        if site.is_local:
            path = site.rsrc
            if not os.path.exists(path):
                raise FileNotFoundError('[path] File not found: %r' % path)
            if os.path.isdir(path):
                raise IsADirectoryError('[path] Got directory name: %r' % path)
            return True
        return False

    def check_dfile(self, site):
        """Check if downloading is necessary (done).

        True:  not necessary
        False: necessary
        """
        if self.check_rsrc(site):
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

    def write(self, dfile, text):
        dfile = self.get_dfile(dfile)
        return system.download_write(dfile, text)

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
        return system.download_write(name, text)

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

    def write(self, efile, text):
        if self._site.is_remote:
            self.set_dfile(efile)
        return system.write(efile, text)


class Extractor(TextFormatter):
    """Provide basic extraction methods for html."""

    def parse(self):
        return self._parse(self.dfile, text=self.text)

    def _add_css_elememnt(self, doc):
        for htmlstr in self.get_css_reference():
            el = lxml_html.fragment_fromstring(htmlstr)
            doc.head.append(el)

    def add_css_elememnt(self):
        self._add_css_elememnt(self.doc)

    def write(self, doc):
        overwrite = self._conf.general.overwrite_html
        if self._site.is_remote and not overwrite:
            self.set_dfile(self.efile)
        return lxml_html.write(self.efile, doc=doc)


class CSSWriter(Extractor):
    """Open html file and add css reference."""

    def read_and_write(self):
        doc = self._parse(self.efile)
        self._add_css_elememnt(doc)
        self.write(doc=doc)
