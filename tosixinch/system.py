
"""Communicate with outside environments (OS, shell, python import)."""

import importlib
import logging
import os
import sys
import subprocess

from tosixinch import _ImportError
from tosixinch import manuopen
from tosixinch import templite

try:
    import lxml.etree
    import lxml.html
except ImportError:
    lxml = _ImportError('lxml')

logger = logging.getLogger(__name__)


# file read and write ---------------------------

DEFAULT_DOCTYPE = '<!DOCTYPE html>'


def make_directories(fname, on_error_exit=True):
    if not _in_current_dir(fname):
        if on_error_exit:
            msg = 'filename path is outside of current dir: %r' % fname
            logger.error(msg)
            sys.exit(1)
        else:
            return
    dname = os.path.abspath(os.path.dirname(fname))
    os.makedirs(dname, exist_ok=True)


def _in_current_dir(fname, base=os.curdir):
    current = os.path.abspath(base)
    filepath = os.path.abspath(fname)
    # note: the same filepath is not 'in' current dir.
    if filepath.startswith(current + os.sep):
        return True
    else:
        return False


class _File(object):
    """Common object for Reader and Writer."""

    def __init__(self, fname, platform):
        self.fname = fname
        self.platform = platform


class Reader(_File):
    """Text reader object."""

    def __init__(self, fname, text=None, codings=None,
            errors='strict', platform=sys.platform):
        super().__init__(fname, platform)
        self.text = text
        self.codings = codings
        self.errors = errors

    def _prepare(self):
        if self.text:
            return
        self.text, self.encoding = manuopen.manuopen(
            self.fname, self.codings, self.errors)

    def read(self):
        self._prepare()
        return self.text


class Writer(_File):
    """Text writer object."""

    def __init__(self, fname, doc=None, text=None, platform=sys.platform):
        super().__init__(fname, platform)
        self.doc = doc
        self.text = text

    def _serialize(self):
        if self.text:
            return
        self.text = '\n'.join(self.doc)

    def _prepare(self):
        self._serialize()
        make_directories(self.fname)

    def write(self):
        self._prepare()
        with open(self.fname, 'w') as f:
            f.write(self.text)


class HtmlReader(Reader):
    """html reader object.

    From fname or text, return document object (lxml.html.HtmlElement).
    """

    def _parse(self):
        parser = lxml.html.HTMLParser(encoding='utf-8')
        # For now, follows ``readability.htmls``,
        # in redundant utf-8 encoding-decoding.
        self.doc = lxml.html.document_fromstring(
            self.text.encode('utf-8', 'replace'), parser=parser)

    def read(self):
        self._prepare()
        self._parse()
        return self.doc


class HtmlWriter(Writer):
    """html writer object.

    From document object, write serialized text to fname.
    """

    def __init__(self, fname, doc=None, text=None,
            platform=sys.platform, doctype=DEFAULT_DOCTYPE):
        super().__init__(fname, doc, text, platform)
        self.doctype = doctype

    def _serialize(self):
        if self.text:
            return
        self.text = lxml.html.tostring(
            self.doc, encoding='unicode', doctype=self.doctype)


# shell invocation ------------------------------

def render_template(csspath, new_csspath, context):
    with open(csspath) as f:
        template = f.read()
    template = templite.Templite(template)
    text = template.render(context)
    with open(new_csspath, 'w') as f:
        f.write(text)


def run_cmd(conf, site, cmd):
    if cmd:
        cmd[:] = [_eval_obj(conf, 'conf', word) for word in cmd]
        cmd[:] = [_eval_obj(site, 'site', word) for word in cmd]
        paths = _add_path_env(conf)

        # return subprocess.Popen(cmd).pid
        return subprocess.run(cmd, env=dict(os.environ, PATH=paths))


def _eval_obj(obj, objname, word):
    if not obj:
        return word
    if not word.startswith(objname + '.'):
        return word

    for w in word.split('.'):
        if not w.isidentifier():
            return word

    return str(eval(word, {objname: obj}))


def _add_path_env(conf):
    psep = os.pathsep
    paths = psep.join((conf._userscriptdir, conf._scriptdir))
    paths = psep.join((paths, os.environ['PATH']))
    return paths


# python import ----------------------------------

def userpythondir_init(userdir):
    if userdir is None:
        return

    sys.path.insert(0, userdir)

    if os.path.isdir(os.path.join(userdir, 'process')):
        if 'process' not in sys.modules:
            try:
                import process  # noqa: F401 (unused import)
                fmt = "user 'process' directory is registered. (%r)"
                logger.debug(fmt, os.path.join(userdir, 'process'))
            except ImportError:
                pass

    del sys.path[0]


# TODO: pre-import modules in process.
def run_process(element, func_string):
    """Search functions in ``process`` directories, and execute them.

    Modules and functions are delimitted by '.'.
    Functions must be top level ones.
    The first argument is always 'element'.
    Other argements are words splitted by '?' if any.
    E.g. the string 'aaa.bbb?cc?dd' calls
    '[tosixinch.]process.aaa.bbb(element, cc, dd)'.
    """
    names, *args = [f.strip() for f in func_string.split('?') if f.strip()]
    if '.' not in names:
        msg = ('You have to name functions with modulenames, '
            "like 'modulename.funcname'")
        raise ValueError(msg)
    modname, func = names.rsplit('.', maxsplit=1)
    try:
        mod = importlib.import_module('process.' + modname)
    except ModuleNotFoundError:
        try:
            mod = importlib.import_module('tosixinch.process.' + modname)
        except ModuleNotFoundError:
            fmt = 'process module name (%r) is not found'
            raise ModuleNotFoundError(fmt % modname)

    func = getattr(mod, func)
    return func(element, *args)
