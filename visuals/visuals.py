# -*- coding: utf-8 -*-
"""
    visuals.sphinx_ext
    ~~~~~~~~~~~~~~~~~~

    This package is a namespace package that contains ``visuals``
    an extension for Sphinx.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import absolute_import

from docutils import nodes
from docutils.parsers.rst import directives, Directive
from docutils.parsers.rst.directives.images import Image, Figure

# recording the actual things I'm using in self.state.document.settings.env
from sphinx.environment import BuildEnvironment
# from sphinx.config import Config
# from sphinx.application import Sphinx
from docutils import frontend
from docutils.parsers.rst import states


__version__ = '0.1'


class VisualsClient(object):
    """
    Client for the visuals API. A dummy for now.
    """
    def __init__(self):
        pass

    def geturi(self):
        return 'http://placehold.it/350x150'


class visual(nodes.General, nodes.Element):
    """ A Visual Node """
    pass


class Visual(Figure):
    """
    The Visual Directive

    A visual that should be inserted in the document.

    Based on Figure to reuse image presentation stuff.
    That means this has_content, 1 required argument w/ whitespace
    """

    option_spec = Figure.option_spec.copy()
    option_spec['caption'] = directives.unchanged
    # option_spec['option'] = directives.describe_option_type

    def run(self):
        docname, visualid = self.get_visual_id_info()

        visual_node = visual()

        # pass the node into (self = the directive) to get node.source, node.line
        # sphinx.util.nodes.set_source_info(self, node)

        caption = self.options.pop('caption', None)
        caption = self.make_caption_node(caption)
        nodes.caption(caption) if caption is not None else None
        caption.source = self.source
        caption.line = self.line

        # check child nodes (based on Figure)
        if self.content:
            parsed = visual()     # anonymous container for parsing
            self.state.nested_parse(self.content, self.content_offset, parsed)
            if len(parsed) > 0:
                # use the first legend. Ignore everything else.
                legend_index = parsed.first_child_matching_class(nodes.legend)
                legend = parsed[legend_index]
                if legend_index is not None:
                    del parsed[legend_index]

            # parsed has the description of the visual
            parsed.rawsource

        if isinstance(caption, nodes.caption) or isinstance(legend, nodes.legend):
            is_figure = True

        client = VisualsClient
        uri = client.geturi(docname, visualid, content_node)

        # check for image type

        # Figure/Image expect the URI to be an argument,
        # then they move it to self.options['uri']
        try:
            del self.arguments[0]
        except IndexError:
            pass
        self.arguments[0] = uri
        if is_figure:
            figure_node = Figure.run(self)[0]
            for node in (caption, legend):
                if node:
                    figure_node += node
            visual_node += figure_node
        else:
            (image_node,) = Image.run(self)[0]
            visual_node += image_node

    def get_visual_id_info(self):
        # These assertions tell pycharm what everything is to enable autocomplete
        # They also make my implicit dependencies more explicit.
        assert isinstance(self.state, states.RSTState)                          # docutils.parser.rst
        assert isinstance(self.state.document, nodes.document)                  # docutils
        assert isinstance(self.state.document.settings, frontend.Values)        # docutils
        assert isinstance(self.state.document.settings.env, BuildEnvironment)   # sphinx.environment
        # assert isinstance(self.state.document.settings.env.config, Config)      # sphinx.config
        # assert isinstance(self.state.document.settings.env.app, Sphinx)         # sphinx.application
        assert isinstance(self.state_machine, states.RSTStateMachine)           # docutils

        env = self.state.document.settings.env

        # srcdir = env.srcdir
        # src should be relative to srcdir
        docname = env.docname

        visualid = directives.unchanged_required(self.arguments[0])
        # or use this to get an ID-compatible string
        # name = directives.class_option(self.arguments[0])

        return docname, visualid

    def make_caption_node(directive, caption):
        parsed = nodes.Element()
        self.state.nested_parse(ViewList([caption], source=''),
                                directive.content_offset, parsed)
        caption_node = nodes.caption(parsed[0].rawsource, '',
                                     *parsed[0].children)
        caption_node.source = parsed[0].source
        caption_node.line = parsed[0].line
        container_node += caption_node
        container_node += literal_node

class Legend(Directive):

    has_content = True

    def run(self):
        if not isinstance(self.state.parent, visual):
            return [self.state.document.reporter.warning(
                'Legend Directives can only be used inside Visual Directives',
                line=self.lineno)]
        if self.content:
            node = nodes.Element()          # anonymous container for parsing
            self.state.nested_parse(self.content, self.content_offset, node)



def visit_visual(self, node):
    """
    self is a sphinx/writer/*Translator which implements docutils.nodes.NodeVisitor
    node is a visual node

    I can't just assume that visual=figure,
    because it might be a screencast (or some other oembed) instead of an image

    This should only add any wrapper stuff (divs in html or similar)
    The Translator will call the appropriate visit_* on subnodes as well,
    so we can just pass most of the time.

    Related visitors:
     self.visit_figure
      self.visit_image
      self.visit_caption
      self.visit_legend

    If I need to prevent visit_/depart_ on all children:
    raise nodes.SkipNode
    This might be especially helpful in text writers
    """
    pass


def depart_visual(self, node):
    # See visit_visual
    pass


def setup(app):
    """ sphinx setup """
    app.add_node(visual,
                 html=(visit_visual, depart_visual),
                 latex=(visit_visual, depart_visual),
                 text=(visit_visual, depart_visual))

    app.add_directive('visual', Visual)
    app.add_directive('legend', Legend)

    return {'version': __version__, 'parallel_read_safe': True}
