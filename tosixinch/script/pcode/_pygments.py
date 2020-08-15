
"""Tokenize text using Pygments, and wrap some tokens with html tags.

Only called from _pcode.py.
"""

import html
import re
import sys

import pygments
import pygments.lexers
import pygments.util
import pygments.token

from tosixinch import location
from tosixinch import textformat

PLATFORM = sys.platform
WORDSEP = re.compile(r'([\v\f ]+)')  # '\n\r\t' are already processed.


class _PygmentsCode(textformat.Prose):
    """Collect non-exposed methods for PygmentsCode."""

    def __init__(self, conf, site,
            lexer, tagdb=None, start_token=None, kindmap=None,
            escape=None, debug=False):
        super().__init__(conf, site)
        self.lexer = lexer
        self.tagdb = tagdb
        start_token = start_token or 'Token.Name'
        self.start_token = pygments.token.string_to_tokentype(start_token)
        self.kindmap = kindmap or {}
        self.escape = escape or html.escape
        self.debug = debug

    def _get_textclass(self):
        # e.g. 'tsi-text tsi-pcode tsi-python'
        return textformat.TEXTCLASS_PREFIX + 'pcode tsi-' + self.ftype

    def _preprocess(self):
        """Simulate what``pygments.Lexer.get_tokens()`` does.

        Before calling ``.get_tokens_unprocessed()``.
        """
        text = self.text
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        text = text.rstrip('\n') + '\n'
        text = text.expandtabs(4)
        return text

    def _collect_chunk(self, line):
        """Subdivide a line of tokens to words or whites groups.

        Token values are e.g. 'func', '(', 'arg', ')', ':'...
        To calculate text wrapping,
        we have to concatenate successive non-whitespaces or whitespaces tokens
        (and divide a token if ever exists a mixed one).

        Fow now no special treatment for whitespace groups,
        they are just like non-whitespace ones.
        """
        words, whites = [], []
        for undivided, token, value in line:
            for i, part in enumerate(WORDSEP.split(value)):
                if i % 2:  # current 'part' is whitespaces or ''
                    current = whites
                    prev = words
                else:  # current 'part' is letters or ''
                    current = words
                    prev = whites

                if part == '':
                    continue

                if prev:
                    yield prev
                    prev[:] = []  # clear referent (words or whites)

                if part == value:
                    undivided = 1
                else:
                    undivided = 0
                    token = None
                current.append((undivided, token, part))
        if current:
            yield current

    def _format_line(self, lnum, line):
        """Actually wrap and highlight token values.

        Note for wrapping, the units are a sequence of printable characters.
        For highlighting, the units are (smaller) token values.
        """
        cnt = 0
        escape = self.escape
        indent = self.indent
        width = self.width
        indent_width = len(indent)
        for chunk in self._collect_chunk(line):
            chunk_cnt = sum(len(v) for u, t, v in chunk)
            if cnt + chunk_cnt > width - 1:
                if indent_width + chunk_cnt <= width:
                    yield escape('\n' + indent)
                    cnt = indent_width

            for undivided, token, value in chunk:
                if undivided:
                    yield self.format_entry(lnum, line, token, escape(value))
                else:
                    yield escape(value)
                cnt += len(value)

    def _format_lines(self):
        r"""Divide token stream to lines.

        Note the last two 'parts' are always '\n' and ''.
        So we don't need to postprocess them.
        """
        lnum = 1
        line = []
        for index, token, value in self.tokensource:
            is_first = True
            for part in value.split('\n'):
                if is_first:
                    is_first = False
                else:
                    if line:
                        yield from self._format_line(lnum, line)
                        line = []
                    yield '\n'
                    lnum += 1

                if part == '':
                    continue

                if part == value:
                    undivided = 1
                else:
                    undivided = 0
                line.append((undivided, token, part))

    def _format_lines_debug(self):
        """Return text with format unchanged.

        Each token value has a title attribute with its token name
        (So that you can see it when the mouse cursor is on it in the browser).
        """
        for index, token, value in self.tokensource:
            tok = str(token)[6:]  # strip first 6 chars, always 'Token.'
            yield '<span title="%s">%s</span>' % (tok, self.escape(value))

    def _get_text(self):
        text = self._preprocess()
        self.tokensource = self.lexer.get_tokens_unprocessed(text)
        if self.debug:
            format_lines = self._format_lines_debug
        else:
            format_lines = self._format_lines
        return ''.join(format_lines())

    def wrap(self):
        self.wrapped = self._get_text()
        self.done_escape = True

    def run(self):
        self.wrap()
        self.build()
        self.highlight()
        self.write()
        return 101


class PygmentsCode(_PygmentsCode):
    """A hook extractor for source codes, using Pygments and Ctags."""

    TAGNAME = 'h2'
    TAGFMT = '<{tagname} id={id} class="{classes}">{value}</{tagname}>'
    REFFMT = '<a href="{path}#{id}">{value}</a>'

    def format_entry(self, lnum, line, token, value):
        if token not in self.start_token:
            return value

        if not self.tagdb:
            return value

        rows = self.tagdb.find(value, self.ftype, self.fname)
        if rows == ([], []):
            return value

        text = self.check_def(lnum, line, token, value, rows)
        if text:
            return text
        text = self.check_ref(lnum, line, token, value, rows)
        if text:
            return text
        return value

    def check_def(self, lnum, line, token, value, rows):
        rows1, rows2 = rows
        for row in rows1:
            if row[3] == lnum:
                tagname = self.get_tagname(row[5])
                return self.wrap_def(value, row[0], tagname)

    def check_ref(self, lnum, line, token, value, rows):
        for rows in rows:
            for row in rows:
                # just picking the first one
                url = self.get_relative_url(row[2])
                return self.wrap_ref(value, row[0], url)

    def wrap_def(self, value, id_, tagname=None, fmt=None):
        fdict = {
            'tagname': tagname or self.TAGNAME,
            'id': id_,
            'classes': self.textclass,
            'value': value,
        }
        fmt = fmt or self.TAGFMT
        return fmt.format(**fdict)

    def wrap_ref(self, value, id_, path, fmt=None):
        fdict = {
            'path': path,
            'id': id_,
            'value': value,
        }
        fmt = fmt or self.REFFMT
        return fmt.format(**fdict)

    def get_relative_url(self, refname):
        if refname == self.fname:
            return ''
        path = location.Location(refname).fnew
        return location.path2ref(path, self.fnew)

    def get_tagname(self, kind):
        d = self.kindmap
        if d.get(kind):
            return d[kind]
        if d.get('*'):
            return d['*']
        return self.TAGNAME


def _get_lexer(fname, text):
    try:
        return pygments.lexers.guess_lexer_for_filename(fname, text)
    except pygments.util.ClassNotFound:
        pass
