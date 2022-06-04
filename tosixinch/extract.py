
"""Prepare html content before PDF conversion.

* select the main content parts
* strip undesirable parts in them
* process (call arbitrary functions) accoding to site specific settings
* download inner components (images) only in the stripped content
* clean up (call ``clean.py``)
* save the content to utf-8 file.
"""

import logging
import os

from tosixinch import _ImportError
from tosixinch import action
from tosixinch import clean
from tosixinch import content
from tosixinch import system

import tosixinch.process.sample as process_sample

try:
    import readability
except ImportError:
    readability = _ImportError('readability')

logger = logging.getLogger(__name__)


class Extract(action.Extractor):
    """Provide actual extractor with config data."""

    def __init__(self, conf, site):
        super().__init__(conf, site)

        self.sel = site.select
        self.excl = site.exclude
        self.sp = site.general.defaultprocess + site.process
        self.section = site.section

        self._parts_download = site.general.parts_download
        self._guess = conf.general.guess

    def load(self):
        self.root = self.parse()

        doctype = self.root.getroottree().docinfo.doctype
        self.doctype = doctype or content.DEFAULT_DOCTYPE
        self.baseurl = self.get_baseurl()

    def get_baseurl(self):
        base = self.root.xpath('//base[@href]')
        if base:
            baseurl = base[0].get('href')
            logger.debug('[base url] %s', baseurl)
            for b in base:
                b.drop_tree()
            return baseurl

    def build(self):
        title = self.root.xpath('//title/text()')
        title = title[0] if title else content.DEFAULT_TITLE
        self.title = title

        self.doc = content.build_new_html(doctype=self.doctype, title=title)

    def guess_selection(self):
        for guess in self._guess:
            sel = self.root.xpath(guess)
            if sel and len(sel) == 1:
                return guess

    def select(self):
        sel = self.sel or self.guess_selection() or '*'
        for t in self.root.body.xpath(sel):
            self.doc.body.append(t)

    def exclude(self):
        if self.excl:
            for t in self.doc.body.xpath(self.excl):
                if t.getparent() is not None:
                    t.getparent().remove(t)

    def process(self):
        for s in self.sp:
            system.run_function(self._conf._userdir, 'process', self.doc, s)

    def clean(self):
        tags = self._site.general.add_clean_tags
        attrs = self._site.general.add_clean_attrs
        paths = self._site.general.elements_to_keep_attrs
        cleaner = clean.Clean(self.doc, tags, attrs, paths)
        cleaner.run()

    def resolve(self, doc=None):
        if doc is None:
            doc = self.doc
        loc, locs = self._site, self._conf.sites
        baseurl, conf = self.baseurl, self._conf
        Resolver(doc, loc, locs, baseurl, conf).resolve()

    def write(self, doc=None):
        if doc is None:
            doc = self.doc
        super().write(doc)

    def run(self):
        self.load()
        self.build()
        self.select()
        self.exclude()
        self.process()
        self.clean()
        self.resolve()
        self.add_css_elememnt()
        self.write()


class KeepExtract(Extract):
    """Provide superficial extractor.

    Use input html as is, without select, clean, css-add etc.
    Only do comp-download and resolve, to make local html (fname) complete.
    """

    def run(self):
        self.load()
        self.resolve(self.root)
        self.write(self.root)


class ReadabilityExtract(Extract):
    """Define methods for readability."""

    def build(self):
        title = readability.Document(self.text).title()
        content_ = readability.Document(self.text).summary(html_partial=True)

        # ``Readability`` generally does not care about main headings.
        # So we manually insert a probable ``title``.
        doc = content.build_new_html(title=title, content=content_)
        heading = doc.xpath('//h1')
        if len(heading) == 0:
            process_sample.add_h1(doc)
        if len(heading) > 1:
            process_sample.lower_heading(doc)
            process_sample.add_h1(doc)

        self.doc = doc

    def run(self):
        self.build()
        self.resolve()
        self.add_css_elememnt()
        self.write()


class Resolver(content.Resolver):
    """Download components and rewrite links."""

    def __init__(self, doc, loc, locs, baseurl, conf):
        super().__init__(doc, loc, locs, baseurl)
        self._conf = conf

    def _get_component(self, el, comp):
        self._download_component(comp)
        self._add_component_attributes(el, comp.fname)

    def _set_component(self, comp):
        if os.path.isfile(comp.fname):
            super()._set_component(comp)

    def _download_component(self, comp):
        url = comp.url
        if url.startswith('data:image/'):
            return
        downloader = CompDownloader(self._conf, self.loc)
        downloader.download(comp)

    def _add_component_attributes(self, el, fname):
        if el.tag != 'img':
            return

        full = self.loc.general.full_image
        w, h = content.get_component_size(el, fname)
        if w and h:
            length = max(w, h)
            if length >= full:
                ratio = h / w
                if ratio > self._conf.pdfratio:
                    el.classes.add('tsi-tall')
                else:
                    el.classes.add('tsi-wide')


class CompDownloader(action.CompDownloader):
    """Add logging."""

    def request(self, comp, on_error_exit=False):
        logger.info('[img] %s', comp.url)
        super().request(comp, on_error_exit)


def run(conf, site):
    extractor = site.general.extractor

    if extractor == 'lxml':
        if conf.general.keep_html:
            runner = KeepExtract
        else:
            runner = Extract
    elif extractor == 'readability':
        if site.section == 'scriptdefault':
            runner = ReadabilityExtract
        else:
            runner = Extract
    elif extractor == 'readability_only':
        runner = ReadabilityExtract

    runner(conf, site).run()
