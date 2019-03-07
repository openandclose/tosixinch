
"""Reformat text and convert to html.

In ``Extract`` action ('-2'), if text formats are not html,
files are just passed to this module.
"""

import html
import logging
import os
import re
import sys
import textwrap


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


class Prose(object):
    """General text type, paragraph oriented."""

    def __init__(self, conf, site, text):
        self._conf = conf
        self._site = site
        self.text = text

        self.fname = site.fname
        self.fnew = site.fnew
        self.minsep = conf.minsep
        self.width = int(conf.general.textwidth)
        self.indent = conf.general.textindent.strip('"\'')

        self._name = self.__class__.__name__.lower()
        self.textclass = TEXTCLASS_PREFIX + self._name

    def _wrap(self):
        self.wrapped = self.text

    def _build(self):
        fname = self.fname
        fname = fname.split(os.sep, maxsplit=self.minsep)[-1]
        if sys.platform == 'win32':
            fname = fname.replace('\\', '/')

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
        fnew = self.fnew
        if not os.path.exists(fnew):
            self._site.make_directories
        with open(fnew, 'w') as f:
            f.write(self.highlighted)

    def run(self):
        self._wrap()
        self._build()
        self._highlight()
        self._write()


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


def dispatch(conf, site, ftype, kind, text):
    runner = None
    if ftype == 'prose':
        runner = Prose(conf, site, text)
    elif ftype == 'nonprose':
        runner = NonProse(conf, site, text)
    elif ftype == 'code':
        if kind == 'python':
            runner = PythonCode(conf, site, text)
    if runner:
        runner.run()
