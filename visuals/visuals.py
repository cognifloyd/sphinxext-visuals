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

import re
from docutils import nodes
from docutils.parsers.rst import directives, Directive
from docutils.parsers.rst.directives.images import Image, Figure

# recording the actual things I'm using in self.state.document.settings.env
from sphinx.environment import BuildEnvironment
# from sphinx.config import Config
# from sphinx.application import Sphinx
from docutils import frontend  # , statemachine
from docutils.statemachine import StringList
from docutils.parsers.rst import states

from . import node_utils


__version__ = '0.1'


class VisualsClient(object):
    """
    Client for the visuals API. A dummy for now.
    """
    def __init__(self):
        pass

    def geturi(docname, visualid):
        return 'http://placehold.it/350x150?text=' + docname + '.' + '+'.join(visualid.split())


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
        caption = self.options.pop('caption', None)
        if caption:
            caption = node_utils.make_caption_for_directive(self, caption)
            self.is_figure = True

        # check child nodes (based on Figure)
        print('\ncontent check')
        if self.content:
            legend, visual_content = self.separate_legend_from_content(self.content)
            if legend:
                self.is_figure = True

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

        # print(visual_node)

        return [visual_node]

    def get_visual_id_info(self):
        # These assertions tell pycharm what everything is to enable autocomplete
        # They also make my implicit dependencies more explicit.
        assert isinstance(self.state, states.RSTState)                          # docutils.parser.rst.states.Body
        assert isinstance(self.state.document, nodes.document)                  # docutils
        assert isinstance(self.state.document.settings, frontend.Values)        # docutils
        assert isinstance(self.state.document.settings.env, BuildEnvironment)   # sphinx.environment
        # assert isinstance(self.state.document.settings.env.config, Config)      # sphinx.config
        # assert isinstance(self.state.document.settings.env.app, Sphinx)         # sphinx.application
        assert isinstance(self.state_machine, (states.RSTStateMachine, states.NestedStateMachine))          # docutils

        env = self.state.document.settings.env

        # srcdir = env.srcdir
        # src should be relative to srcdir
        docname = env.docname

        visualid = directives.unchanged_required(self.arguments[0])
        # or use this to get an ID-compatible string
        # name = directives.class_option(self.arguments[0])

        return docname, visualid

    def separate_legend_from_content(self, content):
        """
        I can't just nested_parse(self.content...) because I want
        to support any directive, even if it is not available locally.
        That bit of rst might just get parsed somewhere else.
        That means that I have to:
            regex through to find the start of any legend directives,
            look at the indent
            find where it dedents
            pop off everything between start and dedent and:
                nested_parse that to generate legend.


        I can use StateMachineWS to get current indent.
        """

        legend = None
        visual_content = None

        sm = self.state_machine
        """:type sm: states.NestedStateMachine"""
        state = self.state
        """:type state: states.Body"""

        # self.lineno           # 1-based start line
        # sm.abs_line_number()  # 1-based end line (the blank line)
        # sm.abs_line_offset()  # 0-based end line (the blank line)
        # self.content_offset   # 0-based start of content (after blank line)
        # self.content          # content lines excluding initial/final blank lines
        # self.blocktext        # text from ".. visual::" including last blank line
        # sm.input_offset       # 0-based start of input lines

        # save for later
        content_start_offset = self.content_offset  # 0-based lineno of content start
        content_end_offset = sm.abs_line_offset()   # 0-based lineno of content end

        sm.goto_line(content_start_offset)
        block, indent, line_offset, blank_finish = sm.get_indented()
        """:type block: StringList"""
        sm.goto_line(content_start_offset)

        # Find the beginning of the legend block, and process that.
        # Then get the rest of the content, without the legend block.
        directive_pattern = node_utils.make_directive_pattern()
        directives_in_block = []
        # (lineno, directive_name, match)
        for line in block:
            directive_first_line_match = directive_pattern.match(line)
            if directive_first_line_match:
                print(type(block))
                # group 0: the whole line
                # group 1: directive name
                # group 2: whitespace after ::
                directive_name = directive_first_line_match.group(1)
                directives_in_block.append((line, directive_name, directive_first_line_match))

        if len(directives_in_block) > 0:
            for (line, directive_name, match) in directives_in_block:

                dummy_directive = Directive(directive_name, None, None, None, None, None, None, state, sm)
                # Dummy directive makes reusing state.parse_directive* possible
                # even if the directive is unknown (ie without using directive.run())
                dummy_directive.optional_arguments = 1
                dummy_directive.final_argument_whitespace = True
                dummy_directive.has_content = True
                dummy_directive.option_spec = None

                # directive_has_whitespace = directive_first_line_match.start(2) != directive_first_line_match.end(2)

                directive_indented, directive_indent, directive_line_offset, directive_blank_finish \
                    = sm.get_first_known_indented(indent + match.end(), strip_top=0)
                # print(sm.abs_line_offset())
                # print(sm.abs_line_number())
                # print(self.content_offset)
                # print(indent + directive_first_line_match.end())
                print(block)
                print(directive_indented)

                # arguments, options, content, content_offset \
                #     = state.parse_directive_block(directive_indented,
                #         line_offset,
                #         dummy_directive,
                #         option_presets
                #     )

        # state.parse_directive_arguments()
        # state.parse_directive_block()
        # state.parse_directive_options()

        # restore saved position
        sm.goto_line(content_end_offset)

        # print(sm.get_text_block())  # not helpful
        # indented, indent, offset, blank_finish = sm.get_indented()
        # print(offset)
        # print(sm.get_first_known_indented(4))
        # print(sm.get_known_indented(4))
        # print(sm.line())

        # sm.previous_line(5)  # up 5 lines

        parsed = visual()     # anonymous container for parsing (must be visual to support legend)
        # unknown_directive_orig = states.Body.unknown_directive
        # states.Body.unknown_directive = unknown_directive
        self.state.nested_parse(self.content, self.content_offset, parsed)
        # states.Body.unknown_directive = unknown_directive_orig

        if len(parsed) > 0:
            # use the first legend. Ignore everything else.
            legend = parsed.next_node(nodes.legend)

            # parsed.rawsource
            # self.block_text (includes .. visual::)
            # self.content (a list of lines in content portion dedented)
            # self.content_offset (lineno in file from top)
            # self.lineno (line in file of .. visual::)
            # print(parsed)

            # parsed has the description of the visual
            # parsed.rawsource

        return legend, visual_content


def unknown_directive(self, type_name):
    indented, indent, offset, blank_finish = \
        self.state_machine.get_first_known_indented(0, strip_indent=False)
    return [], blank_finish


class Legend(Directive):

    has_content = True

    def run(self):
        if not isinstance(self.state.parent, visual):
            return [self.state.document.reporter.warning(
                'Legend Directives can only be used inside Visual Directives',
                line=self.lineno)]
        if self.content:
            legend_node = nodes.legend(self.content)
            self.state.nested_parse(self.content, self.content_offset, legend_node)

        return [legend_node]


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
