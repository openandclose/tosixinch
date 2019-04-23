"""Clean html, using ``lxml.html.clean`` library.

the object of cleanup is:
1. strip style information, to make easier to apply user stylesheets.
2. simplify html, removing those that might confuse or slow PDF rendering.

We strip all inline and external css, for reason 1.
(exception: when specially ordered to keep <style> tag
in process or userprocess functions.)

We strip all inline and external javascript, for reason 2.
After downloading, I think we don't need javascript any more.
But I may be wrong.

For now, we don't strip any other elements (tags) by default.
``form`` related tags are a candidate,
but in some cases, we may need some texts in them.

For now, we strip only 'color', 'width' and 'height' for attributes.

We don't use ``lxml.html.clean_html`` for attributes cleanup.
``lxml.html`` adopts a whitelist approach (``safe_attrs_only``).
A blacklist approach is more suitable here for our purpose.

And attributes cleanup is skipped inside <svg> and <math> elements.
you need ``color`` and ``width`` for svg image, for example.
"""

import lxml.html

from tosixinch.util import KEEP_STYLE, conditioned_iter

SKIPTAGS = ('svg', 'math')


class Clean(object):
    """Main class of the module."""

    # ``lxml.html.clean.clean_html`` keyword arguments
    kwargs = dict(
        scripts=True,
        javascript=True,
        comments=True,
        style=True,  # changed
        inline_style=False,
        links=True,
        meta=False,  # changed
        page_structure=False,  # changed
        processing_instructions=True,
        embedded=False,  # changed
        frames=False,  # changed
        forms=False,  # changed
        annoying_tags=True,
        remove_tags=None,
        allow_tags=None,
        kill_tags=None,
        remove_unknown_tags=False,  # changed
        safe_attrs_only=False,  # changed
        safe_attrs=[],  # changed
        add_nofollow=False,
        host_whitelist=(),
        whitelist_tags=set(['iframe', 'embed']),
    )

    def __init__(self, doc, tags=None, attrs=None):
        self.doc = doc
        self.tags = tags
        self.attrs = attrs

    def _clean_html(self):
        if self.tags:
            self.kwargs['kill_tags'] = self.tags
        cleaner = lxml.html.clean.Cleaner(**self.kwargs)
        cleaner(self.doc)

    def _skip_tags(self, el):
        if el.tag in SKIPTAGS:
            return False
        return True

    def _skip_style(self, el):
        if KEEP_STYLE in el.classes:
            return True
        return False

    def _clean_attributes(self):
        if not self.attrs:
            return
        for el in conditioned_iter(self.doc, self._skip_tags):
            for attribute in el.attrib:
                if attribute in self.attrs:
                    del el.attrib[attribute]
                    continue
                if attribute == 'style':
                    if self._skip_style(el):
                        continue
                    del el.attrib[attribute]

    def run(self):
        self._clean_html()
        self._clean_attributes()
