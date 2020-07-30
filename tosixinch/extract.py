
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

import logging

from tosixinch import content
from tosixinch import download
from tosixinch import stylesheet
from tosixinch import system
from tosixinch import textformat

logger = logging.getLogger(__name__)


def add_css_reference(conf, site):
    e = Extract(conf, site)
    e.read()
    e.add_css()
    e.write()


class Extract(content.HtmlContent):
    """Inject config data into HtmlContent."""

    def __init__(self, conf, site):
        super().__init__(site)

        self._conf = conf
        self._site = site

        self.codings = site.general.encoding
        self.errors = site.general.encoding_errors

        self.sel = site.select
        self.excl = site.exclude
        self.sp = site.general.defaultprocess + site.process
        self.section = site.section

        self._parts_download = site.general.parts_download
        self._guess = conf.general.guess
        self._full_image = site.general.full_image

    def select(self):
        if self.sel == '':
            self.sel = self.guess_selection(self._guess) or '*'
        super().select(self.sel)

    def exclude(self):
        if self.excl:
            super().exclude(self.excl)

    def process(self):
        for s in self.sp:
            system.run_function(self._conf._userdir, 'process', self.doc, s)

    def clean(self):
        tags = self._site.general.add_clean_tags
        attrs = self._site.general.add_clean_attrs
        super().clean(tags, attrs)

    def resolve(self):
        Resolver(self.doc, self._site, self._conf.sites, self._conf).resolve()

    def add_css(self):
        cssfiles = stylesheet.StyleSheet(self._conf, self._site).stylesheets
        super().add_css(cssfiles)

    def run(self):
        self.load()
        self.build()
        self.select()
        self.exclude()
        self.process()
        self.clean()
        self.resolve()
        self.add_css()
        self.write()


class Resolver(content.BaseResolver):
    """Download components and rewrite links."""

    def __init__(self, doc, loc, locs, conf):
        super().__init__(doc, loc, locs)
        self._conf = conf

    def _get_component(self, el, comp):
        self._download_component(comp, comp.url, comp.fname)
        self._add_component_attributes(el, comp.fname)

    def _set_component(self, comp):
        if comp.check_fname():
            super()._set_component(comp)

    def _download_component(self, comp, url, fname):
        force = self.loc.general.force_download
        cache = self._conf._cache.download
        if comp.check_fname(force=force, cache=cache):
            return
        logger.info('[img] %s', url)
        system.make_directories(fname)
        download.download(url, fname, on_error_exit=False)

    def _add_component_attributes(self, el, fname):
        full = int(self.loc.general.full_image)
        w, h = content.get_component_size(el, fname)
        if w and h:
            length = max(w, h)
            if length >= full:
                ratio = h / w
                if ratio > self._conf.pdfratio:
                    el.classes.add('tsi-tall')
                else:
                    el.classes.add('tsi-wide')


class ReadabilityExtract(Extract, content.ReadabilityHtmlContent):
    """Methods for readability."""

    def run(self):
        self.load()
        self.build()
        self.resolve()
        self.add_css()
        self.write()


def _get_ftypes(conf):
    for site in conf.sites:
        ftype = site.ftype = site.general.ftype.lower()
        if ftype:
            continue

        fname = site.fname
        text = site.text
        if content.is_html(fname, text):
            site.ftype = 'html'


def dispatch(conf):
    _get_ftypes(conf)

    pre_each_cmd = conf.general.pre_each_cmd2
    post_each_cmd = conf.general.post_each_cmd2

    for site in conf.sites:
        returncode = system.run_cmds(pre_each_cmd, conf, site)

        if returncode not in (101, 102):
            if site.ftype == 'html':
                run(conf, site)
            else:
                textformat.dispatch(conf, site)

        if returncode not in (102,):
            returncode = system.run_cmds(post_each_cmd, conf, site)


def run(conf, site):
    extractor = site.general.extractor
    if extractor == 'lxml':
        runner = Extract
    elif extractor == 'readability':
        if site.section == 'scriptdefault':
            runner = ReadabilityExtract
        else:
            runner = Extract
    elif extractor == 'readability_only':
        runner = ReadabilityExtract

    runner(conf, site).run()
