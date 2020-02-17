
"""A sample hook for source codes using Pygments and Ctags."""

import configparser
import logging
import os

from tosixinch import system
from tosixinch.script.pcode import _ctags
from tosixinch.script.pcode import _pygments

logger = logging.getLogger(__name__)

_PCODE_CACHE = None


class PCode(object):
    """Manage Pygments and Ctags data."""

    INIFILE = 'pcode.ini'
    PACKAGE_NAME = 'script.pcode'
    FTYPE_MOD = '_ftype'
    FTYPE_CLASS = 'FType'

    def __init__(self, conf):
        self.conf = conf
        self.pconfig = self._get_config()
        self.ctags_path = os.path.expanduser(
            self.pconfig['ctags'].get('ctags', 'ctags'))
        self.p2ftype, self.c2ftype = self._get_fdicts()

        self._lexer_cache = {}
        self._class_cache = {}
        self._get_ftypes()

        if self._lexer_cache:
            logger.debug('[p2ftype]\n%s' % self.p2ftype)
            logger.debug('[c2ftype]\n%s' % self.c2ftype)
            self._create_ctags()

    def _get_config(self):
        inifile = self.INIFILE
        files = (
            os.path.join(self.conf._configdir, inifile),
            os.path.join(self.conf._userdir, inifile),
        )
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(files)
        return config

    def _get_fdicts(self):
        class_ = system._get_object(self.conf._userdir,
            self.PACKAGE_NAME, self.FTYPE_MOD, self.FTYPE_CLASS)
        p2ftype, c2ftype = class_(self.ctags_path)()

        pconfig = self.pconfig
        if pconfig.has_section('p2ftype'):
            for k, v in pconfig.items('p2ftype'):
                if pconfig['DEFAULT'].get(k):
                    continue
                p2ftype[k] = v
        if pconfig.has_section('c2ftype'):
            for k, v in pconfig.items('c2ftype'):
                if pconfig['DEFAULT'].get(k):
                    continue
                c2ftype[k] = v
        return p2ftype, c2ftype

    def _get_ftypes(self):
        for site in self.conf.sites:
            if site.ftype:
                continue
            fname = site.fname
            text = site.text
            lexer = _pygments._get_lexer(fname, text)
            if lexer:
                name = lexer.name
                fmt = 'Pygments lexer: %r (%s)'
                logger.debug(fmt % (name, fname))
                ftype = self.p2ftype.get(name)
                if ftype:
                    if ftype == 'prose':
                        site.ftype = 'prose'
                        continue
                    if ftype == 'nonprose':
                        site.ftype = 'nonprose'
                        continue

                    self._lexer_cache[fname] = lexer
                    self._class_cache[fname] = self._get_module(ftype)
                    site.ftype = ftype
                    continue
                else:
                    site.ftype = 'nonprose'

    def _get_module(self, ftype):
        class_ = None
        section = self._get_section(ftype)
        modname = section.get('module')
        if modname:
            classname = section.get('class')
            if classname:
                class_ = system._get_object(
                    self.conf._userdir, self.PACKAGE_NAME, modname, classname)
        return class_ or _pygments.PygmentsCode

    def _get_section(self, section_name):
        if not self.pconfig.has_section(section_name):
            section_name = 'DEFAULT'
        return self.pconfig[section_name]

    def _create_ctags(self):
        tagfile = self.pconfig['ctags']['tagfile']
        cmd = self.ctags_path + ' ' + self.pconfig['ctags']['arguments']
        files = [site.fname for site in self.conf.sites
            if self._class_cache.get(site.fname)]
        _ctags._create_ctags(tagfile, cmd, files)
        self._db = _ctags.Tags(tagfile=tagfile, c2ftype=self.c2ftype)

    def _parse_kindmap(self, kindmap):
        """Create kind-to-elem dict from elem-to-kind text.

        'h2=cf, h3=m' -> {'c': 'h2', 'f': 'h2', 'm': 'h3'}
        """
        d = {}
        for item in kindmap.split(','):
            elem, kinds = item.split('=')
            elem = elem.strip()
            for kind in kinds.strip():
                d[kind] = elem
        return d

    def run(self, site):
        fname = site.fname
        runner = self._class_cache.get(fname)
        if runner:
            lexer = self._lexer_cache[fname]
            fmt = '[pcode: %s (%s)] %r'
            logger.info(fmt % (site.ftype, runner.__name__, fname))

            section = self._get_section(site.ftype)
            start_token = section.get('start_token')
            kindmap = self._parse_kindmap(section.get('kindmap'))
            return runner(
                self.conf, site, lexer, self._db, start_token, kindmap).run()
        return 0


def run(conf, site):
    global _PCODE_CACHE
    if not _PCODE_CACHE:
        _PCODE_CACHE = PCode(conf)
    return _PCODE_CACHE.run(site)
