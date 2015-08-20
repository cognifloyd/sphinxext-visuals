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
# TODO: for pending nodes below
# from docutils.transforms import Transform

from . import node_utils
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
        docname, visualid = self.get_visual_id_info()

        visual_node = visual()

        # pass the node into (self = the directive) to get node.source, node.line
        # sphinx.util.nodes.set_source_info(self, node)

        legend = None
        visual_content = []

        caption = self.options.pop('caption', None)
        if caption:
            caption = node_utils.make_caption_for_directive(self, caption)
            self.is_figure = True

        # check child nodes (based on Figure)
        if self.content:
            legend, visual_content = self.separate_legend_from_content()
            if legend:
                self.is_figure = True

        print(visual_content)
        client = VisualsClient
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

        # Restore the content now that Figure/Image are done processing.
        self.content = content_backup

        print(visual_node)

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

        legend = None
        visual_content = content_block[:].disconnect()
        """content_block (disconnected from content_block) that will have legend removed"""
        # TODO: for pending nodes below
        # visual_nodes = nodes.pending(VisualTransform)
        # """visual_content (minimally) converted into a list of nodes"""
        # content_wo_directives = None
        # """content w/o directives"""

        # Find the beginning of the legend block, and process that.
        # Then get the rest of the content, without the legend block.
        directive_pattern = node_utils.make_directive_pattern()
        directives_in_block = []
        # TODO: for pending nodes below
        # nondirective_pattern = node_utils.make_nondirective_pattern()

        # for line in content_block:
        for source, line_offset, line in content_block.xitems():
            offset_in_block = line_offset - content_offset
            directive_first_line_match = directive_pattern.match(line)
            if directive_first_line_match:
                # line_match = directive_first_line_match
                directive_name = directive_first_line_match.group(1)
                # name = directive_name

                # TODO: Remove this when we can create the pending nodes below
                if directive_name != 'legend':
                    # We don't use any other directives yet, so skip.
                    # later, we might need to process them into something else...
                    continue
                directives_in_block.append((offset_in_block, line_offset, directive_name, directive_first_line_match))

            # TODO: a node tree... But, how do I deal with paragraphs and non-directive content?
            # visual_nodes += nodes.pending(
            #     VisualTransform,
            #     details={
            #         'type': 'directive',
            #         'offset_in_block': offset_in_block,
            #         'line_offset': line_offset,
            #         'name': name,
            #         'line_match': line_match
            #     }
            # )

        for (offset_in_block, directive_offset, directive_name, match) in directives_in_block:
            directive_block, directive_indent, blank_finish \
                = content_block.get_indented(start=offset_in_block, first_indent=match.end())

            dummy_directive = Directive(directive_name, None, None, None, None, None, None, None, None)
            # Dummy directive makes reusing state.parse_directive* possible
            # even if the directive is unknown (ie without using directive.run())
            # This is important if the content will be rendered by an external service.
            dummy_directive.has_content = True
            dummy_directive.option_spec = None
            if directive_name != 'legend':
                # If it's not legend, then we don't know what it is.
                # Turn it into one long argument block without options.
                dummy_directive.optional_arguments = 1
                dummy_directive.final_argument_whitespace = True

            directive_arguments, directive_options, directive_content, directive_content_offset \
                = state.parse_directive_block(directive_block, directive_offset, dummy_directive, option_presets={})

            if directive_name == 'legend' and legend is None:  # only use the first legend, don't overwrite.
                legend = nodes.legend(directive_content)
                state.nested_parse(directive_content, directive_content_offset, legend)

                last_offset = directive_content.offset(-1) - content_offset + 1
                if blank_finish:
                    last_offset += 1

                del visual_content[offset_in_block:last_offset]
                # legend_block = content_block[offset_in_block:last_offset]

        return legend, visual_content


# TODO: For pending nodes above
# class VisualTransform(Transform):
#     def apply(self, **kwargs):
#         pass


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
