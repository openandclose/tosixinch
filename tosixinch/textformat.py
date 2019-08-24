
"""Module for text (non-html) content nmanipulations."""

import html
import logging
import re
import textwrap

from tosixinch import system

logger = logging.getLogger(__name__)

TEXTCLASS_PREFIX = 'tsi-text tsi-'

HTML_TEXT_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{fname}</title>
</head>
  <body>
    <h1 class="{textclass}">{fname}</h1>
    <pre class="{textclass}">
{content}
    </pre>
  </body>
</html>"""

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

    ftype = 'prose'

    def __init__(self, conf, site, text):
        self._conf = conf
        self._site = site
        self.text = text

        self.fname = site.fname
        self.shortname = site.shortname
        self.fnew = site.fnew
        self.width = int(conf.general.textwidth)
        self.indent = conf.general.textindent.strip('"\'')

        self._name = self.__class__.__name__.lower()
        self.textclass = TEXTCLASS_PREFIX + self._name

    def _wrap(self):
        self.wrapped = self.text

    def _build(self):
        fname = self.shortname
        content = html.escape(self.wrapped)
        fdict = {
            'fname': fname,
            'textclass': self.textclass,
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


class NonProse(Prose):
    """Text type with significant line breaks. Require special text-wrap."""

    ftype = 'nonprose'

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

    ftype = 'code'


class PythonCode(Code):
    """Python code, a subclass of ``Code``.

    Implement a few text highlights
    (as far as fit for black-and-white e-readers).
    """

    ftype = 'python'

    LEAD = '|(?:    )+'
    KW = 'def +|class +'
    VAR = '[a-zA-Z0-9_]+'
    DEF = r'^(%s)(%s)(%s)\b'
    REF = r'(?<!%s)\b(%s)\b'
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

            pat = self.REF % (kw, var)
            repl = '<a href="#tsi{i}">{var}</a>'.format(**fdict)
            text = re.sub(pat, repl, text)

        self.highlighted = text


def _get_ftype(name):
    if not name:
        return

    name = name.lower()
    if name == 'nonprose':
        return NonProse
    elif name == 'prose':
        return Prose

    classname = name[0].upper() + name[1:].lower() + 'Code'
    try:
        obj = globals()[classname]
    except LookupError:
        pass
    else:
        if issubclass(obj, Prose):
            return obj

    raise ValueError('Got unknown ftype: %r' % name)


def dispatch(conf, site, fname, text):
    runner = _get_ftype(site.ftype)
    if runner:
        pass
    elif is_prose(fname, text):
        runner = Prose
    elif is_python(fname, text):
        runner = PythonCode
    else:
        runner = NonProse

    logger.info('[ftype] %s: %r', runner.ftype, fname)
    runner(conf, site, text).run()
