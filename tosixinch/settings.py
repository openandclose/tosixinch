
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

from tosixinch import configfetch
from tosixinch import location
from tosixinch.util import transform_xpath
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


def _get_pdfname(sites, minsep):
    site = list(sites)[0]
    url = site.url

    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.replace('www.', '').split('.')[0]
    # host = host.encode('ascii').decode('idna')
    path = parts.path.rstrip('/').split('/')[-1]
    rootpath = parts.path.split('/')[minsep - 1]
    section = site.section.split(' : ')[0]

    if len(sites) == 1:
        name = path or host
        name = os.path.basename(name)
    else:
        if section == 'scriptdefault':
            name = host or rootpath
        else:
            name = section

    pdfname = name + '.pdf'
    return pdfname


# TODO: refactor
# build a reverse dictionary with match url keys, for faster lookup.
def _checkmacth(url, siteconfig):
    def checkloc(url, matches):
        matches = [
            match for match in matches
            if fnmatch.fnmatch(matchstr(url), matchstr(match, True))]

        if len(matches) == 0:
            matched = 'http://tosixinch.example.com'  # [scriptdefault]
        elif len(matches) == 1:
            matched = matches[0]
        else:
            matched = sorted(matches, key=checkslash)[-1]
        return matched

    def matchstr(url, star=False):
        url = ''.join(urllib.parse.urlsplit(url)[1:3])
        if star:
            url = url if url.endswith('*') else url + '*'
        return url.lower()

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


def _get_configs(paths, args, envs):
    configdir = resource_filename('tosixinch', 'data').rstrip(os.sep)

    default_appconfig = os.path.join(configdir, 'tosixinch.default.ini')
    default_siteconfig = os.path.join(configdir, 'site.default.ini')
    sample_siteconfig = os.path.join(configdir, 'site.sample.ini')

    appconf = configfetch.fetch(
        default_appconfig, paths=paths, args=args, envs=envs, Func=Func,
        empty_lines_in_values=False)
    siteconf = configfetch.fetch(
        default_siteconfig, parser=ZConfigParser,
        paths=paths, args=args, envs=envs, Func=Func,
        empty_lines_in_values=False)

    if appconf.general.nouserdir:
        userdir = None
    elif appconf.general.userdir:
        userdir = appconf.general.userdir
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
            appconf.read(appconfig)

        if appconf.general.use_sample:
            siteconf.read(sample_siteconfig)

        for siteconfig in siteconfigs:
            logger.debug('reading user site config: %r', siteconfig)
            siteconf.read(siteconfig)
    else:
        if appconf.general.use_sample:
            siteconf.read(sample_siteconfig)

    return configdir, userdir, appconf, siteconf


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
    def _xpath(self, value):
        # Presuppose 'value' is already a list.
        return [transform_xpath(val) for val in value]

    @configfetch.register
    def _plus_binaries(self, value):
        values = self.values
        return configfetch._get_plusminus_values(
            reversed(values), BINARY_EXTENSIONS)


class Sites(location.Locations):
    """An object for ``Site`` iteratorion."""

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
                    continue
            yield url

    @property
    def urls(self):
        urls = super().urls
        # If urls consists of a single url, It doesn't apply filters.
        if len(urls) == 1:
            return urls
        else:
            return list(self._filter_urls(urls))


class Site(location.Location):
    """Settings for each url."""

    def __init__(self, url, conf, siteconf, platform=sys.platform):
        super().__init__(url, platform)
        self._conf = conf
        self._siteconf = siteconf
        self._config = siteconf._config

        self.section = _checkmacth(self.url, self._config)

        self.general = configfetch.Double(
            self._get_self(), self._conf.general)
        self.style = configfetch.Double(
            self._get_self(), self._conf.style)

    def _get_self(self):
        return self._siteconf.get(self.section)

    def __getattr__(self, option):
        return self._get_self().get(option)


class Conf(object):
    """It possesses all configuration data."""

    def __init__(self, urls=None, ufile=None,
            paths=None, args=None, envs=None):
        paths = paths or {}
        args = args or argparse.Namespace()
        envs = envs or {}
        _confs = _get_configs(paths, args, envs)
        self._configdir, self._userdir, self._appconf, self._siteconf = _confs

        # shortcuts
        self.general = self._appconf.general
        self.style = self._appconf.style
        self.converter = getattr(self._appconf, self.general.converter)

        self._sites_init(urls, ufile)

    def _sites_init(self, urls, ufile):
        sites = Sites(urls, ufile, self._appconf, self._siteconf)

        self._urls = sites._urls
        self._ufile = sites._ufile
        self.sites = sites

        self.minsep = self._get_minsep()

    def _get_minsep(self):
        seps = [len(site.url.split(os.sep)) for site in self.sites]
        return min(seps) - 2

    @property
    def urls(self):
        return self.sites.urls

    @property
    def pdfname(self):
        pname = self.general.pdfname
        if pname:
            return pname
        if not self.urls:
            return DEFAULT_PDFNAME
        return _get_pdfname(self.sites, self.minsep)

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
            print('[%s]' % section)
            for option in sorted(site):
                print('%-12s: %s' % (option, general.get(option)))
            return

        for site in self.sites:
            print('[%s] %s' % (site.section, site.match))

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
