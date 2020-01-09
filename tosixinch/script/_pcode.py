
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
        self.p2ftype, self.c2ftype, self.proses = self._get_fdicts()

        self._lexer_cache = {}
        self._class_cache = {}
        self._get_ftypes()
        self._create_ctags()

    def _get_config(self):
        inifile = self.INIFILE
        files = (
            os.path.join(self.conf._configdir, inifile),
            os.path.join(self.conf._userdir, inifile),
        )
        config = configparser.ConfigParser()
        config.read(files)
        return config

    def _get_fdicts(self):
        class_ = system._get_object(self.conf._userdir,
            self.PACKAGE_NAME, self.FTYPE_MOD, self.FTYPE_CLASS)
        return class_(self.ctags_path)()

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
                    self._lexer_cache[fname] = lexer
                    self._class_cache[fname] = self._get_module(ftype)
                    site.ftype = ftype
                else:
                    if name in self.proses:
                        site.ftype = 'prose'
                    else:
                        site.ftype = 'nonprose'

    def _get_module(self, ftype):
        class_ = None
        section = ftype if self.pconfig.has_section(ftype) else 'DEFAULT'
        modname = self.pconfig[section]['module']
        if modname:
            classname = self.pconfig[section]['class']
            if classname:
                class_ = system._get_object(
                    self.conf._userdir, self.PACKAGE_NAME, modname, classname)
        return class_ or _pygments.PygmentsCode

    def _create_ctags(self):
        tagfile = self.pconfig['ctags']['tagfile']
        cmd = self.ctags_path + ' ' + self.pconfig['ctags']['arguments']
        files = [site.fname for site in self.conf.sites
            if self._class_cache.get(site.fname)]
        _ctags._create_ctags(tagfile, cmd, files)
        self._db = _ctags.Tags(tagfile=tagfile, c2ftype=self.c2ftype)

    def run(self, site):
        fname = site.fname
        runner = self._class_cache.get(fname)
        if runner:
            lexer = self._lexer_cache[fname]
            fmt = '[pcode: %s (%s)] %r'
            logger.info(fmt % (site.ftype, runner.__name__, fname))
            return runner(self.conf, site, lexer, self._db).run()
        return 0


def run(conf, site):
    global _PCODE_CACHE
    if not _PCODE_CACHE:
        _PCODE_CACHE = PCode(conf)
    return _PCODE_CACHE.run(site)
