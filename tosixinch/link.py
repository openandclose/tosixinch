
"""Get inner links in a page, reading from site configuration.

Not developed now.

The idea is that since we already built configurations
for each site of our particular interest,
it can be used to register some site-specific procedures.
"""

import logging
import urllib.parse

from tosixinch.util import lxml_open

logger = logging.getLogger(__name__)


def getlinks(conf):
    links = []
    for site in conf.sites:
        fname = site.fname
        path = site.link
        links.append(getlink(fname, path))
        links.append('')
    return links


def getlink(url, path):
    root = lxml_open(url)
    links = root.xpath(path)
    links = [urllib.parse.urljoin(url, link.strip()) for link in links]
    return links


def print_links(conf):
    links = getlinks(conf)
    for link in links:
        for line in link:
            print(line)
