
"""Module for text (non-html) content nmanipulations."""

import html
import logging
import re
import textwrap

from tosixinch import action

logger = logging.getLogger(__name__)

HTML_TEXT_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    {csslinks}
  </head>
  <body>
    <h1 class="{textclass}">{title}</h1>
    <pre class="{textclass}">
{content}
    </pre>
  </body>
</html>"""

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
            if count > width + 1:
                continuation = 0
            width = count
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
    parts = fname.rsplit('.', maxsplit=1)
    if len(parts) == 2 and parts[1] in PYTHONEXT:
        return True
    if PYTHONFILE.match(text):
        return True
    return False


class Prose(action.TextFormatter):
    """General text type, paragraph oriented."""

    def __init__(self, conf, site):
        super().__init__(conf, site)

        self.shortname = site.shortname
        self.width = int(conf.general.textwidth)
        self.indent = conf.general.textindent.strip('"\'')
        self.ftype = self._site.ftype
        self.textclass = self._get_textclass()
        self.done_escape = False

    def _get_textclass(self):
        name = self.__class__.__name__.lower()
        return TEXTCLASS_PREFIX + name

    def wrap(self):
        self.wrapped = self.text

    def build(self):
        css = '\n    '.join(self.get_css_reference())
        text = self.wrapped
        content = text if self.done_escape else html.escape(text)
        fdict = {
            'title': self.shortname,
            'textclass': self.textclass,
            'csslinks': css,
            'content': content,
        }
        self.built = HTML_TEXT_TEMPLATE.format(**fdict)

    def highlight(self):
        self.highlighted = self.built

    def write(self):
        return self._write(self.fnew, text=self.highlighted)

    def run(self):
        self.wrap()
        self.build()
        self.highlight()
        self.write()


class NonProse(Prose):
    """Text type with significant line breaks. Require special text-wrap."""

    def wrap(self):
        wrapper = textwrap.TextWrapper()
        wrapper.width = self.width
        wrapper.tabsize = 4
        wrapper.subsequent_indent = self.indent
        text = []
        for line in self.text.split('\n'):
            s = wrapper.fill(line)
            text.append(s)
        self.wrapped = '\n'.join(text)


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

    def highlight(self):
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


def run(conf, site):
    if not site.ftype:
        fname = site.fname
        text = site.text
        if is_prose(fname, text):
            site.ftype = 'prose'
        elif is_python(fname, text):
            site.ftype = 'python'
        else:
            site.ftype = 'nonprose'  # default

    if site.ftype == 'prose':
        runner = Prose
    elif site.ftype == 'python':
        runner = PythonCode
    else:
        runner = NonProse

    logger.info('[ftype] %s: %r', site.ftype, site.fname)
    runner(conf, site).run()
