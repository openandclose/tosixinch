
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


def get_filename(fname, platform=sys.platform):
    """Convert internal 'fname' to 'filename' OS actually uses."""
    # if platform == 'win32':
    #     return fname.replace('/', '\\')
    return fname


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


def _in_current_dir(fname, base=os.curdir, sep=os.sep):
    current = os.path.abspath(base)
    filepath = os.path.abspath(fname)
    # note: the same filepath is not 'in' current dir.
    if filepath.startswith(current + sep):
        return True
    else:
        return False


class _File(object):
    """Common object for Reader and Writer."""

    def __init__(self, fname, platform):
        self._fname = fname
        self.platform = platform
        self.filename = get_filename(fname, platform)


class Reader(_File):
    """Text reader object."""

    def __init__(self, fname, text=None, codings=None, platform=sys.platform):
        super().__init__(fname, platform)
        self.text = text
        self.codings = codings

    def _prepare(self):
        if self.text:
            return
        self.text = manuopen.manuopen(self.filename, self.codings)

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
        make_directories(self.filename)

    def write(self):
        self._prepare()
        with open(self.filename, 'w') as f:
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

    From document object, write serialized text to filename.
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


def runcmd(conf, cmds):
    if cmds:
        cmds[:] = [_eval_conf(conf, word) for word in cmds]
        paths = _add_path_env(conf)

        # return subprocess.Popen(cmds).pid
        return subprocess.run(cmds, env=dict(os.environ, PATH=paths))


def _eval_conf(conf, word):
    if not word.startswith('conf.'):
        return word

    for w in word.split('.'):
        if not w.isidentifier():
            return word

    return str(eval(word, {'conf': conf}))


def _add_path_env(conf):
    psep = os.pathsep
    scriptdir = os.path.dirname(conf._configdir) + os.sep + 'script'
    paths = conf._userdir + psep + scriptdir + psep
    paths = paths + os.environ['PATH']
    paths = paths.rstrip(psep)
    return paths


# python import ----------------------------------

def userpythondir_init(userdir):
    if userdir is None:
        return
    if not os.path.isdir(os.path.join(userdir, 'userprocess')):
        return

    # if userdir not in sys.path:
    if 'userprocess' not in sys.modules:
        sys.path.insert(0, userdir)
        import userprocess  # noqa: F401 (unused import)
        del sys.path[0]
        fmt = "user python directory is registered. (%r)"
        logger.debug(fmt, os.path.join(userdir, 'userprocess'))


# TODO: pre-import modules in process.
def apply_function(element, func_string):
    """Search functions in ``process`` directories, and execute them.

    Modules and functions are delimitted by '.'.
    Functions must be top level ones.
    The first argument is always 'element'.
    Other argements are words splitted by '?' if any.
    E.g. the string 'aaa.bbb?cc?dd' calls
    '[user]process.aaa.bbb(element, cc, dd)'.
    """
    names, *args = [f.strip() for f in func_string.split('?') if f.strip()]
    if '.' not in names:
        msg = ('You have to name functions with modulenames, '
            "like 'modulename.funcname'")
        raise ValueError(msg)
    modname, func = names.rsplit('.', maxsplit=1)
    try:
        mod = importlib.import_module('userprocess.' + modname)
    except ModuleNotFoundError:
        try:
            mod = importlib.import_module('tosixinch.process.' + modname)
        except ModuleNotFoundError:
            fmt = 'process module name (%r) is not found'
            raise ModuleNotFoundError(fmt % modname)

    func = getattr(mod, func)
    if args:
        return func(element, *args)
    else:
        return func(element)
