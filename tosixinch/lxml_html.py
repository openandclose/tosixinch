
"""Add a few utilities to lxml.html."""

from tosixinch import _ImportError

try:
    import lxml
except ImportError:
    lxml = _ImportError('lxml')
    lxml_html = _ImportError('lxml')

if lxml:
    from tosixinch._lxml_html import *  # noqa: F401 (unused)
