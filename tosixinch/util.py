
"""Collect utility functions to be used by other modules."""

import logging
import os
import posixpath
import re
import subprocess

from tosixinch import _ImportError
from tosixinch import imagesize
from tosixinch import manuopen
from tosixinch import templite

try:
    import lxml.etree
    import lxml.html
except ImportError:
    lxml = _ImportError('lxml')

logger = logging.getLogger(__name__)

HTMLEXT = ('htm', 'html')
_COMMENT = r'\s*(<!--.+?-->\s*)*'
_XMLDECL = r'(<\?xml version.+?\?>)?'
_DOCTYPE = '(<!doctype .+?>)?'
HTMLFILE = re.compile(
    '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + '<html(| .+?)>',
    flags=re.IGNORECASE | re.DOTALL)

PYTHONEXT = ('py',)
PYTHONFILE = re.compile((
    r'^(?:'
    r'#!.+python'
    r'|\s*import'
    ')'
))

_HTML_HEAD = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>%s</title>
  </head>
  <body>
"""

_HTML_TAIL = """  </body>
</html>"""

HTML_TEMPLATE = _HTML_HEAD + '%s' + _HTML_TAIL

BLANK_HTML = '%s<html><body></body></html>'

DEFAULT_DOCTYPE = '<!DOCTYPE html>'
DEFAULT_TITLE = 'notitle'

KEEP_STYLE = 'tsi-keep-style'


def check_ftype(fname, codings=None):
    """Open a file and detect file type.

    Return a tuple (ftype, kind, text)
    """
    text = manuopen.manuopen(fname, codings=codings)
    if is_html(text):
        return 'html', None, text
    elif is_prose(text):
        return 'prose', None, text
    else:
        if is_code(fname, text):
            return 'code', 'python', text
        else:
            return 'nonprose', None, text


def is_html(text):
    if len(text) > 1000 and HTMLFILE.match(text[:1000]):
        return True
    return False


def is_prose(text):
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


def is_code(fname, text=None):
    # For now, only for python code
    ext = fname.rsplit('.', maxsplit=1)
    if len(ext) == 2 and ext[1] in PYTHONEXT:
        return True
    if PYTHONFILE.match(text):
        return True
    return False


def lxml_open(fname=None, text=None, codings=None):
    if not text:
        text = manuopen.manuopen(fname, codings=codings)
    parser = lxml.html.HTMLParser(encoding='utf-8')
    # For now, follows ``readability.htmls``,
    # in redundant utf-8 encoding-decoding.
    root = lxml.html.document_fromstring(
        text.encode('utf-8', 'replace'), parser=parser)
    return root


def lxml_write(fname, doc, doctype=DEFAULT_DOCTYPE):
    html = lxml.html.tostring(doc, encoding='unicode', doctype=doctype)
    with open(fname, 'w') as f:
        f.write(html)


def build_new_html(title=None, content=''):
    """Build minimal html to further edit."""
    title = title or DEFAULT_TITLE
    html = HTML_TEMPLATE % (title, content)
    root = lxml.html.document_fromstring(html)
    return root


def build_blank_html(doctype=None):
    """Build 'more' minimal html, used in `extract.Extract._prepare`."""
    doctype = doctype or DEFAULT_DOCTYPE
    html = BLANK_HTML % doctype
    root = lxml.html.document_fromstring(html)
    return root


def conditioned_iter(el, test):
    """Recursively iterate on an element, yield just matching ones.

    It is like ``element.iter(condition)``,
    but this one skips unmatched element as a tree,
    with its subelements all together.
    It seems lxml doesn't have this functionality, ``iter`` or otherwise.

    cf. ``.xpath()`` could do this kind of things,
    but not suited for more than simplest condition tests.

    Argument ``el`` is presupposed to be an single ``lxml.etree.element``.
    No checks are done.
    """
    if not test(el):
        return
    yield el
    if len(el) == 0:
        return
    for sub in el:
        yield from conditioned_iter(sub, test)


def iter_component(doc):
    """Get inner links needed to download or modify in a html.

    Used in extract.py and toc.py.
    """
    for el in doc.xpath('//img'):
        urls = el.xpath('./@src')
        if not urls:
            continue
        url = urls[0]

        # For data url (e.g. '<img src=data:image/png;base64,iVBORw0K...'),
        # just pass it on to pdf conversion libraries.
        if url.startswith('data:image/'):
            continue

        if _skip_sites(url):
            continue

        yield el, url


def xpath_select(el, string):
    try:
        return el.xpath(string)
    except lxml.etree.LxmlError as e:
        _e = e.error_log.last_error
        n = _e.column
        s = string[:n] + '^^^ ' + string[n] + ' ^^^' + string[n + 1:]
        fmt = ("Xpath error occured probably at column %s "
               "(find the mark '^^^'):\n%s\n")
        logger.error(fmt, n, s)
        raise


# experimental
def _skip_sites(url):
    sites = ()
    # sites = ('gravatar.com/', )
    for site in sites:
        if site in url:
            return True
    return False


def get_component_size(el, fname, stream=None):
    # Get size from html attributes (if any and the unit is no unit or 'px').
    w = el.get('width')
    h = el.get('height')
    if w and h:
        match = re.match('^([0-9.]+)(?:px)?$', w)
        w = int(match[1]) if match else None
        match = re.match('^([0-9.]+)(?:px)?$', h)
        h = int(match[1]) if match else None
    if w and h:
        return w, h

    # Get size from file header (if possible).
    try:
        mime, w, h = imagesize.get_size(fname, stream)
        return int(w), int(h)
    except FileNotFoundError:
        return None, None
    except ValueError:
        return None, None


def transform_xpath(path):
    pat = r'([a-zA-Z]+|[hH][1-6]|\*)\[@class==([\'"])([_a-zA-Z0-9-]+)\2\]'
    pat = re.compile(pat)
    repl = r'\1[contains(concat(" ", normalize-space(@class), " "), " \3 ")]'
    return pat.sub(repl, path)


# https://github.com/django/django/blob/master/django/utils/text.py
def slugify(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


# TODO: Links to merged htmls should be rewritten to fragment links.
def merge_htmls(paths, pdfname, codings=None):
    if len(paths) > 1:
        hname = pdfname.replace('.pdf', '.html')
        root = build_blank_html()
        _append_bodies(root, hname, paths, codings)
        lxml_write(hname, root)
        return hname
    else:
        return paths[0]


def _append_bodies(root, rootname, fnames, codings=None):
    for fname in fnames:
        bodies = lxml_open(fname, codings=codings).xpath('//body')
        for b in bodies:
            _relink_component(b, rootname, fname)
            b.tag = 'div'
            b.set('class', 'tsi-body-merged')
            root.body.append(b)


def _relink_component(doc, rootname, fname):
    for el, url in iter_component(doc):
        # print(url)
        url = posixpath.join(posixpath.dirname(fname), url)
        # print(url, 'joined')
        url = posixpath.relpath(url, start=posixpath.dirname(rootname))
        url = posixpath.normpath(url)
        # print(url, 'relpathed')
        el.attrib['src'] = url


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
