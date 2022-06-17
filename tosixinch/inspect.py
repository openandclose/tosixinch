
"""parse downloaded htmls (dfiles), and do arbitrary things user specified."""

import logging

from tosixinch import action
from tosixinch import system

logger = logging.getLogger(__name__)


class Inspect(action.Extractor):
    """Process original html, extract.Extract's self.root."""

    def load(self):
        self.doc = self.parse()

    def process(self):
        for s in self._site.inspect:
            system.run_function(self._conf._userdir, 'process', self.doc, s)

    def run(self):
        self.load()
        self.process()


def run(conf, sites):
    for site in sites:
        Inspect(conf, site).run()
