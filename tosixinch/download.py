
"""Download by ``urllib`` or ``selenium``."""

import logging

from tosixinch import action

logger = logging.getLogger(__name__)

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
        self.driver, self.driver_path = self.get_driver()

    def get_driver(self):
        driver_paths = {
            'chrome': self._site.general.selenium_chrome_path,
            'firefox': self._site.general.selenium_firefox_path,
        }

        driver = self._site.general.browser_engine[9:]
        driver_path = driver_paths[driver]
        return driver, driver_path

    def start(self):
        global SELENIUM_DRIVER
        if not SELENIUM_DRIVER:
            SELENIUM_DRIVER = start_selenium(self.driver, self.driver_path)
            self.agent = SELENIUM_DRIVER
            action.add_cleanup(self.cleanup)

    def cleanup(self):
        global SELENIUM_DRIVER
        if SELENIUM_DRIVER:
            end_selenium(SELENIUM_DRIVER)
            SELENIUM_DRIVER = None

    def request(self, site):
        self.start()
        logger.info('using selenium (%s)...', self.driver)
        url = site.idna_url
        self.agent.get(url)

    def retrieve(self):
        self.text = self.agent.page_source


class Downloader(action.Downloader):
    """Add logging."""

    def request(self, site):
        logger.info('[url] %s', site.url)
        super().request(site)


def run(conf, site):
    downloader = site.general.downloader
    browser_engine = site.general.browser_engine

    if downloader == 'headless':
        if browser_engine.startswith('selenium-'):
            SeleniumDownloader(conf, site).download()
        else:
            msg = ('Invalid browser_engine option: %r' % browser_engine)
            logger.critical(msg)
            raise ValueError(msg)
    else:
        Downloader(conf, site).download()
