
from docutils import nodes
from docutils.parsers.rst.directives.admonitions import BaseAdmonition

class details(nodes.Admonition, nodes.Element): pass

# from docutils.parsers.rst import directives
# directives.register_directive('details', details)

class Details(BaseAdmonition):
    node_class = nodes.admonition


def setup(app):
    # pass
    app.add_node(details)
    app.add_directive('details', Details)
