
"""Build configuration objects.

The main class is `Conf`,
which returns a wrapper of a few `ConfigFetch` objects,
which are themselves wrappers of `ConfigFileParser` objects.

Following `configfetch` module,
we try to keep the word ``config`` for `ConfigParser` object,
``conf`` for `ConfigFetch` object.
"""

import argparse
import fnmatch
import glob
import logging
import os
import re
import sys
import urllib.parse

from pkg_resources import resource_filename

from tosixinch import cached_property
from tosixinch import configfetch
from tosixinch import location
from tosixinch import system

from tosixinch.zconfigparser import ZConfigParser

logger = logging.getLogger(__name__)

DEFAULT_PDFNAME = 'no-urls.pdf'

# https://github.com/sindresorhus/binary-extensions
BINARY_EXTENSIONS = """
    3ds 3g2 3gp 7z a aac adp ai aif aiff alz ape apk ar arj asf au avi bak bh
    bin bk bmp btif bz2 bzip2 cab caf cgm class cmx cpio cr2 csv cur dat deb
    dex djvu dll dmg dng doc docm docx dot dotm dra DS_Store dsk dts dtshd dvb
    dwg dxf ecelp4800 ecelp7470 ecelp9600 egg eol eot epub exe f4v fbs fh fla
    flac fli flv fpx fst fvt g3 gif graffle gz gzip h261 h263 h264 ico ief img
    ipa iso jar jpeg jpg jpgv jpm jxr key ktx lha lvp lz lzh lzma lzo m3u m4a
    m4v mar mdi mht mid midi mj2 mka mkv mmr mng mobi mov movie mp3 mp4 mp4a
    mpeg mpg mpga mxu nef npx numbers o oga ogg ogv otf pages pbm pcx pdf pea
    pgm pic png pnm pot potm potx ppa ppam ppm pps ppsm ppsx ppt pptm pptx psd
    pya pyc pyo pyv qt rar ras raw rgb rip rlc rmf rmvb rtf rz s3m s7z scpt sgi
    shar sil sketch slk smv so sub swf tar tbz tbz2 tga tgz thmx tif tiff tlz
    ttc ttf txz udf uvh uvi uvm uvp uvs uvu viv vob war wav wax wbmp wdp weba
    webm webp whl wim wm wma wmv wmx woff woff2 wvx xbm xif xla xlam xls xlsb
    xlsm xlsx xlt xltm xltx xm xmind xpi xpm xwd xz z zip zipx
""".split()


class Cache(object):
    """A namespace for caches."""


class URLLoader(object):
    """Supply urls to ``Conf`` object."""

    def __init__(self, conf=None, urls=None, ufile=None):
        self.urls = urls
        self.ufile = ufile
        self.conf = conf

    def build(self):
        pass

    def __call__(self):
        self.build()
        return self.conf


class SampleURLLoader(URLLoader):
    """Get sample urls."""

    SAMPLE_UFILE = 'urls.txt'
    PDFNAME = 'sample.pdf'

    def get_data(self):
        configdir = _get_configdir()
        ufile = os.path.join(configdir, self.SAMPLE_UFILE)
        urls = location.Locations(ufile=ufile).urls
        return urls, ufile

    def build(self):
        urls, ufile = self.get_data()

        pname = self.conf.general.pdfname
        if not pname:
            self.conf.general.pdfname = self.PDFNAME
        self.conf.sites_init(urls=urls)


class ReplaceURLLoader(URLLoader):
    """Preprocess urls before Conf.sites_init."""

    REPLACEFILE = 'urlreplace.txt'

    def get_urls(self):
        userdir = self.conf._userdir
        if not userdir:
            return self.urls
        replacefile = os.path.join(userdir, self.REPLACEFILE)
        urls = location.ReplacementParser(replacefile, self.urls, self.ufile)()
        return urls

    def build(self):
        urls = self.get_urls()
        self.conf.sites_init(urls=urls, ufile=self.ufile)


def _get_pdfname(sites):
    site = list(sites)[0]
    url = site.url
    section = site.section
    length = len(sites)
    return _getpdfname(url, section, length)


def _getpdfname(url, section, length=1):
    parts = urllib.parse.urlsplit(url)
    host = ''
    if parts.netloc:
        domainparts = parts.netloc.replace('www.', '').split('.')[:-1]
        host = max(domainparts, key=len)
        # host = host.encode('ascii').decode('idna')
    path = parts.path.rstrip('/').split('/')[-1]
    query = parts.query[:20]
    if query:
        path = path + '-' + location.slugify(query)
    section = section.split(' : ')[0].replace(os.sep, '_')
    _sam = '_sam_'  # Application sample confings have this prefix.
    section = section[len(_sam):] if section.startswith(_sam) else section

    if section == 'scriptdefault':
        name = host or section
    else:
        name = section

    if length == 1:
        path = path or host
        if name != path:
            path = os.path.basename(path)
            name = name + '-' + path

    return name + '.pdf'


# TODO: refactor
# build a reverse dictionary with match url keys, for faster lookup.
def _checkmacth(url, siteconfig):
    def checkloc(url, matches):
        url = url.lower()
        matches = [
            m for m in matches if fnmatch.fnmatch(url, m.lower())]

        if len(matches) == 0:
            matched = 'http://tosixinch.example.com'  # [scriptdefault]
        elif len(matches) == 1:
            matched = matches[0]
        else:
            matched = sorted(matches, key=checkslash)[-1]
        return matched

    def checkslash(url):
        upath = urllib.parse.urlsplit(url)[2]
        num = len(upath.split('/'))
        if upath == '':
            num = -1
        return num

    t = [[sec, siteconfig[sec]['match']] for sec in siteconfig.sections()]
    matched = checkloc(url, [match for sec, match in t])
    for sec, match in t:
        if match == matched:
            return sec


def _get_configdir():
    return resource_filename('tosixinch', 'data').rstrip(os.sep)


def _get_configs(fmts, args, envs):
    configdir = _get_configdir()

    default_appconfig = os.path.join(configdir, 'fini', '_tosixinch.fini')
    default_siteconfig = os.path.join(configdir, 'fini', '_site.fini')
    sample_siteconfig = os.path.join(configdir, 'site.sample.ini')

    appconf, siteconf = _read_configs(
        default_appconfig, default_siteconfig, fmts, args, envs)

    with open(sample_siteconfig) as f:
        siteconf.read_file(f)

    return configdir, appconf, siteconf


def _read_configs(appconfig, siteconfig, fmts, args, envs):
    """Read appconfig and siteconfig files.

    Option names which start with '*' in appconfig are common options.

    When reading the appconfig file, these '*'s are stripped.
    And when reading the siteconfig file,
    the corresponding options and their 'func' are added.
    """
    common_re = re.compile(r'^\*(.*?)=')
    common_options = {}
    builder = configfetch.FiniOptionBuilder

    def _iterate(f):
        for line in f:
            m = common_re.match(line)
            if m:
                common_options[m.group(1)] = 1  # value (1) is not used
                yield line[1:]
            else:
                yield line

    with open(appconfig) as f:
        cstring = ''.join(_iterate(f))

    appconf = configfetch.fetch(
        cstring, fmts=fmts, args=args, envs=envs, Func=Func,
        option_builder=builder, empty_lines_in_values=False)

    siteconf = configfetch.fetch(
        siteconfig, parser=ZConfigParser,
        fmts=fmts, args=args, envs=envs, Func=Func,
        option_builder=builder, empty_lines_in_values=False)

    for option in common_options:
        siteconf._config['DEFAULT'][option] = ''
        func = appconf._ctx.get(option, {}).get('func')
        if func:
            siteconf._ctx[option] = {}
            siteconf._ctx[option]['func'] = func

    return appconf, siteconf


def _get_user_configs(args, appconf, siteconf):
    if getattr(args, 'nouserdir', None):
        userdir = None
    elif getattr(args, 'userdir', None):
        userdir = args.userdir
        userdir = os.path.expanduser(userdir).rstrip(os.sep)
        if not os.path.isdir(userdir):
            msg = ('userdir: %r is not an existing directory. '
                "It must be full path. '~' and '~user' are expanded.")
            logger.error(msg, userdir)
            raise NotADirectoryError(userdir)
        logger.debug("[userdir] '%s'", userdir)
    else:
        userdir = _check_platform_dirs()

    if userdir:
        appconfigs = sorted(glob.glob(userdir + os.sep + 'tosixinch*.ini'))
        siteconfigs = sorted(glob.glob(userdir + os.sep + 'site*.ini'))
        for appconfig in appconfigs:
            logger.debug('reading user application config: %r', appconfig)
            with open(appconfig) as f:
                appconf.read_file(f)

        for siteconfig in siteconfigs:
            logger.debug('reading user site config: %r', siteconfig)
            with open(siteconfig) as f:
                siteconf.read_file(f)

    return userdir


def _check_platform_dirs():
    """Search platform user config directories.

    Only the most typical ones.
    """
    platform = sys.platform
    home = os.path.expanduser('~')
    if platform not in ('win32', 'darwin'):
        platform = 'others'
        unix_config_home = os.getenv('XDG_CONFIG_HOME',
            os.path.expanduser('~/.config'))

    dirs = {
        'win32': [
            (home, 'AppData', 'Roaming', 'tosixinch'),
            (home, 'AppData', 'Local', 'tosixinch'),
            (home, 'Local Settings', 'Application Data', 'tosixinch'),
            (home, 'Application Data', 'tosixinch'),
        ],
        'darwin': [
            (home, 'Library', 'Application Support', 'tosixinch'),
        ],
        'others': [
            (unix_config_home, 'tosixinch'),
        ],
    }

    for d in dirs[platform]:
        path = os.path.join(*d)
        if os.path.isdir(path):
            return path


class Func(configfetch.Func):
    """Customize configfetch.Func for this application."""

    @configfetch.register
    def plus_binaries(self, value):
        values = self.values
        return configfetch._get_plusminus_values(
            reversed(values), BINARY_EXTENSIONS)


class Sites(location.Locations):
    """An object for ``Site`` iteration."""

    def __init__(self, urls, ufile, conf, siteconf):
        super().__init__(urls, ufile)
        self._conf = conf
        self._siteconf = siteconf
        self._config = siteconf._config
        self._iterobj = (Site, conf, siteconf)

        self._filters = conf.general.add_binary_extensions

    def _filter_urls(self, urls):
        for url in urls:
            parts = url.rsplit('.', maxsplit=1)
            if len(parts) > 1:
                if parts[-1] in self._filters:
                    logger.info('skipping url with binary extension: %r', url)
                    continue
            yield url

    @cached_property
    def urls(self):
        urls = super().urls
        # If urls consists of a single url, It doesn't apply filters.
        if len(urls) == 1:
            return urls
        else:
            return list(self._filter_urls(urls))


class Site(location.Location):
    """Settings for each url."""

    def __init__(self, url, conf, siteconf):
        super().__init__(url)
        self._conf = conf
        self._siteconf = siteconf
        self._config = siteconf._config

        self.INDEX = conf.general.loc_index or self.INDEX
        self.APPENDIX = conf.general.loc_appendix or self.APPENDIX

        self.section = _checkmacth(self.url, self._config)

        _sec = self._get_self()
        self.general = configfetch.Double(_sec, self._conf.general)
        self.style = configfetch.Double(_sec, self._conf.style)

        _conv = getattr(self._conf, self._conf.general.converter)
        self.converter = configfetch.Double(_sec, _conv)

    def _get_self(self):
        return self._siteconf.get(self.section)

    def __getattr__(self, option):
        return self._get_self().get(option)

    @property
    def shortname(self):
        if self.is_local():
            num = int(self.general.trimdirs)
            sep = os.sep
        else:
            num = 2  # remove '_htmls' and host
            sep = '/'
        parts = self.url.split(sep)
        num = min(num, len(parts) - 1)
        return sep.join(parts[num:])

    @cached_property
    def text(self):
        fname = self.fname
        codings = self.general.encoding
        errors = self.general.encoding_errors
        return system.read(fname, codings=codings, errors=errors)


class Conf(object):
    """Manage all configuration data.

    Initialization from the main process takes three phases.

    First, it loads application configs,
    then define commandline argumets.

    Second, after checking possible user config data from commandline,
    ('--userdir' and '--nouserdir'),
    it loads user configs.

    Third, after possible preprocessing of urls,
    It loads urls (by a URLLoader).
    """

    SCRIPTDIR = 'script'
    CSSDIR = 'css'

    def __init__(self, urls=None, ufile=None,
            fmts=None, args=None, envs=None):
        fmts = fmts or {}
        args = args or argparse.Namespace()
        envs = envs or {}
        _confs = _get_configs(fmts, args, envs)
        self._configdir, self._appconf, self._siteconf = _confs

        self._appdir = os.path.dirname(self._configdir)
        self._scriptdir = os.path.join(self._appdir, self.SCRIPTDIR)
        self._cssdir = os.path.join(self._configdir, self.CSSDIR)

        self._cache = Cache()
        self._cache.download = {}  # cache for already downloaded files

        # shortcuts
        self.general = self._appconf.general
        self.style = self._appconf.style

        if urls or ufile:
            self.user_init(args)
            self.sites_init(urls, ufile)

    def user_init(self, args):
        self._userdir = _get_user_configs(
            args, self._appconf, self._siteconf)

        if self._userdir:
            self._user_scriptdir = os.path.join(self._userdir, self.SCRIPTDIR)
            self._user_cssdir = os.path.join(self._userdir, self.CSSDIR)
        else:
            self._user_scriptdir = None
            self._user_cssdir = None

    def sites_init(self, urls=None, ufile=None):
        sites = Sites(urls, ufile, self._appconf, self._siteconf)

        self._urls = sites._urls
        self._ufile = sites._ufile
        self.sites = sites

    @property
    def urls(self):
        return self.sites.urls

    @property
    def converter(self):
        return getattr(self._appconf, self.general.converter)

    @property
    def pdfname(self):
        pname = self.general.pdfname
        if pname:
            return pname
        if not self.urls:
            return DEFAULT_PDFNAME
        return _get_pdfname(self.sites)

    @property
    def pdfsize(self):
        if self.style.orientation == 'landscape':
            return self.style.landscape_size
        else:
            return self.style.portrait_size

    @property
    def pdfratio(self):
        w, h = self.pdfsize.split()
        num_and_unit = r'^([0-9.]+)([A-Za-z]+)?$'
        w, h = [re.sub(num_and_unit, r'\1', size) for size in (w, h)]
        return int(h) / int(w)

    def print_siteconf(self):
        if len(self.sites) == 1:
            site = list(self.sites)[0]
            section = site.section
            general = site.general
            site = site._get_self()
            print('%-12s: %s' % ('section', section))
            for option in sorted(site):
                print('%-12s: %s' % (option, general.get(option)))
        else:
            for site in self.sites:
                print('[%s] %s' % (site.section, site.match))

        blankline = None
        for site in self.sites:
            if site.is_local:
                if not blankline:
                    print()
                    print('local files:')
                    blankline = 'done'
                print(site.shortname)

    def print_appconf(self):
        print('general:')
        for option in self.general:
            print('  %-14s = %s' % (option, self.general.get(option)))
        print('style:')
        for option in self.style:
            print('  %-14s = %s' % (option, self.style.get(option)))
        print('converter:')
        for option in self.converter:
            print('  %-14s = %s' % (option, self.converter.get(option)))

    def print_files(self, opt):
        for site in self.sites:
            if opt == '0':
                print(site.url)
            elif opt == '1':
                print(site.fname)
            elif opt == '2':
                print(site.fnew)
            elif opt == 'all':
                print('%s\t%s\t%s' % (site.url, site.fname, site.fnew))
        if opt == '3':
            print(self.pdfname)
