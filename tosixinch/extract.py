
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
import os

from tosixinch import content
from tosixinch import system
from tosixinch import textformat

logger = logging.getLogger(__name__)


class Extract(content.HtmlContent):
    """Inject config data into HtmlContent."""

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
        self.sp = site.general.defaultprocess + site.process
        self.section = site.section

        self._guess = conf.general.guess
        self.codings = site.general.encoding
        self.errors = site.general.encoding_errors
        self._parts_download = site.general.parts_download
        self._force_download = site.general.force_download
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

    def components(self):
        if self._parts_download:
            super().get_components()

    def cleanup(self):
        tags = self._site.general.add_clean_tags
        attrs = self._site.general.add_clean_attrs
        super().clean(tags, attrs)

    def add_auto_css(self):
        fname = self._site.section + '.css'
        configdir = self._conf._configdir
        userdir = self._conf._userdir
        dirs = (configdir, userdir) if userdir else (configdir,)
        cssfiles = [os.path.join(d, 'css', 'auto', fname) for d in dirs]
        super().add_auto_css(cssfiles)

    def run(self):
        self.load()
        self.build()
        self.select()
        self.exclude()
        self.process()
        self.components()
        self.cleanup()
        self.add_auto_css()
        self.write()

    def _get_component(self, el, url):
        comp = super()._get_component(el, url)
        self._add_component_attributes(el, comp.fname)

    def _download_component(self, comp, url, fname):
        force = self._site.general.force_download
        cache = self._conf._dlcache
        if comp.check_fname(force=force, cache=cache):
            return
        logger.info('[img] %s', url)
        super()._download_component(comp, url, fname)

    def _add_component_attributes(self, el, fname):
        full = int(self._full_image)
        w, h = content.get_component_size(el, fname)
        if w and h:
            length = max(w, h)
            if length >= full:
                ratio = h / w
                if ratio > self._conf.pdfratio:
                    el.classes.add('tsi-tall')
                else:
                    el.classes.add('tsi-wide')


class ReadabilityExtract(content.ReadabilityHtmlContent):
    """Collect methods only for readability."""

    def __init__(self, conf, site, text):
        super().__init__(site.url, site.fname, site.fnew, text)
        self._conf = conf
        self._site = site
        self._parts_download = site.general.parts_download

    def components(self):
        if self._parts_download:
            super().get_components()

    def run(self):
        self.load()
        self.build()
        self.components()
        self.write()


def dispatch(conf):
    pre_percmd = conf.general.pre_percmd2
    post_percmd = conf.general.post_percmd2

    # subprocess version
    # extractors = conf.general.add_extractors
    # e_cmd = ['sample_extractor.py', '--prog']
    # e_cmd.append(','.join(extractors))
    # e_cmd = [e_cmd]
    # import version
    e_cmd = [['sample_extractor']]

    for site in conf.sites:
        returncode = system.run_cmds(pre_percmd, conf, site)

        if returncode not in (101, 102):
            returncode = system.run_cmds(e_cmd, conf, site)

        if returncode not in (101, 102):
            fname = site.fname
            codings = site.general.encoding
            errors = site.general.encoding_errors
            text = system.Reader(fname, codings=codings, errors=errors).read()

            if (site.ftype == 'html'
                    or not site.ftype and content.is_html(fname, text)):
                run(conf, site, text)
            else:
                textformat.dispatch(conf, site, fname, text)

        if returncode not in (102,):
            returncode = system.run_cmds(post_percmd, conf, site)


def run(conf, site, text):
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

    runner(conf, site, text).run()
