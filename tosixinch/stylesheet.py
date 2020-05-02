
"""Create stylesheet files."""

import logging
import os
import re

from tosixinch import cached_property
from tosixinch import templite

logger = logging.getLogger(__name__)

TEMPLATE_EXT = '.t.css'
SAMPLE = 'sample'

_cache = {}


def _get_scale_func(scale):  # length and percentage
    def func(css_size):
        m = re.match(r'(?:\+?)([0-9]+)([A-Za-z]*)', css_size)
        num, unit = m.group(1), m.group(2)
        num = int(num) * float(scale)
        return str(round(num, 4)) + unit
    return func


def _add_percent_scale_func(context, percent):
    # add percent-scale function to context, e.g. percent80(20) -> 16
    key = 'percent%02d' % percent
    context[key] = _get_scale_func(percent / 100)


class StyleSheet(object):
    """Create stylesheet files from configuration."""

    def __init__(self, conf, site=None):
        if site:
            self.css = site.general.css
        else:
            self.css = conf.converter.css2
        self.style = conf.style
        self.pdfsize = conf.pdfsize
        self._cssdir = conf._cssdir
        self._user_cssdir = conf._user_cssdir
        self._conf = conf
        self._site = site

    @property
    def stylesheets(self):
        yield from self._get_paths()

    @cached_property
    def context(self):
        return self._build_context()

    def _get_paths(self):
        # build css files if necessary, and yield filepaths
        for name in self.css:
            if name == SAMPLE:
                name = SAMPLE + TEMPLATE_EXT

            if name in _cache:
                if _cache[name]:
                    yield _cache[name]
                continue

            _cache[name] = self._get_file(name)
            if _cache[name]:
                yield _cache[name]

    def _get_file(self, name):
        for d in (self._user_cssdir, self._cssdir):
            if d:
                path = os.path.join(d, name)
                if os.path.isfile(path):
                    if name.endswith(TEMPLATE_EXT):
                        return self.render_template(name, path)
                    else:
                        return path

    def render_template(self, name, path):
        new_name = name[:-len(TEMPLATE_EXT)] + '.css'
        if self._user_cssdir:
            new_path = os.path.join(self._user_cssdir, new_name)
        else:
            new_path = new_name  # current directory

        return self._render_template(path, new_path, self.context)

    def _render_template(self, path, new_path, context):
        with open(path) as f:
            template = f.read()
        template = templite.Templite(template)
        text = template.render(context)
        with open(new_path, 'w') as f:
            f.write(text)
        return new_path

    def _build_context(self):
        context = {key: self.style.get(key) for key in self.style}

        context['size'] = self.pdfsize
        context['scale'] = _get_scale_func(self.style.font_scale)

        sizes = self.pdfsize.split()
        if len(sizes) == 2:
            context['width'], context['height'] = sizes

        for i in range(80, 100):
            _add_percent_scale_func(context, i)

        using = lambda x: self._conf.converter.name == x
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
