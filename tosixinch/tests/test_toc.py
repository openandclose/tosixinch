
import os
import textwrap

from tosixinch import toc


def check(ulist, expected):
    ulist = [u.strip() for u in ulist.strip().split('\n')]
    expected = textwrap.dedent(expected).split('\n')[1:-1]
    nodes = toc.Nodes(ulist, 'dummy-urls.txt', 'dummy-urls-toc.txt')
    result = []
    append = result.append
    for node in nodes.nodes:
        append(_get_simplename(node._root))
        for child in node._children:
            append('    %s' % _get_simplename(child))
        for r, e in zip(result, expected):
            assert r == e


def _get_simplename(name):
    return name.replace(os.path.abspath('.') + os.sep, '')


class TestNodes:

    def test_parse(self):
        """
        Format:
            <'    ' * DOC_LEVEL> <URL>
        """
        ulist = """
            # aaa
            # bbb
            ccc
            ddd
        """
        expected = """
            http://tosixinch.example.com/aaa
            http://tosixinch.example.com/bbb
                ccc
                ddd
        """
        check(ulist, expected)

        ulist = """
            aaa
            # bbb
            # ccc
            ddd
        """
        expected = """
            aaa
            http://tosixinch.example.com/bbb
            http://tosixinch.example.com/ccc
                ddd
        """
        check(ulist, expected)

        ulist = """
            aaa
            bbb
            # ccc
            # ddd
        """
        expected = """
            aaa
            bbb
            http://tosixinch.example.com/ccc
            http://tosixinch.example.com/ddd
        """
        check(ulist, expected)

        ulist = """
            aaa
            # bbb
            ccc
            # ddd
        """
        expected = """
            aaa
            http://tosixinch.example.com/bbb
                ccc
            http://tosixinch.example.com/ddd
        """
        check(ulist, expected)

        ulist = """
            # aaa
            bbb
            # ccc
            ddd
        """
        expected = """
            http://tosixinch.example.com/aaa
                bbb
            http://tosixinch.example.com/ccc
                ddd
        """
        check(ulist, expected)
