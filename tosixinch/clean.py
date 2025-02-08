"""Clean html, using ``lxml_html_clean`` or ``lxml.html.clean`` library.

the object of cleanup is:
1. strip style information, to make easier to apply user stylesheets.
2. simplify html, removing those that might confuse or slow PDF rendering.

We strip all inline and external css, for reason 1.
(exception: when specially ordered to keep <style> tag
in process functions.)

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

import re

from tosixinch import lxml_html  # use lxml_html_clean from lxml_html

RE_CSS_DECLARATION = re.compile(r'^\s*([\w-]+)\s*:\s*(.*?)\s*$')
RE_CSS_VALUE = re.compile(r"""((?:"[^"]+")|(?:'[^\']+')|(?:[^ \t\n]+))""")

KEEP_STYLE = 'tsi-keep-style'


def conditioned_iter(el, *tests):
    """Recursively iterate on an element, yield just matching ones.

    It is like ``element.iter(condition)``,
    but this one skips unmatched element as a tree,
    with its subelements all together.

    Argument ``el`` is presupposed to be an single ``lxml.etree.element``.
    No checks are done.
    """
    for test in tests:
        if not test(el):
            return
    yield el
    if len(el) == 0:
        return
    for sub in el:
        yield from conditioned_iter(sub, *tests)


class Clean(object):
    """Main class of the module."""

    # ``lxml_html_clean.clean_html`` keyword arguments
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

    def __init__(self, doc, tags=None, attrs=None, paths=None, styles=None):
        self.doc = doc
        self.tags = tags
        self.attrs = attrs
        self.paths = paths
        self.stylematcher = StyleMatcher(styles)

    def _clean_html(self):
        if self.tags:
            self.kwargs['kill_tags'] = self.tags
        cleaner = lxml_html.clean.Cleaner(**self.kwargs)
        cleaner(self.doc)

    def _make_skip_element_tests(self):

        def make_test(path):
            def f(doc):
                if doc.xpath(path):
                    return False
                return True
            return f

        tests = []
        for test in self.paths:
            tests.append(make_test(test))

        return tests

    def _keep_style(self, el):
        if KEEP_STYLE in el.classes:
            return True
        return False

    def _clean_attributes(self):
        if not self.attrs:
            return
        for el in conditioned_iter(self.doc, *self._make_skip_element_tests()):
            for attribute in el.attrib:
                if attribute in self.attrs:
                    del el.attrib[attribute]
                    continue
                if attribute == 'style':
                    if self._keep_style(el):
                        continue
                    css = self.stylematcher.run_matches(el.attrib[attribute])
                    if css:
                        el.attrib[attribute] = css
                    else:
                        del el.attrib[attribute]

    def run(self):
        self._clean_html()
        self._clean_attributes()


class StyleMatcher(object):
    """Retain only specified inline style attributes."""

    # ',' is used e,g. in 'font-family'
    # '/' is used e.g. in 'line-height' in 'font'
    # '(' is used e.g. in function calls
    DIFFICULT_PARSE_INDICATOR = ',/('

    def __init__(self, matches=None):
        if not matches:
            matches = []
        self.matches, self.raw_props = self.build_matches(matches)

    def parse_declaration(self, declarations):
        for dec in declarations.split(';'):
            if not dec.strip():
                continue
            m = RE_CSS_DECLARATION.match(dec)
            if m:
                prop, valstr = m.groups()
                prop = prop.lower()
                valstr = valstr.replace(' !important', '').strip()
                yield prop, valstr

    def parse_values(self, valstr):
        for c in self.DIFFICULT_PARSE_INDICATOR:
            if c in valstr:
                yield valstr
                return

        for value in RE_CSS_VALUE.findall(valstr):
            if value.strip():
                yield value.strip()

    def build_matches(self, matches):
        decs = {}
        raw_props = set()
        for match in matches:
            match = match.rstrip(';').strip()
            for prop, valstr in self.parse_declaration(match):
                if valstr == '':
                    raw_props.add(prop)
                else:
                    for value in self.parse_values(valstr):
                        decs[(prop, value)] = 1
        return decs, raw_props

    def run_matches(self, cssstr):
        """Return a new css string containg only the matched ones."""
        csslist = []
        for prop, valstr in self.parse_declaration(cssstr):
            if prop in self.raw_props:
                csslist.append((prop, valstr))
            else:
                for value in self.parse_values(valstr):
                    if (prop, value) in self.matches:
                        csslist.append((prop, value))
        return self.compile(csslist)

    def compile(self, csslist):
        s = {}
        for prop, value in csslist:
            s[prop] = []
        for prop, value in csslist:
            s[prop].append(value)

        for prop in s:
            values = ' '.join(s[prop])
            s[prop] = '%s: %s' % (prop, values)

        return '; '.join(s.values())
