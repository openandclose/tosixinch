
"""Build commandline strings and run conversion applications in shell."""

import collections.abc
import logging
import os
import shlex
import subprocess
import re

from tosixinch import location
from tosixinch.system import render_template
from tosixinch.content import merge_htmls

logger = logging.getLogger(__name__)

TEMPLATE_EXT = '.t.css'


def _extend(obj, args):
    # Utility function to extend ``list`` or similar object.
    # Mainly to absorb ``append`` and ``extend`` distinction.
    # Presuppose flattened sequence, so you can't do e.g. ``.append([1, 2])``.
    Sequence = collections.abc.Sequence
    if isinstance(args, str):
        if args:
            return obj.append(args)
    elif isinstance(args, Sequence):
        if args:
            return obj.extend(args)
    else:
        fmt = "'args' must be 'str' or 'Sequence'. Got %r(%r)."
        msg = fmt % (type(args), args)
        raise ValueError(msg)


def _is_newer(oldfile, newfile):
    if os.path.getmtime(oldfile) < os.path.getmtime(newfile):
        return True
    return False


def _get_scale_func(scale):
    def func(css_size):
        m = re.match(r'([0-9]+)([A-Za-z]*)', css_size)
        num, unit = m.group(1), m.group(2)
        num = int(num) * float(scale)
        return str(num) + unit
    return func


class Convert(object):
    """Base class for each application specific classes."""

    def __init__(self, conf):
        self._conf = conf
        self.path = conf.converter.cnvpath
        self.css = conf.converter.css
        self.arguments = conf.converter.cnvopts
        self.pdfname = conf.pdfname
        self.style = conf.style
        self._encoding = conf.general.encoding

        ufile = conf._ufile
        tocfile = self._get_tocfile()
        if conf.general.raw:
            files = [site.url for site in conf.sites]
        elif ufile and tocfile and _is_newer(ufile, tocfile):
            locations = location.Locations(ufile=tocfile)
            files = [loc.fnew for loc in locations]
        else:
            files = [site.fnew for site in conf.sites]
        self.files = files

        self.cmd = [self.path]

    def _get_tocfile(self):
        tocfile = self._conf.sites.get_tocfile()
        if tocfile:
            if os.path.isfile(tocfile):
                return tocfile

    def _get_cssfile(self, css):
        configdir = self._conf._configdir
        userdir = self._conf._userdir
        if css == 'sample':
            css = 'sample.t.css'
        if css == 'sample.t.css':
            csspath = os.path.join(configdir, 'css', css)
        else:
            csspath = os.path.join(userdir, 'css', css)

        if css.endswith(TEMPLATE_EXT):
            new_css = css[:-len(TEMPLATE_EXT)] + '.css'
            if userdir is None:
                new_csspath = new_css  # current directory
            else:
                new_csspath = os.path.join(userdir, 'css', new_css)
            context = self._build_context()
            render_template(csspath, new_csspath, context)
            return new_csspath
        else:
            return csspath

    def _build_context(self):
        context = {key: self.style.get(key) for key in self.style}

        context['size'] = self._conf.pdfsize
        context['scale_font'] = _get_scale_func(self.style.font_scale)

        using = lambda x: self._conf.converter._section == x
        conv_dict = {
            'prince': using('prince'),
            'weasyprint': using('weasyprint'),
            'wkhtmltopdf': using('wkhtmltopdf'),
        }
        context.update(conv_dict)

        bookmarks_levels = ['none'] * 6
        for i in range(int(context['toc_depth'])):
            bookmarks_levels[i] = str(i + 1)
        bm_dict = {
            'bm1': bookmarks_levels[0],
            'bm2': bookmarks_levels[1],
            'bm3': bookmarks_levels[2],
            'bm4': bookmarks_levels[3],
            'bm5': bookmarks_levels[4],
            'bm6': bookmarks_levels[5],
        }
        context.update(bm_dict)

        return context

    def _add_css_arguments(self, optstr=None):
        # Add css file arguments to commnad.
        opts = []
        for css in self.css:
            if optstr:
                opts.append(optstr)
            css = self._get_cssfile(css)
            opts.append(css)

        _extend(self.cmd, opts)

    def _add_arguments(self):
        # Add other arguments.
        _extend(self.cmd, self.arguments)

    def _add_args(self, args):
        # Add additional arguments.
        _extend(self.cmd, args)

    def _add_files(self):
        _extend(self.cmd, self.files)

    def _add_merged_files(self):
        self.hname = merge_htmls(
            self.files, self.pdfname, codings=self._encoding)
        _extend(self.cmd, self.hname)

    def _add_pdfname(self, pdf_optstr=None):
        if pdf_optstr:
            _extend(self.cmd, pdf_optstr)
        _extend(self.cmd, self.pdfname)

    def _log(self):
        # from https://bugs.python.org/issue22454
        cmdstr = ' '.join(shlex.quote(c) for c in self.cmd)
        logger.info('[pdf] %r (%r)', self.pdfname, self.path)
        logger.debug('[convert command] %s', cmdstr)

    def _run(self, log=True, dry_run=False):
        if log:
            self._log()
        if not dry_run:
            subprocess.run(self.cmd)

    def run(self):
        raise NotImplementedError


class PrinceConvert(Convert):
    """Run ``prince``.

    https://www.princexml.com/
    """

    def run(self):
        self._add_css_arguments('--style')
        self._add_arguments()
        self._add_files()
        self._add_pdfname('--output')
        self._run()


class WeasyPrintConvert(Convert):
    """Run ``weasyprint``.

    http://weasyprint.org/
    """

    def run(self):
        self._add_css_arguments('--stylesheet')
        self._add_arguments()
        self._add_merged_files()
        self._add_pdfname()
        self._run()


class WkhtmltopdfConvert(Convert):
    """Run ``wkhtmltopdf``.

    https://wkhtmltopdf.org/
    """

    def run(self):
        self._add_css_arguments('--user-style-sheet')
        self._add_arguments()
        self._add_args(['--outline-depth', self.style.toc_depth or '3'])
        self._add_files()
        self._add_pdfname()
        self._run()


def run(conf):
    converter = conf.general.converter
    if converter == 'prince':
        convert = PrinceConvert(conf)
    elif converter == 'weasyprint':
        convert = WeasyPrintConvert(conf)
    elif converter == 'wkhtmltopdf':
        convert = WkhtmltopdfConvert(conf)
    else:
        raise KeyError('Not known converter: %s' % converter)

    convert.run()
