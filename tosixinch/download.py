
"""Just download and save html contnet (no decoding).

Either by ``urllib`` or ``pyqt5``.
"""

import http.cookiejar
import gzip
import logging
import time
import urllib.request
import zlib

from tosixinch import system

logger = logging.getLogger(__name__)

QT_APP = None


def download(url, fname,
        user_agent='Mozilla/5.0', cookies=None, on_error_exit=True):
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa: E501
        'Accept-Encoding': 'gzip, deflate',
        # 'Accept-Charset': 'utf-8,*;q=0.1',
        # 'Accept-Language': 'en-US,en;q=0.8',
    }
    # Many things are wrong.
    # http://stackoverflow.com/questions/789856/turning-on-debug-output-for-python-3-urllib  # noqa: E501
    # https://bugs.python.org/issue26892
    debuglevel = 0
    if logger.getEffectiveLevel() == 10:
        debuglevel = 1
    logger.debug("[download] '%s'", url)

    req = urllib.request.Request(url, headers=headers)
    cj = http.cookiejar.CookieJar()
    if cookies:
        for cookie in cookies:
            cj = add_cookie(cj, cookie)

    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(debuglevel=debuglevel),
        urllib.request.HTTPCookieProcessor(cj))

    try:
        with opener.open(req) as f:
            text = f.read()
            if isinstance(f, http.client.HTTPResponse):
                if f.getheader('Content-Encoding') == 'gzip':
                    text = gzip.decompress(text)
                elif f.getheader('Content-Encoding') == 'deflate':
                    logger.info("[http] 'Content-Encoding' is 'deflate'")
                    text = zlib.decompress(text)
            system.write(fname, text=text)

    except urllib.request.HTTPError as e:
        if on_error_exit:
            raise
        if e.code == 404:
            logger.info('[HTTPError 404 %s] %s' % (e.reason, url))
        else:
            logger.warning(
                '[HTTPError %s %s %s] %s' % (
                    e.code, e.reason, e.headers, url))

    except urllib.request.URLError as e:
        if on_error_exit:
            raise
        logger.warning('[URLError %s] %s' % (e.reason, url))

    except http.client.RemoteDisconnected as e:
        if on_error_exit:
            raise
        logger.warning('[RemoteDisconnected: %s] %s' % (str(e), url))


def _add_cookie(cj, name, value, domain, path='/'):
    # cf. http.cookiejar.Cookie signature
    #
    # def __init__(
    #     version, name, value,
    #     port, port_specified,
    #     domain, domain_specified, domain_initial_dot,
    #     path, path_specified,
    #     secure, expires, discard,
    #     comment, comment_url, rest,
    #     rfc2109=False,
    # )
    #
    domain_initial_dot = False
    if domain.startswith('.'):
        domain_initial_dot = True
    expires = time.time() + 60 * 60 * 24 * 2  # 2 days from now

    cookie = http.cookiejar.Cookie(
        0, name, value,
        '80', True,
        domain, True, domain_initial_dot,
        path, True,
        False, expires, False,
        'simple-cookie', None, None,
    )
    cj.set_cookie(cookie)
    return cj


def add_cookie(cj, cookie):
    # 'cookie' is now an unparsed string.
    values = [c.strip() for c in cookie.split(',') if c.strip()] or []
    if len(values) == 3:
        values.append('/')
    name, value, domain, path = values
    return _add_cookie(cj, name, value, domain, path)


# Notes about Qt

# Codes relating ``qt`` are just snippet copies arround the web.

# It seems many stackoverflow answers follow his article.
# https://impythonist.wordpress.com/2015/01/06/ultimate-guide-for-scraping-javascript-rendered-web-pages/  # noqa: E501

# For continuous download
# http://pyqt.sourceforge.net/Docs/PyQt5/gotchas.html
# https://stackoverflow.com/a/33041555

# WebEngine version
# https://stackoverflow.com/a/35245162

# WebEngine import order
# 'ImportError: QtWebEngineWidgets must be imported before a QCoreApplication instance is created'  # noqa: E501
# https://stackoverflow.com/a/41268939

def start_qt(qt_ver):
    QWebEngineView = None
    if qt_ver == 'webengine':
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            msg = ("Error occured while loading pyqt5 'WebEngine' modules.")
            logger.critical(msg)
            raise

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        msg = ('Error occured while loading pyqt5 modules.'
                "This script uses qt5 libraries when set 'javascript=yes'")
        logger.critical(msg)
        raise

    qt_app = QApplication([])
    return qt_app, QWebEngineView


def end_qt(app):
    app.exit()


def qt_webkit_init(url, qt_app):
    try:
        from PyQt5.QtWebKitWidgets import QWebPage
        from PyQt5.QtCore import QUrl
    except ImportError:
        msg = ("Error occured while loading pyqt5 'WebKit' modules.")
        logger.critical(msg)
        raise

    class Render(QWebPage):
        def __init__(self, url):
            self.app = qt_app
            QWebPage.__init__(self)
            self.loadFinished.connect(self._loadfinished)
            self.mainFrame().load(QUrl(url))
            self.app.exec_()

        def _loadfinished(self, result):
            self.frame = self.mainFrame()
            self.app.quit()

    return Render


def qt_webkit_download(url, fname, render):
    logger.info('using Qt5 WebKit...')
    r = render(url)
    html = r.frame.toHtml()

    # cf. QT5 has new method `toHtmlEscaped()`,
    # but pyqt5 doesn't expose `QString`.

    # For now, the way to save the document
    # is left different from urllib download
    # in encoding and escaping.
    # But details are not checked.

    # with open(fname, 'wb') as g:
    with open(fname, 'w') as g:
        g.write(html)


def qt_webengine_init(url, qt_app, QWebEngineView):
    try:
        from PyQt5.QtCore import QEventLoop
        from PyQt5.QtCore import QUrl
    except ImportError:
        msg = ('Error occured while loading pyqt5 modules.')
        logger.critical(msg)
        raise

    class Render(QWebEngineView):
        def __init__(self, html):
            self.html = None
            self.app = qt_app
            QWebEngineView.__init__(self)
            self.loadFinished.connect(self._loadfinished)
            # self.setHtml(html)
            self.page().load(QUrl(url))
            while self.html is None:
                self.app.processEvents(
                    QEventLoop.ExcludeUserInputEvents
                    | QEventLoop.ExcludeSocketNotifiers
                    | QEventLoop.WaitForMoreEvents)
            self.app.quit()

        def _callable(self, data):
            self.html = data

        def _loadfinished(self, result):
            self.page().toHtml(self._callable)

    return Render


def qt_webengine_download(url, fname, render):
    logger.info('using Qt5 WebEngine...')
    r = render(url)
    html = r.html

    with open(fname, 'w') as g:
        g.write(html)


def dispatch(conf):
    global QT_APP

    pre_each_cmd = conf.general.pre_each_cmd1
    post_each_cmd = conf.general.post_each_cmd1
    # downloader = site.general.downloader

    for site in conf.sites:
        returncode = system.run_cmds(pre_each_cmd, conf, site)

        if returncode not in (101, 102):
            run(conf, site)

        if returncode not in (102,):
            returncode = system.run_cmds(post_each_cmd, conf, site)

    if QT_APP:
        end_qt(QT_APP)
        QT_APP = None


def run(conf, site):
    global QT_APP

    user_agent = site.general.user_agent
    qt_ver = site.general.browser_engine

    url = site.idna_url
    fname = site.fname
    js = site.general.javascript
    cookies = site.cookie
    force = site.general.force_download
    cache = conf._cache.download

    if site.check_fname(force=force, cache=cache):
        return
    system.make_directories(fname)

    if js:
        if not QT_APP:
            QT_APP, QWebEngineView = start_qt(qt_ver)
            if qt_ver == 'webengine':
                render = qt_webengine_init(url, QT_APP, QWebEngineView)
                qt_download = qt_webengine_download
            elif qt_ver == 'webkit':
                render = qt_webkit_init(url, QT_APP)
                qt_download = qt_webkit_download
            else:
                msg = ("You have to set option 'browser_engine' to "
                        "either 'webengine' or 'webkit'")
                logger.critical(msg)
                raise KeyError(msg)
        qt_download(url, fname, render)
    else:
        download(url, fname, user_agent, cookies)
    logger.info('[url] %s', url)
