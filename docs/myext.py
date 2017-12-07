
from docutils import nodes
# from docutils.parsers.rst.directives.admonitions import BaseAdmonition

# class details(nodes.Admonition, nodes.Element): pass

# class Details(BaseAdmonition):
#     node_class = details


def setup(app):
    # app.add_object_type('listing', 'listing')
    app.add_object_type('listing', 'listing', ref_nodeclass=nodes.generated)

    # app.add_node(details)
    # app.add_directive('details', Details)
