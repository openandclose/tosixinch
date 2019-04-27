
"""Communicate with outside environments (OS, shell, python import)."""

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
