
"""Communicate with outside environments (OS, shell, python import)."""

import http.cookiejar
import gzip
import importlib
import logging
import os
import sys
import subprocess
import time
import types
import urllib.request
import zlib

from tosixinch import manuopen

logger = logging.getLogger(__name__)


# download  --------------------------------------

def request(url, user_agent='Mozilla/5.0', cookies=None, on_error_exit=True):
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa: E501
        'Accept-Encoding': 'gzip, deflate',
        # 'Accept-Charset': 'utf-8,*;q=0.1',
        # 'Accept-Language': 'en-US,en;q=0.8',
    }
    # Many things are wrong.
    # http://stackoverflow.com/questions/789856/turning-on-debug-output-for-python-3-urllib  # noqa: E501
    # https://bugs.python.org/issue26892
    debuglevel = 0
    if logger.getEffectiveLevel() == 10:
        debuglevel = 1
    logger.debug("[download] '%s'", url)

    req = urllib.request.Request(url, headers=headers)
    cj = http.cookiejar.CookieJar()
    if cookies:
        for cookie in cookies:
            cj = add_cookie(cj, cookie)

    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(debuglevel=debuglevel),
        urllib.request.HTTPCookieProcessor(cj))

    try:
        return opener.open(req, timeout=5)

    except urllib.request.HTTPError as e:
        if on_error_exit:
            raise
        if e.code == 404:
            logger.info('[HTTPError 404 %s] %s' % (e.reason, url))
        else:
            logger.warning(
                '[HTTPError %s %s %s] %s' % (
                    e.code, e.reason, e.headers, url))

    except urllib.request.URLError as e:
        if on_error_exit:
            raise
        logger.warning('[URLError %s] %s' % (e.reason, url))


def retrieve(f, on_error_exit=True):
    # ``f`` is either file object or http.client.HTTPResponse object.
    try:
        text = f.read()
        if isinstance(f, http.client.HTTPResponse):
            if f.getheader('Content-Encoding') == 'gzip':
                text = gzip.decompress(text)
            elif f.getheader('Content-Encoding') == 'deflate':
                logger.info("[http] 'Content-Encoding' is 'deflate'")
                text = zlib.decompress(text)
        return text

    except http.client.RemoteDisconnected as e:
        if on_error_exit:
            raise
        logger.warning('[RemoteDisconnected: %s] %s' % (str(e), f.url))


def _add_cookie(cj, name, value, domain, path='/'):
    # cf. http.cookiejar.Cookie signature
    #
    # def __init__(
    #     version, name, value,
    #     port, port_specified,
    #     domain, domain_specified, domain_initial_dot,
    #     path, path_specified,
    #     secure, expires, discard,
    #     comment, comment_url, rest,
    #     rfc2109=False,
    # )
    #
    domain_initial_dot = False
    if domain.startswith('.'):
        domain_initial_dot = True
    expires = time.time() + 60 * 60 * 24 * 2  # 2 days from now

    cookie = http.cookiejar.Cookie(
        0, name, value,
        '80', True,
        domain, True, domain_initial_dot,
        path, True,
        False, expires, False,
        'simple-cookie', None, None,
    )
    cj.set_cookie(cookie)
    return cj


def add_cookie(cj, cookie):
    # 'cookie' is now an unparsed string.
    values = [c.strip() for c in cookie.split(',') if c.strip()] or []
    if len(values) == 3:
        values.append('/')
    name, value, domain, path = values
    return _add_cookie(cj, name, value, domain, path)


# file read and write ----------------------------

def make_directories(fname, on_error_exit=True):
    if not _in_current_dir(fname):
        if on_error_exit:
            msg = 'filename path is outside of current dir: %r' % fname
            logger.error(msg)
            sys.exit(1)
        else:
            return
    path = os.path.abspath(os.path.dirname(fname))
    os.makedirs(path, exist_ok=True)


def _in_current_dir(fname, base=os.curdir):
    current = os.path.abspath(base)
    path = os.path.abspath(fname)
    # note: the same filepath is not 'in' current dir.
    if path.startswith(current + os.sep):
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
            errors='strict', length=None, platform=sys.platform):
        super().__init__(fname, platform)
        self.text = text
        self.codings = codings
        self.errors = errors
        self.buf_length = length or 102400

    def _prepare(self):
        if self.text:
            return
        self.text, self.encoding = manuopen.manuopen(
            self.fname, self.codings, self.errors, self.buf_length)

    def read(self):
        self._prepare()
        return self.text


class Writer(_File):
    """Text writer object."""

    def __init__(self, fname, text, platform=sys.platform):
        super().__init__(fname, platform)
        self.text = text

    def _prepare(self):
        make_directories(self.fname)

    def write(self):
        self._prepare()
        mode = 'wb' if isinstance(self.text, bytes) else 'w'
        with open(self.fname, mode) as f:
            f.write(self.text)


def read(fname, text=None, codings=None,
        errors='strict', length=None, platform=sys.platform):
    return Reader(fname, text, codings, errors, length, platform).read()


def write(fname, text, platform=sys.platform):
    return Writer(fname, text, platform).write()


# shell invocation -------------------------------

def run_cmds(cmds, conf, site=None):
    returncode = 0
    userdir = conf._userdir
    scriptdir = conf._scriptdir
    user_scriptdir = conf._user_scriptdir
    scriptd = conf.SCRIPTDIR

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
        if returncode in (100, 101, 102):
            break

    # If returncode is None, normalize it to 0
    return returncode or 0


def run_cmd(command, user_scriptdir, scriptdir, conf, site=None):
    if not command:
        return

    cmd = [_eval_obj(conf, 'conf', word) for word in command]
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

_PROCESS_FUNCTIONS_REGISTERED = False

_mod_cache = {}
_obj_cache = {}


def _register_userdir(userdir):
    if userdir is None:
        return
    if userdir in sys.path:
        return
    sys.path.insert(0, userdir)


def _get_module(userdir, package_name, modname, on_error_exit=False):
    key = (userdir, package_name, modname)
    if key in _mod_cache:
        return _mod_cache[key]

    if userdir:
        _register_userdir(userdir)

    if userdir:
        name = '%s.%s' % (package_name, modname)
    else:
        name = 'tosixinch.%s.%s' % (package_name, modname)

    mod = None
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError:
        if on_error_exit:
            raise

    _mod_cache[key] = mod
    return mod


def run_module(userdir, package_name, modname, conf, site=None):
    mod = _get_module(userdir, package_name, modname, True)
    return mod.run(conf, site)


def _get_object(userdir, package_name, modname, objname):
    keys = [(u, package_name, modname, objname) for u in (userdir, None)]
    for key in keys:
        if key in _obj_cache:
            return _obj_cache[key]

    for key in keys:
        mod = _get_module(key[0], package_name, modname)
        if mod:
            obj = getattr(mod, objname, None)
            if obj:
                _obj_cache[key] = obj
                return obj


def _parse_func_string(func_string):
    names, *args = [f.strip() for f in func_string.split('?') if f.strip()]
    num = len(names.split('.'))
    if num == 1:
        return None, names, args
    elif num == 2:
        modname, funcname = names.split('.', maxsplit=1)
        return modname, funcname, args
    else:
        msg = 'More than one dot is used in function name: %r' % names
        raise ValueError(msg)


def _get_all_modules(userdir, package_name):
    if userdir:
        names = os.listdir(os.path.join(userdir, package_name))
    else:
        d = os.path.dirname(__file__)
        d = os.path.join(d, package_name)
        names = os.listdir(d) if os.path.isdir(d) else []
    for name in names:
        if name.startswith('__'):
            continue
        if name.endswith('.py'):
            modname = name[:-3]
            mod = _get_module(
                userdir, package_name, modname, on_error_exit=True)
            yield modname, mod


def _register_all_functions(userdir, package_name):
    global _PROCESS_FUNCTIONS_REGISTERED
    if _PROCESS_FUNCTIONS_REGISTERED:
        return

    for u in (userdir, None):
        for modname, mod in _get_all_modules(u, package_name):
            for objname, obj in mod.__dict__.items():
                if isinstance(obj, types.FunctionType):
                    key = (userdir, package_name, modname, objname)
                    _obj_cache[key] = obj

    _PROCESS_FUNCTIONS_REGISTERED = True


def _search_function(package_name_, funcname):
    user_funcs = []
    program_funcs = []
    for key in _obj_cache:
        userdir, package_name, modname, objname = key
        if package_name == package_name_:
            if funcname == objname:
                if userdir:
                    user_funcs.append(key)
                else:
                    program_funcs.append(key)

    if len(user_funcs) > 1:
        msg = ['%s.%s' % (modname, objname)
            for userdir, package_name, modname, objname in user_funcs]
        msg = 'duplicate function names: ' + ', '.join(msg)
        raise ValueError(msg)

    if user_funcs:
        return _obj_cache[user_funcs[0]]
    if program_funcs:
        return _obj_cache[program_funcs[0]]
    return None


def run_function(userdir, package_name, element, func_string):
    """Search functions in modules in a directory, and execute them.

    Functions must be top level ones.

    The first argument of the function is 'element'.

    ``func_string`` can have optinal '?'s.
    Strings after '?' until next '?' (or end) are other arguments.

    The rest of ``func_string`` must not include more than one dot ('.').
    If it includes one dot,
    the program interpretes it as ``<module name>.<function name>``.
    If it includes no dot,
    the program searches the name in all modules.
    """
    modname, funcname, args = _parse_func_string(func_string)
    if modname is None:
        _register_all_functions(userdir, package_name)
        func = _search_function(package_name, funcname)
        msg = 'function (%r) is not found' % funcname
    else:
        func = _get_object(userdir, package_name, modname, funcname)
        msg = "function ('%s.%s') is not found" % (modname, funcname)

    if func is None:
        raise AttributeError(msg)
    return func(element, *args)
