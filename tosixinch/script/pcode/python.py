
"""A plugin example for _pcode.py (Python)."""

from tosixinch.script.pcode import _pygments


class CustomCode(_pygments.PygmentsCode):
    """Format Python code."""

    def check_def(self, lnum, line, token, value, rows):
        if self._check_dunder_method(value):
            return

        rows1, rows2 = rows
        for row in rows1:
            if row[3] == lnum:
                tagname = self._check_indent(line)
                return self.wrap_def(value, row[0], tagname)

    def check_ref(self, lnum, line, token, value, rows):
        if self._check_dunder_method(value):
            return
        return super().check_ref(lnum, line, token, value, rows)

    def _check_dunder_method(self, value):
        if value.startswith('__') and value.endswith('__'):
            return True
        return False

    def _check_indent(self, line):
        num = 0  # number of leading whitespaces
        for undivided, token, value in line:
            if value.strip():
                break
            for char in value:
                if char == ' ':
                    num += 1
                else:  # horizontal tab in most cases
                    num += 4

        if num < 4:
            tagname = 'h2'
        elif num < 8:
            tagname = 'h3'
        elif num < 12:
            tagname = 'h4'
        else:
            tagname = 'span'
        return tagname
