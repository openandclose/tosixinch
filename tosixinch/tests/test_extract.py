
from tosixinch import extract
from tosixinch import settings

import test_content

fromstring = test_content.fromstring
compare_html = test_content.compare_html


class TestReadabilityExtract:

    def test_imports(self):
        text = """
        <html>
          <head>
            <title>aaa - bbb</title>
          </head>
          <body>
            <h1>xxx</h1>
            <h1>yyy</h1>
            <div>zzz</div>
          </body>
        </html>"""
        expected = """
        <html>
          <head>
            <meta charset="utf-8">
            <title>aaa - bbb</title>
          </head>
          <body>
            <h1>aaa - bbb</h1>
            <h2>xxx</h2>
            <h2>yyy</h2>
            <p>zzz</p>
          </body>
        </html>"""
        if extract.readability:
            conf = settings.Conf(urls=['http://example.com'])
            site = list(conf.sites)[0]
            site.text = text
            c = extract.ReadabilityExtract(conf, site)
            c.build()
            compare_html(c.doc, fromstring(expected))
