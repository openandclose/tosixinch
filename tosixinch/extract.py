
"""Prepare html content before PDF conversion.

* (load file and decode)
* (if text is not html, delegate to textformat.py)
* select the main content parts
* strip undesirable parts in them
* process (call arbitrary functions) accoding to site specific settings
* download inner components (images) only in the stripped content
* clean up (call ``clean.py``)
* save the content to utf-8 file.
"""

import copy
import importlib
import logging
import os
import sys
import urllib.parse

from tosixinch import _ImportError
from tosixinch import clean
from tosixinch import download
from tosixinch import location
from tosixinch import process
from tosixinch import system
from tosixinch import textformat
from tosixinch.util import (
    build_new_html, build_blank_html,
    check_ftype, iter_component, xpath_select,
    get_component_size)

try:
    import readability
except ImportError:
    readability = _ImportError('readability')

logger = logging.getLogger(__name__)


class Extract(object):
    """Main class bundling all functionarities in this modeule."""

    def __init__(self, conf, site, text):
        self._conf = conf
        self._appconf = conf._appconf
        self._site = site
        self.text = text

        self.url = site.url
        self.fname = site.fname
        self.fnew = site.fnew
        self.sel = site.select
        self.excl = site.exclude
        self.sp = site.general.preprocess + site.process
        self.section = site.section

        self._guess = conf.general.guess
        self._encoding = site.general.encoding
        self._parts_download = site.general.parts_download
        self._force_download = site.general.force_download
        self._full_image = site.general.full_image

        system.userpythondir_init(self._conf._userdir)

    def load(self):
        reader = system.HtmlReader(
            self.fname, text=self.text, codings=self._encoding)
        self.root = reader.read()

    def prepare(self):
        title = self.root.xpath('//title/text()')
        title = title[0] if title else 'notitle'
        baseurl = self.root.base or self.url
        logger.debug('[base url] %s', baseurl)

        doctype = self.root.getroottree().docinfo.doctype
        doc = build_blank_html(doctype)
        head = self.root.head
        if head is not None:
            doc.insert(0, copy.deepcopy(head))
        # or
        # doc = copy.deepcopy(self.root)
        # doc.body.clear()

        self.title = title
        self.baseurl = baseurl
        self.doctype = doctype
        self.doc = doc

    def select(self):
        if self.sel == '':
            self.sel = self.guess_selection() or '*'

        for t in xpath_select(self.root.body, self.sel):
            self.doc.body.append(t)

    def exclude(self):
        if self.excl:
            for t in xpath_select(self.doc.body, self.excl):
                if t.getparent() is not None:
                    t.getparent().remove(t)

    def process(self):
        for s in self.sp:
            system.apply_function(self.doc, s)

    def components(self):
        if self._parts_download:
            self.get_components()

    def cleanup(self):
        tags = self._site.general.add_clean_tags
        attrs = self._site.general.add_clean_attrs

        cleaner = clean.Clean(self.doc, tags, attrs)
        cleaner.run()

    def write(self):
        writer = system.HtmlWriter(
            self.fnew, doc=self.doc, doctype=self.doctype)
        writer.write()

    def readability_select(self):
        title = readability.Document(self.root).title()
        content = readability.Document(self.root).summary(html_partial=True)

        # ``Readability`` generally does not care about main headings.
        # So we manually insert a probable ``title``.
        doc = build_new_html(title, content)
        heading = doc.xpath('//h1')
        if len(heading) == 0:
            process.gen.add_title(doc)
        if len(heading) > 1:
            process.gen.decrease_heading(doc)
            process.gen.add_title(doc)

        self.doc = doc

    def run(self):
        self.load()
        self.prepare()
        self.select()
        self.exclude()
        self.process()
        self.components()
        self.cleanup()
        self.write()

    def readability_run(self):
        self.load()
        self.readability_select()
        self.components()
        self.write()

    def guess_selection(self):
        guesses = self._guess
        for guess in guesses:
            s = xpath_select(self.root, guess)
            if s and len(s) == 1:
                return guess
        return None

    # cf. Embedded contents are:
    #         audio, canvas, embed, iframe, img, math, object, svg, video
    # https://www.w3.org/TR/html5/dom.html#embedded-content-2
    def get_components(self):
        for el, url in iter_component(self.doc):
            self._get_component(el, url)

    def _get_component(self, el, url):
        comp = location.Component(url, self)
        url = comp.url
        src = comp.component_url
        fname = comp.component_fname
        el.attrib['src'] = src
        self._download_component(url, fname)
        self._add_component_attributes(el, fname)

    def _download_component(self, url, fname):
        if not os.path.exists(fname) or self._force_download:
            logger.info('[img] %s', url)
            system.make_directories(fname)
            try:
                download.download(url, fname)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    logger.info('[HTTPError 404 %s] %s' % (e.reason, url))
                else:
                    logger.warning(
                        '[HTTPError %s %s %s] %s' % (
                            e.code, e.reason, e.headers, url))
            except urllib.error.URLError as e:
                logger.warning('[URLError %s] %s' % (e.reason, url))

    def _add_component_attributes(self, el, fname):
        full = int(self._full_image)
        w, h = get_component_size(el, fname)
        if w and h:
            length = max(w, h)
            if length >= full:
                ratio = h / w
                if ratio > self._conf.pdfratio:
                    el.classes.add('tsi-tall')
                else:
                    el.classes.add('tsi-wide')


def run(conf):
    for site in conf.sites:
        fname = site.fname
        ftype, kind, text = check_ftype(fname, codings=site.general.encoding)
        if ftype == 'html':
            _run(conf, site, text)
        else:
            textformat.dispatch(conf, site, ftype, kind, text)


def _run(conf, site, text):
    extractor = conf.general.extractor
    extract = Extract(conf, site, text)
    if extractor == 'lxml':
        extract.run()
    elif extractor == 'readability':
        if site.section == 'scriptdefault':
            extract.readability_run()
        else:
            extract.run()
    elif extractor == 'readability_only':
        extract.readability_run()
