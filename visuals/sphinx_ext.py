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
from docutils.statemachine import StringList
from sphinx.util import FilenameUniqDict
from sphinx.util.nodes import set_source_info

from . import utils
from utils.assets import AssetsDict
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

    def __init__(self, name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
        super().__init__(name, arguments, options, content, lineno, content_offset, block_text, state, state_machine)
        self.env = self.state.document.settings.env
        """:type env: sphinx.environment.BuildEnvironment"""
        self.app = self.env.app
        """:type app: sphinx.application.Sphinx"""

    allowed_types = oembed_resource_types = ('photo', 'video', 'link', 'rich')
    """ Inspired by oembed.com """
    default_type = 'photo'
    """override default_type in sub classes with a string from oembed_resource_types"""

    def type(argument):
        # Unbound method used in option_spec; Not a staticmethod; See Image.align
        return directives.choice(argument, Visual.allowed_types)

    option_spec = Figure.option_spec.copy()
    option_spec['caption'] = directives.unchanged
    option_spec['type'] = type
    # option_spec['option'] = directives.describe_option_type

    def run(self):
        visual_node = visual(is_figure=False)
        set_source_info(self, visual_node)
        utils.set_type_info(self, visual_node)

        visual_node['docname'], visual_node['visualid'] = self.get_visual_id_info()
        self.options['name'] = visual_node['visualid']
        self.add_name(visual_node)

        self.emit('visual-node-inited', self, visual_node)

        caption = self.get_caption()
        legend, visual_node['content_block'] = self.get_legend_and_visual_content()
        if caption is not None or legend is not None:
            visual_node['is_figure'] = True

        self.emit('visual-caption-and-legend-extracted', self, visual_node, caption, legend)

        if visual_node['type'] == 'photo':
            uri = self.get_temp_image_uri()
            self.run_figure_or_image_with_uri(uri, visual_node, caption, legend)
            # Replacing image node is not a good option, but we could manipulate uri.
            # for image_node in visual_node.traverse(condition=nodes.image):
            #     image_node['uri'] = something

            # By default, assume it doesn't need a placeholder. Later processing can change this.
            visual_node['placeholder'] == False;
        elif visual_node['type'] == 'video':
            raise NotImplementedError('Visuals does not support videos yet')
        else:
            raise NotImplementedError('Visuals does not support link or rich oembed content yet')

        self.emit('visual-node-generated', self, visual_node)

        return [visual_node]

    def get_visual_id_info(self):
        docname = self.env.docname
        """
        docname is not the same as self.source.
        source is a absolute path/filename.
        docname is the path/filename relative to project (without extension)
        """

        visualid = directives.unchanged_required(self.arguments[0])
        # or use this to get an ID-compatible string
        # name = directives.class_option(self.arguments[0])

        return docname, visualid

    def get_caption(self):
        caption = self.options.pop('caption', None)
        if caption is not None:
            return utils.make_caption_for_directive(self, caption)
        else:
            return None

    def get_legend_and_visual_content(self):
        # check child nodes (based on Figure)
        if self.content:
            return self.separate_legend_from_content()
        else:
            return None, []

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
        directives_list = utils.list_directives_in_block(content_offset, content_block, type_limit=['legend'], limit=1)

        if not directives_list:  # then there is no legend
            return None, content_block

        (offset_in_block, directive_offset, directive_name, match) = directives_list[0]

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

    def get_temp_image_uri(self):
        return self.app.config.visuals_local_temp_image

    def run_figure_or_image_with_uri(self, uri, visual_node, caption_node, legend_node):
        """
        use Figure.run() or Image.run() to fill out these attributes:
            general image attributes: alt, height, width,
            scale (scale for the image - this may require additional processing),
            align (horizontal and vertical alignment),
            name (an [html] name for the node),
            target (node or URI that this image should link to),
            class (any additional [html] classes),
            figwidth (figure specific width),
            figclass (figure specific class)

        Note: If figwidth=='image', PIL will try to open the image.
            PIL will only open the image if it's local, and can be found.

        :param visual visual_node: The node to work with.
        """
        # Figure/Image expect the URI to be an argument,
        # then they move it to self.options['uri']
        argument0_backup = self.arguments[0]
        self.arguments[0] = uri

        # Figure/Image will choke on Visual content
        content_backup = self.content
        self.content = StringList()

        if visual_node['is_figure']:
            # The zeroth element is the figure_node
            figure_node = Figure.run(self)[0]
            for node in (caption_node, legend_node):
                if node is not None:
                    figure_node += node
            visual_node += figure_node
        else:
            (image_node,) = Image.run(self)
            visual_node += image_node

        # Restore the content/arg now that Figure/Image are done processing.
        #   Is this needed?
        self.content = content_backup
        self.arguments[0] = argument0_backup

    def emit(self, event, *args):
        """
        Emit a signal so that other extensions can influence the processing of visual nodes
        """
        # self.app is only available when app.update() is running
        if self.app is not None:
            self.app.emit(event, *args)


def builder_init_for_visuals(app):
    """
    app.builder.images = {}
        "images that need to be copied over (source -> dest)"
        Or, in other words, the image must exist in the source files.
        That doesn't make sense for visuals, because images are externally sourced.

    app.env.images = FilenameUniqDict()
        "map absolute path -> (docname, unique filename)"

    Instead, visuals will add its own map of images.

    :param sphinx.application.Sphinx app: Sphinx Application
    """

    # builder = app.builder
    # """:type builder: sphinx.builders.Builder"""

    # builder.images[candidate] = app.config.visuals_local_temp_image
    # app.env.images.add_file(docname, imgpath)

    # builder.visuals = {}
    # app.env.visuals = FilenameUniqDict()

    app.env.assets = AssetsDict()
    # {assetid: {AssetLocationTuple: status}}
    # app.env.assets_status = {}  # asset generation status (use placeholder if not done)
    # {assetid: {AssetLocationTuple: uri}}
    # app.env.assets_uris = {}  # the final uri or oembed block with info for builder


def process_visuals(app, doctree):
    """
    This should send the request to generate the images
    storing status/URI if known

    :param sphinx.application.Sphinx app: Sphinx Application
    :param nodes.document doctree: The doctree of all docs in the project
    :return:
    """
    env = app.builder.env
    """:type env: sphinx.environment.BuildEnvironment"""

    if not hasattr(env, 'visuals'):
        env.visuals = FilenameUniqDict()
    for node in doctree.traverse(visual):
        env.visuals.add_file(env.docname, node['visualid'])


def resolve_visuals(app, doctree, docname):
    """
    This should recheck for any visuals that need to be rendered
    For those, it sends the full visual content (if needed)
    and marks the visual as a placeholder

    :param sphinx.application.Sphinx app: Sphinx Application
    :param nodes.document doctree: The doctree of all docs in the project
    :param str docname: the path/filename relative to project (without extension)
    :return:
    """
    for node in doctree.traverse(visual):
        visual['placeholder'] = True
    pass


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
    # client = VisualsClient()
    # node['uri'] = client.geturi(node)
    # the client could modify node['type'] here, right?

    if node['placeholder']:
        for image in node.traverse(nodes.image):
            image['uri'] = placeholderuri
    pass


def depart_visual(self, node):
    # See visit_visual
    pass


def setup(app):
    """ sphinx setup that runs before builder is loaded
    :param sphinx.application.Sphinx app: Sphinx Application
    """
    # Phase 0: Initialization
    #   sphinx init
    app.connect('builder-inited', builder_init_for_visuals)
    app.add_config_value('visuals_local_temp_image', 'http://example.com/placeholder-uri', 'env')

    # Phase 1: Reading
    #   docutils parsing (and writer visitors in Phase 4)
    app.add_node(visual,
                 html=(visit_visual, depart_visual),
                 latex=(visit_visual, depart_visual),
                 text=(visit_visual, depart_visual))

    app.add_directive('visual', Visual)
    app.add_event('visual-node-inited')
    app.add_event('visual-caption-and-legend-extracted')
    app.add_event('visual-node-generated')

    # Phase 1: Reading
    #   docutils transforms
    # app.add_transform(VisualsTransform)

    # Phase 1: Reading
    #   sphinx post-processing
    app.connect('doctree-read', process_visuals)

    # Phase 3: Resolving
    #   sphinx final stage before writing
    app.connect('doctree-resolved', resolve_visuals)

    # Phase 4: Writing
    #   docutils writer visitors: see docutils parsing section.

    return {'version': __version__, 'parallel_read_safe': True}
