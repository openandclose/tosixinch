
import lxml.html

from tosixinch import clean
from tosixinch import lxml_html


def test_conditioned_iter():
    data = '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>'
    expected = [
        '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>',
        '<h3>aaa</h3>',
        '<div><p>bbb<span>ccc</span></p></div>']

    def is_not_p(el):
        if el.tag == 'p':
            return False
        return True

    def compare(module):
        doc = module.fromstring(data)
        output = []
        for el in clean.conditioned_iter(doc, is_not_p):
            output.append(module.tostring(el, encoding='unicode'))
        assert list(output) == expected

    compare(lxml.html)
    compare(lxml_html)


def test_stylematcher():
    data = """
        color: red !important;
        font: bold 16px "DejaVu Sans";
        content: " (" attr(href) ")";
        background: linear-gradient(to right, rgba(255,0,0,0.5) 50% / rgba(0,0,255,0.5) 50%);
    """
    expected = [
        ('color', 'red'),
        ('font', 'bold'),
        ('font', '16px'),
        ('font', '"DejaVu Sans"'),
        ('content', '" (" attr(href) ")"'),
        ('background', 'linear-gradient(to right, rgba(255,0,0,0.5) 50% / rgba(0,0,255,0.5) 50%)'),
    ]

    matches = [
        'font: bold "DejaVu Sans";',
        'content: ;',
    ]
    expected2 = 'font: bold "DejaVu Sans"; content: " (" attr(href) ")"'

    matcher = clean.StyleMatcher(matches)

    decs, raw_props = matcher.build_matches([s.rstrip(';') for s in data.split('\n')])
    decs = [key for key in decs]
    assert decs == expected

    css = matcher.run_matches(data)
    assert css == expected2
