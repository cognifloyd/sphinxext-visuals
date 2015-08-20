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
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image, Figure
from sphinx.util.nodes import set_source_info

from . import utils
from .client import VisualsClient

__version__ = '0.1'


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

    is_figure = False

    def run(self):
        visual_node = visual()
        set_source_info(self, visual_node)

        caption = self.options.pop('caption', None)
        if caption:
            caption = utils.make_caption_for_directive(self, caption)
            self.is_figure = True

        # check child nodes (based on Figure)
        if self.content:
            legend, visual_content = self.separate_legend_from_content()
            if legend:
                self.is_figure = True
        else:
            legend = None
            visual_content = []

        client = VisualsClient
        docname, visualid = self.get_visual_id_info()
        uri = client.geturi(docname, visualid)  # , content_node)

        # check for image type

        # Figure/Image expect the URI to be an argument,
        # then they move it to self.options['uri']
        self.arguments[0] = uri

        # Figure/Image will choke on Visual content
        content_backup = self.content
        self.content = ''

        if self.is_figure:
            # The zeroth element is the figure_node
            figure_node = Figure.run(self)[0]
            for node in (caption, legend):
                if node:
                    figure_node += node
            visual_node += figure_node
        else:
            (image_node,) = Image.run(self)
            visual_node += image_node

        # Restore the content now that Figure/Image are done processing. Is this needed?
        self.content = content_backup

        return [visual_node]

    def get_visual_id_info(self):
        env = self.state.document.settings.env
        """:type env: sphinx.environment.BuildEnvironment"""

        docname = env.docname

        visualid = directives.unchanged_required(self.arguments[0])
        # or use this to get an ID-compatible string
        # name = directives.class_option(self.arguments[0])

        return docname, visualid

    def separate_legend_from_content(self):
        """
        I can't just nested_parse(self.content...) because I want
        to support any directive, even if it is not available locally.
        That bit of rst might just get parsed in an external service
        """
        content_offset = self.content_offset  # This is 0-based
        """:type content_offset: int"""
        content_block = self.content
        """:type content_block: docutils.statemachine.StringList"""
        state = self.state
        """:type state: docutils.parsers.rst.states.Body"""

        # we only use the first legend, don't overwrite. (limit=1)
        [(offset_in_block, directive_offset, directive_name, match)] \
            = utils.list_directives_in_block(content_offset, content_block, type_limit=['legend'], limit=1)

        legend_directive \
            = utils.make_dummy_directive(directive_name, optional_arguments=0, final_argument_whitespace=False)

        block, indent, blank_finish \
            = content_block.get_indented(start=offset_in_block, first_indent=match.end())

        arguments, options, legend_content, legend_content_offset \
            = state.parse_directive_block(block, directive_offset, legend_directive, option_presets={})

        legend = nodes.legend(legend_content)
        state.nested_parse(legend_content, legend_content_offset, legend)

        last_offset = legend_content.offset(-1) - content_offset + 1
        if blank_finish:
            last_offset += 1

        visual_content = content_block[:]
        """copy of content_block that will have legend removed"""
        visual_content.disconnect()  # disconnect from content_block
        del visual_content[offset_in_block:last_offset]
        # legend_block = content_block[offset_in_block:last_offset]

        return legend, visual_content


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

    return {'version': __version__, 'parallel_read_safe': True}
