
"""Download by ``urllib``, ``pyqt5`` or ``selenium``."""

import logging

from tosixinch import action

logger = logging.getLogger(__name__)

QT_APP = None

# Notes about Qt

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


def start_qt_webengine():
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        msg = ("Error occured while loading pyqt5 'WebEngine' modules.")
        logger.critical(msg)
        raise

    return start_qt_webkit(), QWebEngineView


def start_qt_webkit():
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        msg = ('Error occured while loading pyqt5 modules.'
                "This script uses Qt5 libraries when set 'javascript=yes'")
        logger.critical(msg)
        raise

    return QApplication([])


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


def qt_webengine_init(url, qt_app, QWebEngineView):
    try:
        from PyQt5.QtCore import QEventLoop
        from PyQt5.QtCore import QUrl
    except ImportError:
        msg = ("Error occured while loading pyqt5 'webengine' modules.")
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


class QtDownloader(action.Downloader):
    """Provide common Qt downloader methods."""

    def __init__(self, conf, site):
        super().__init__(conf, site)

        global QT_APP
        if not QT_APP:
            QT_APP = self.start()

        action.add_cleanup(self.cleanup)

    def start(self):
        pass

    def cleanup(self):
        global QT_APP

        if QT_APP:
            end_qt(QT_APP)
            QT_APP = None


class QtWebKitDownloader(QtDownloader):
    """Download by QtWebKit."""

    def start(self):
        return start_qt_webkit()

    def request(self, site):
        logger.info('using Qt5 WebKit...')
        url = site.idna_url
        render = qt_webkit_init(url, QT_APP)
        self.agent = render(url)

    def retrieve(self):
        self.text = self.agent.frame.toHtml()


class QtWebEngineDownloader(QtDownloader):
    """Download by QtWebEngine."""

    def start(self):
        qt_app, self.QWebEngineView = start_qt_webengine()
        return qt_app

    def request(self, site):
        logger.info('using Qt5 WebEngine...')
        url = site.idna_url
        render = qt_webengine_init(url, QT_APP, self.QWebEngineView)
        self.agent = render(url)

    def retrieve(self):
        self.text = self.agent.html


SELENIUM_DRIVER = None


def start_selenium(driver, driver_path=None):
    try:
        from selenium import webdriver
    except ImportError:
        msg = 'Error occured while importing selenium.webdriver package.'
        logger.critical(msg)
        raise

    if driver == 'firefox':
        driver = webdriver.Firefox
        from selenium.webdriver.firefox.options import Options
    elif driver == 'chrome':
        driver = webdriver.Chrome
        from selenium.webdriver.chrome.options import Options

    options = Options()
    options.headless = True

    kwargs = {'options': options}
    if driver_path:
        kwargs['executable_path'] = driver_path

    driver = driver(**kwargs)
    driver.implicitly_wait(10)

    return driver


def end_selenium(driver):
    driver.close()


class SeleniumDownloader(action.Downloader):
    """Download by Selenium."""

    def __init__(self, conf, site):
        super().__init__(conf, site)

        global SELENIUM_DRIVER
        if not SELENIUM_DRIVER:
            SELENIUM_DRIVER = self.start()

        self.agent = SELENIUM_DRIVER
        action.add_cleanup(self.cleanup)

    def start(self):
        driver_paths = {
            'chrome': self._site.general.selenium_chrome_path,
            'firefox': self._site.general.selenium_firefox_path,
        }

        driver = self._site.general.browser_engine[9:]
        driver_path = driver_paths[driver]

        logger.info('using selenium (%s)...', driver)
        return start_selenium(driver, driver_path)

    def cleanup(self):
        global SELENIUM_DRIVER

        if SELENIUM_DRIVER:
            end_selenium(SELENIUM_DRIVER)
            SELENIUM_DRIVER = None

    def request(self, site):
        url = site.idna_url
        self.agent.get(url)

    def retrieve(self):
        self.text = self.agent.page_source


def run(conf, site):
    javascript = site.general.javascript
    browser_engine = site.general.browser_engine

    if javascript:
        if browser_engine == 'webkit':
            QtWebKitDownloader(conf, site).download()
        elif browser_engine == 'webengine':
            QtWebEngineDownloader(conf, site).download()
        elif browser_engine.startswith('selenium-'):
            SeleniumDownloader(conf, site).download()
        else:
            msg = ('Invalid browser_engine option: %r' % browser_engine)
            logger.critical(msg)
            raise ValueError(msg)
    else:
        action.Downloader(conf, site).download()
    logger.info('[url] %s', site.url)
