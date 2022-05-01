
import os
import textwrap

from tosixinch import toc


def check(ulist, expected):
    ulist = [u.strip() for u in ulist.strip().split('\n')]
    expected = textwrap.dedent(expected).split('\n')[1:-1]
    nodes = toc.Nodes(ulist, 'url-toc.txt')
    for node, ref_line in zip(nodes, expected):
        url = node.url.replace(os.path.abspath('.') + os.sep, '')
        data = (_get_indent(node), url)
        line = '%s%s' % data
        if node.last:
            line += ' ]'
        assert line == ref_line


def _get_indent(node):
    if node.title:
        return '    ' * (node.level - 1)
    else:
        return '    ' * node.level 


class TestNodes:

    def test_parse(self):
        """
        Format:
            <'    ' *  DOC_LEVEL> <node.url> <' ]' if node.last>
        """
        ulist = """
            # aaa
            # bbb
            ccc
            ddd
        """
        expected = """
            http://tosixinch.example.com/aaa ]
            http://tosixinch.example.com/bbb
                ccc
                ddd ]
        """
        check(ulist, expected)

        ulist = """
            aaa
            # bbb
            # ccc
            ddd
        """
        expected = """
            aaa ]
            http://tosixinch.example.com/bbb ]
            http://tosixinch.example.com/ccc
                ddd ]
        """
        check(ulist, expected)

        ulist = """
            aaa
            bbb
            # ccc
            # ddd
        """
        expected = """
            aaa ]
            bbb ]
            http://tosixinch.example.com/ccc ]
            http://tosixinch.example.com/ddd ]
        """
        check(ulist, expected)

        ulist = """
            aaa
            # bbb
            ccc
            # ddd
        """
        expected = """
            aaa ]
            http://tosixinch.example.com/bbb
                ccc ]
            http://tosixinch.example.com/ddd ]
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
                bbb ]
            http://tosixinch.example.com/ccc
                ddd ]
        """
        check(ulist, expected)
