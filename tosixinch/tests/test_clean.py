
import lxml.html
import pytest

from tosixinch import clean

fromstring = lxml.html.fromstring
tostring = lambda el: lxml.html.tostring(el, encoding='unicode')


class TestFilteredIter:

    def test(self):
        data = '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>'
        expected = [
            '<div><h3>aaa</h3><div><p>bbb<span>ccc</span></p></div></div>',
            '<h3>aaa</h3>',
            '<div><p>bbb<span>ccc</span></p></div>']

        def is_not_p(el):
            if el.tag == 'p':
                return False
            return True

        doc = fromstring(data)
        output = []
        for el in clean.conditioned_iter(doc, is_not_p):
            output.append(tostring(el))
        assert list(output) == expected
