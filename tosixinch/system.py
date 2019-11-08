
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
        self.encoding = 'utf-8'


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
        parser = lxml.html.HTMLParser(encoding=self.encoding)
        self.doc = lxml.html.document_fromstring(self.text, parser=parser)

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
        tree = self.doc.getroottree()
        self.text = lxml.html.tostring(tree, encoding='unicode')


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
    scriptdir = conf._scriptdir
    user_scriptdir = conf._user_scriptdir
    scriptd = conf.scriptd

    for cmd in cmds:
        modname = _check_module(user_scriptdir, cmd)
        if modname:
            returncode = run_module(userdir, scriptd, modname, conf, site)
            if returncode in (100, 101, 102):
                break
            else:
                continue

        modname = _check_module(scriptdir, cmd)
        if modname:
            returncode = run_module(None, scriptd, modname, conf, site)
            if returncode in (100, 101, 102):
                break
            else:
                continue

        returncode = run_cmd(cmd, user_scriptdir, scriptdir, conf, site)

    # If returncode is None, normalize it to 0
    return returncode or 0


def run_cmd(_cmd, user_scriptdir, scriptdir, conf, site=None):
    if not _cmd:
        return

    cmd = [_eval_obj(conf, 'conf', word) for word in _cmd]
    cmd = [_eval_obj(site, 'site', word) for word in cmd]

    paths = _add_path_env(user_scriptdir, scriptdir)
    files = _add_files_env(site) if site else {}

    env = os.environ
    env.update(paths)
    env.update(files)
    ret = subprocess.run(cmd, env=env)

    returncode = ret.returncode
    if returncode not in (0, 100, 101, 102):
        args = {
            'returncode': returncode,
            'cmd': ret.args,
            'output': ret.stdout,
            'stderr': ret.stderr,
        }
        raise subprocess.CalledProcessError(**args)

    return returncode


def _check_module(directory, cmd):
    """Check if the command looks like a module.

    If a command consists of one word, without 'dot',
    the script tries to import and run it internally
    (as opposed to run it as a system subprocess command).
    """
    if len(cmd) > 1:
        return
    if '.' in cmd[0]:
        return
    modname = cmd[0]

    if directory:
        pyfile = os.path.join(directory, modname + '.py')
        if os.path.isfile(pyfile):
            return modname


def _eval_obj(obj, objname, word):
    if not obj:
        return word
    if not word.startswith(objname + '.'):
        return word

    for w in word.split('.'):
        if not w.isidentifier():
            return word

    return str(eval(word, {objname: obj}))


def _add_path_env(user_scriptdir, scriptdir):
    psep = os.pathsep
    if user_scriptdir:
        paths = psep.join((user_scriptdir, scriptdir))
    else:
        paths = scriptdir
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


def _get_module(userdir, package_name, modname, on_error_exit=False):
    if userdir:
        _load_user_package(userdir, package_name)

    if userdir:
        name = '%s.%s' % (package_name, modname)
    else:
        name = 'tosixinch.%s.%s' % (package_name, modname)

    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        if on_error_exit:
            fmt = "module ('%s.%s') is not found"
            raise ModuleNotFoundError(fmt % (package_name, modname))


def _get_modules(userdir, package_name, modname):
    mod = _get_module(userdir, package_name, modname)
    if mod:
        exit = False
    else:
        exit = True
    mod2 = _get_module(None, package_name, modname, on_error_exit=exit)

    return mod, mod2


def _get_function(userdir, package_name, modname, funcname):
    mod, mod2 = _get_modules(userdir, package_name, modname)
    func = getattr(mod, funcname, None)  # note: it is OK when mod == None.
    func2 = getattr(mod2, funcname, None)

    if func is None and func2 is None:
        fmt = "function ('%s.%s') is not found"
        raise AttributeError(fmt % (modname, funcname))

    return func or func2


def _parse_func_string(func_string):
    names, *args = [f.strip() for f in func_string.split('?') if f.strip()]
    if len(names.split('.')) != 2:
        msg = ('You have to name a top-level function with a modulename, '
            "like 'modulename.funcname'")
        raise ValueError(msg)
    modname, funcname = names.split('.', maxsplit=1)
    return modname, funcname, args


def run_module(userdir, package_name, modname, conf, site=None):
    mod = _get_module(userdir, package_name, modname, True)
    return mod.run(conf, site)


def run_function(userdir, package_name, element, func_string):
    """Search functions in ``process`` directories, and execute them.

    Modules and functions are delimitted by '.'.
    Functions must be top level ones.
    The first argument is always 'element'.
    Other argements are words splitted by '?' if any.
    E.g. the string 'aaa.bbb?cc?dd' calls
    '[tosixinch.]process.aaa.bbb(element, cc, dd)'.
    """
    modname, funcname, args = _parse_func_string(func_string)
    func = _get_function(userdir, package_name, modname, funcname)
    return func(element, *args)
