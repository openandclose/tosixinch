
"""Build commandline strings and run conversion applications in shell."""

import collections.abc
import logging
import os
import shlex
import subprocess

from tosixinch import location
from tosixinch import stylesheet

from tosixinch.content import merge_htmls

logger = logging.getLogger(__name__)


def _extend(obj, args):
    """.append or .extend wisely, according to args type."""
    if not args:
        return

    Sequence = collections.abc.Sequence
    if isinstance(args, str):
        return obj.append(args)
    elif isinstance(args, Sequence):
        return obj.extend(args)

    fmt = "'args' must be 'str' or 'Sequence'. Got %r(%r)."
    msg = fmt % (type(args), args)
    raise ValueError(msg)


def _is_newer(oldfile, newfile):
    if os.path.getmtime(oldfile) < os.path.getmtime(newfile):
        return True
    return False


class Convert(object):
    """Base class for each application specific classes."""

    def __init__(self, conf):
        self._conf = conf
        self.path = conf.converter.cnvpath
        self.css2 = conf.converter.css2
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

    def _add_css_arguments(self, optstr=None):
        # Add css file arguments to commnad.
        opts = []
        for css in stylesheet.StyleSheet(self._conf).stylesheets:
            if optstr:
                opts.append(optstr)
            opts.append(css)

        _extend(self.cmd, opts)

    def _add_arguments(self):
        # Add other arguments.
        _extend(self.cmd, self.arguments)

    def _add_args(self, args):
        # Add additional arguments. (for converter idiosyncrasies)
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

    # prince doesn't resolve relative links in local htmls.
    #
    # https://www.princexml.com/forum/topic/3792/cross-document-links-from-relative-paths-in-local-files  # noqa: E501
    # 'Currently the only way to avoid this is
    # to structure the input filenames so that they match the paths used in the links exactly.'  # noqa: E501
    #
    # NG
    # def _add_files(self):
    #     files = [os.path.relpath(fl) for fl in self.files]
    #     _extend(self.cmd, self.files)

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
        raise KeyError('unknown converter: %s' % converter)

    convert.run()
