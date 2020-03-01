
"""Module for text (non-html) content nmanipulations."""

import html
import logging
import re
import textwrap

from tosixinch import stylesheet
from tosixinch import system
from tosixinch.content import HTML_TEXT_TEMPLATE, build_external_css

logger = logging.getLogger(__name__)

TEXTCLASS_PREFIX = 'tsi-text tsi-'

PYTHONEXT = ('py',)
PYTHONFILE = re.compile((
    r'^(?:'
    r'#!.+python'
    r'|\s*import'
    ')'
))


def is_prose(fname, text):
    """Check if text is prose or not.

    Here 'prose' means general texts
    other than non-prose (source code or poetry etc.).
    We want to separate them
    because the roles of newline are somewhat different between them.
    They require different text wrap strategies.
    """
    lines = text[:10000].split('\n')[:-1]
    counts = (len(line) for line in lines)
    if any((count > 400 for count in counts)):
        # If lines are unusually long, we give up.
        return True
    width = 0
    continuation = 0
    times = 0
    for count in counts:
        if count > width:
            width = count
            if count > width + 1:
                continuation = 0
        elif count in (width, width - 1):
            continuation += 1
        else:
            if continuation > 1:
                times += 1
            continuation = 0
        if times > 1:
            return True
    return False


def is_python(fname, text=None):
    # For now, only for python code
    ext = fname.rsplit('.', maxsplit=1)
    if len(ext) == 2 and ext[1] in PYTHONEXT:
        return True
    if PYTHONFILE.match(text):
        return True
    return False


class Prose(object):
    """General text type, paragraph oriented."""

    def __init__(self, conf, site):
        self._conf = conf
        self._site = site
        self.text = site.text

        self.fname = site.fname
        self.shortname = site.shortname
        self.fnew = site.fnew
        self.width = int(conf.general.textwidth)
        self.indent = conf.general.textindent.strip('"\'')

        self._name = self.__class__.__name__.lower()
        self.textclass = TEXTCLASS_PREFIX + self._name
        self.done_escape = False

    def _wrap(self):
        self.wrapped = self.text

    def _build(self):
        css = ''.join(self._get_css())
        text = self.wrapped
        content = text if self.done_escape else html.escape(text)
        fdict = {
            'title': self.shortname,
            'textclass': self.textclass,
            'csslinks': css,
            'content': content,
        }
        self.built = HTML_TEXT_TEMPLATE.format(**fdict)

    def _highlight(self):
        self.highlighted = self.built

    def _write(self):
        system.Writer(self.fnew, text=self.highlighted).write()

    def run(self):
        self._wrap()
        self._build()
        self._highlight()
        self._write()

    def _get_css(self):
        cssfiles = stylesheet.StyleSheet(self._conf, self._site).stylesheets
        for cssfile in cssfiles:
            yield build_external_css(self.fnew, cssfile)


class NonProse(Prose):
    """Text type with significant line breaks. Require special text-wrap."""

    def _wrap(self):
        wrapper = textwrap.TextWrapper()
        wrapper.width = self.width
        wrapper.tabsize = 4
        wrapper.subsequent_indent = self.indent
        text = []
        for line in self.text.split('\n'):
            s = wrapper.fill(line) + '\n'
            text.append(s)
        self.wrapped = ''.join(text)


class Code(NonProse):
    """Source code, a subclass of `NonProse`."""


class PythonCode(Code):
    """Python code, a subclass of ``Code``.

    Implement a few text highlights
    (as far as fit for black-and-white e-readers).
    """

    LEAD = '|(?:    )+'
    KW = 'def +|class +'
    VAR = '[a-zA-Z0-9_]+'
    DEF = r'^(%s)(%s)(%s)\b'
    # Removing ``!"#$%&'-/;<>?^_`~`` from string.punctuation.
    # ';' and '<>' might match html entity references and html tags.
    # and '>' is actually the one which keeps REF from wrapping definitions.
    REF = r'(?<!def )(?<!class )(?<![^ ()*+,.:=@[\]{|}])(%s)\b'
    ALLDEF = re.compile(DEF % (LEAD, KW, VAR), flags=re.MULTILINE)

    def _highlight(self):
        text = self.built
        matches = self.ALLDEF.finditer(text)
        varset = set()
        for i, match in enumerate(matches, 1000):
            i = str(i)
            lead = match[1]
            kw = match[2]
            var = match[3]

            if var in varset:
                continue
            varset.add(var)

            if lead == '':
                n = '2'
            elif lead == '    ':
                n = '3'
            else:
                n = '9'

            fdict = {
                'i': i,
                'lead': lead,
                'kw': kw,
                'var': var,
                'n': n,
                'textclass': self.textclass,
            }

            pat = self.DEF % (lead, kw, var)
            if n in ('2', '3'):
                repl = '{lead}{kw}<h{n} class="{textclass}" id="tsi{i}">{var}</h{n}>'.format(**fdict)  # noqa: E501
            else:
                repl = '{lead}{kw}<span class="{textclass}" id="tsi{i}">{var}</span>'.format(**fdict)  # noqa: E501
            text = re.sub(pat, repl, text, flags=re.MULTILINE)

            pat = self.REF % var
            repl = '<a href="#tsi{i}">{var}</a>'.format(**fdict)
            text = re.sub(pat, repl, text)

        self.highlighted = text


def _get_ftypes(conf):
    for site in conf.sites:
        if site.ftype:
            continue

        fname = site.fname
        text = site.text
        if is_prose(fname, text):
            site.ftype = 'prose'
        elif is_python(fname, text):
            site.ftype = 'python'
        else:
            site.ftype = 'nonprose'  # default


def dispatch(conf, site):
    _get_ftypes(conf)

    ftype = site.ftype
    if ftype == 'prose':
        runner = Prose
    elif ftype == 'python':
        runner = PythonCode
    else:
        runner = NonProse

    logger.info('[ftype] %s: %r', ftype, site.fname)
    runner(conf, site).run()
