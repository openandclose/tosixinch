
import lxml.html
import pytest

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
