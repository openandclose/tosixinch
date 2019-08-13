
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


def run_cmds(cmds, conf, site=None):
    returncode = 0
    userdir = conf._userdir
    for cmd in cmds:
        modname = _check_module(userdir, cmd)
        if modname:
            returncode = run_module(userdir, modname, conf, site)
            if returncode == None:
                returncode = 0
        else:
            returncode = run_cmd(cmd, conf, site)
        if returncode == 100:
            break
    return returncode


def run_cmd(cmd, conf, site=None):
    if not cmd:
        return

    cmd[:] = [_eval_obj(conf, 'conf', word) for word in cmd]
    cmd[:] = [_eval_obj(site, 'site', word) for word in cmd]

    paths = _add_path_env(conf)
    files = _add_files_env(site) if site else {}

    env = os.environ
    env.update(paths)
    env.update(files)
    ret = subprocess.run(cmd, env=env)

    returncode = ret.returncode
    if returncode not in (0, 100, 101):
        args = {
            'returncode': returncode,
            'cmd': ret.args,
            'output': ret.stdout,
            'stderr': ret.stderr,
        }
        raise subprocess.CalledProcessError(**args)

    return returncode


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
    if conf._userscriptdir:
        paths = psep.join((conf._userscriptdir, conf._scriptdir))
    else:
        paths = conf._scriptdir
    paths = psep.join((paths, os.environ['PATH']))
    return {'PATH': paths}


def _add_files_env(site):
    return {
        'TOSIXINCH_URL': site.url,
        'TOSIXINCH_FNAME': site.fname,
        'TOSIXINCH_FNEW': site.fnew,
    }


# python import ----------------------------------

def _load_user_package(userdir, package_name):
    if package_name in sys.modules:
        return
    if userdir is None:
        return
    package_dir = os.path.join(userdir, package_name)
    if not os.path.isdir(package_dir):
        return

    sys.path.insert(0, userdir)
    try:
        importlib.import_module(package_name)
    except ImportError:
        pass
    else:
        fmt = "user %r directory is registered. (%r)"
        logger.debug(fmt, package_name, package_dir)
    del sys.path[0]


def _check_module(userdir, cmd):
    if len(cmd) > 1:
        return
    cmd = cmd[0]
    if '.' in cmd:
        return

    pyfile = os.path.join(userdir, 'script', cmd + '.py')
    if os.path.isfile(pyfile):
        return cmd


def run_module(userdir, modname, conf, site=None):
    _load_user_package(userdir, 'script')

    try:
        mod = importlib.import_module('script.' + modname)
    except ModuleNotFoundError:
        try:
            mod = importlib.import_module('tosixinch.script.' + modname)
        except ModuleNotFoundError:
            fmt = "module name ('script.%s') is not found"
            raise ModuleNotFoundError(fmt % modname)

    return mod.run(conf, site)


def run_process(userdir, element, func_string):
    """Search functions in ``process`` directories, and execute them.

    Modules and functions are delimitted by '.'.
    Functions must be top level ones.
    The first argument is always 'element'.
    Other argements are words splitted by '?' if any.
    E.g. the string 'aaa.bbb?cc?dd' calls
    '[tosixinch.]process.aaa.bbb(element, cc, dd)'.
    """
    _load_user_package(userdir, 'process')

    names, *args = [f.strip() for f in func_string.split('?') if f.strip()]
    if len(names.split('.')) != 2:
        msg = ('You have to name a top-level function with a modulename, '
            "like 'modulename.funcname'")
        raise ValueError(msg)
    modname, funcname = names.rsplit('.', maxsplit=1)

    try:
        mod = importlib.import_module('process.' + modname)
        func = getattr(mod, funcname, None)
    except ModuleNotFoundError:
        func = None
    if not func:
        try:
            mod = importlib.import_module('tosixinch.process.' + modname)
            func = getattr(mod, funcname, None)
        except ModuleNotFoundError:
            pass
    if not func:
        fmt = "process function name ('%s.%s') is not found"
        raise ModuleNotFoundError(fmt % (modname, funcname))

    return func(element, *args)
