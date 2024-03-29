
from tosixinch import content
from tosixinch import location
from tosixinch import lxml_html

fromstring = lxml_html.fromstring
tostring = lambda el: lxml_html.tostring(el, encoding='unicode')


# cf.
# https://bitbucket.org/ianb/formencode/src/tip/formencode/doctest_xml_compare.py
# https://github.com/formencode/formencode/blob/master/formencode/doctest_xml_compare.py
def compare_html(doc1, doc2):
    for x, y in zip(doc1.iter(), doc2.iter()):
        assert x.tag == y.tag
        assert (x.text or '').strip() == (y.text or '').strip()


class TestBlankHtml:

    def test(self):
        expected = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>notitle</title>
  </head>
  <body>

  </body>
</html>
""".strip()
        html = content.build_new_html()
        assert tostring(html.getroottree()) == expected


class _TestRelinkComponent:
    url = 'aaa/bb/cc'
    base = 'xxx/yy'

    def run(self, url):
        doc = fromstring('<body><img src=%s></body>' % url)
        content._relink_component(doc, self.base, self.url)
        return doc

    def test(self):
        url = '../ss/tt'
        doc = self.run(url)
        assert doc.get('src') == '../aaa/ss/tt'

    def test_external_domain(self):
        url = '../../sss/tt/uu'
        doc = self.run(url)
        assert doc.get('src') == '../sss/tt/uu'


class TestResolver:

    urls = (
        'http://h/a/b/c.html',
        'http://h/a/b/?q',
        'http://h/a/b/c.html?q',
        'http://h/a/b/d.html',
        'http://h/a/b/e.html',
    )
    locs = [location.Location(url) for url in urls]

    def compare(self, doc, xpath, expected):
        selected = doc.xpath(xpath)
        assert selected[0] == expected

    def resolve(self, doc):
        doc = fromstring(doc)
        resolver = content.Resolver(doc, self.locs[0], self.locs)
        resolver.resolve()
        return resolver.doc

    def test_same(self):
        doc = """
        <!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
            <div id="blank">        <a href="">            blank</a></div>
            <div id="blank-query">  <a href="?">           blank-query</a></div>
            <div id="blank-frag">   <a href="#">           blank-frag</a></div>

            <div id="query">        <a href="?q">          query</a></div>
            <div id="query2">       <a href="?q2">         query2</a></div>
            <div id="frag">         <a href="#f">          frag</a></div>
        </body></html>
        """
        doc = self.resolve(doc)

        self.compare(doc, '//div[@id="blank"]/a/@href',         '')
        # urllib.parse strips '?' with blank query
        # self.compare(doc, '//div[@id="blank-query"]/a/@href',   'c.html%3F')
        self.compare(doc, '//div[@id="blank-frag"]/a/@href',    '#')

        self.compare(doc, '//div[@id="query"]/a/@href',         'c.html%3Fq')
        self.compare(doc, '//div[@id="query2"]/a/@href',        'http://h/a/b/c.html?q2')
        self.compare(doc, '//div[@id="frag"]/a/@href',          '#f')

    def test_same_dot(self):
        doc = """
        <!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
            <div id="dot">        <a href=".">              dot</a></div>
            <div id="dot-query">  <a href=".?">             dot-query</a></div>
            <div id="dot-frag">   <a href=".#">             dot-frag</a></div>

            <div id="query">      <a href=".?q">            query</a></div>
            <div id="query2">     <a href=".?q2">           query2</a></div>
            <div id="frag">       <a href=".#f">            frag</a></div>
        </body></html>
        """
        doc = self.resolve(doc)

        self.compare(doc, '//div[@id="dot"]/a/@href',           'http://h/a/b/')
        # urllib.parse strips '?' with blank query
        # self.compare(doc, '//div[@id="dot-query"]/a/@href',     'http://h/a/b/?')  # noqa: E501
        self.compare(doc, '//div[@id="dot-frag"]/a/@href',      'http://h/a/b/#')

        self.compare(doc, '//div[@id="query"]/a/@href',         '%3Fq')
        self.compare(doc, '//div[@id="query2"]/a/@href',        'http://h/a/b/?q2')
        self.compare(doc, '//div[@id="frag"]/a/@href',          'http://h/a/b/#f')

    def test_same_dot_slash(self):
        doc = """
        <!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
            <div id="dot">        <a href="./">              dot</a></div>
            <div id="dot-query">  <a href="./?">             dot-query</a></div>
            <div id="dot-frag">   <a href="./#">             dot-frag</a></div>

            <div id="query">      <a href="./?q">            query</a></div>
            <div id="query2">     <a href="./?q2">           query2</a></div>
            <div id="frag">       <a href="./#f">            frag</a></div>
        </body></html>
        """
        doc = self.resolve(doc)

        self.compare(doc, '//div[@id="dot"]/a/@href',           'http://h/a/b/')
        # self.compare(doc, '//div[@id="dot-query"]/a/@href',     'http://h/a/b/?')  # noqa: E501
        self.compare(doc, '//div[@id="dot-frag"]/a/@href',      'http://h/a/b/#')

        self.compare(doc, '//div[@id="query"]/a/@href',         '%3Fq')
        self.compare(doc, '//div[@id="query2"]/a/@href',        'http://h/a/b/?q2')
        self.compare(doc, '//div[@id="frag"]/a/@href',          'http://h/a/b/#f')

    def test_other(self):
        doc = """
        <!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
            <div id="sib">          <a href="d.html">               sib</a></div>
            <div id="sib-query">    <a href="d.html?q">             sibi-query</a></div>
            <div id="sib-frag">     <a href="d.html#f">             sib-frag</a></div>
            <div id="sib-slash">    <a href="/a/b/e.html">          sib-slash</a></div>
            <div id="sib-slash2">   <a href="//h/a/b/e.html">       sib-slash2</a></div>

            <div id="img">          <img src="http://h/a/x.jpg">    </div>
            <div id="img-slash">    <img src="/a/x.jpg">            </div>
            <div id="img-slash2">   <img src="//h/a/x.jpg">         </div>
            <div id="img-rel">      <img src="../x.jpg">            </div>
        </body></html>
        """
        doc = self.resolve(doc)

        self.compare(doc, '//div[@id="sib"]/a/@href',           'd.html')
        self.compare(doc, '//div[@id="sib-query"]/a/@href',     'http://h/a/b/d.html?q')
        self.compare(doc, '//div[@id="sib-frag"]/a/@href',      'd.html#f')
        self.compare(doc, '//div[@id="sib-slash"]/a/@href',     'e.html')
        self.compare(doc, '//div[@id="sib-slash2"]/a/@href',    'e.html')

        self.compare(doc, '//div[@id="img"]/img/@src',          '../x.jpg')
        self.compare(doc, '//div[@id="img-slash"]/img/@src',    '../x.jpg')
        self.compare(doc, '//div[@id="img-slash2"]/img/@src',   '../x.jpg')
        self.compare(doc, '//div[@id="img-rel"]/img/@src',      '../x.jpg')


class TestIDTable:

    def check(self, t, child, url, expected):
        assert t.get(child, url) == expected

    def test_id(self):
        table = (
            ('x',        ['a', 'b/bb']),
            ('y/yy',     ['c', 'd/dd/ddd']),
        )
        t = content.IDTable(table)

        self.check(t, 'a',  '',             '#a')
        self.check(t, 'a',  '#',            '#a')
        self.check(t, 'a',  '#f',           '#f')
        self.check(t, 'a',  'p#f',          'p#f')
        self.check(t, 'a',  'b/bb#f',       '#f')
        self.check(t, 'a',  'c#f',          'y/yy#f')
        self.check(t, 'a',  'd/dd/ddd#f',   'y/yy#f')

        self.check(t, 'b/bb',   '',                 '#bb')
        self.check(t, 'b/bb',   '#',                '#bb')
        self.check(t, 'b/bb',   '#f',               '#f')
        self.check(t, 'b/bb',   'p#f',              'p#f')
        self.check(t, 'b/bb',   '../a#f',           '#f')
        self.check(t, 'b/bb',   '../c#f',           'y/yy#f')
        self.check(t, 'b/bb',   '../d/dd/ddd#f',    'y/yy#f')
