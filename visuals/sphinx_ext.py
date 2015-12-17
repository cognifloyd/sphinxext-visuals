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
from sphinx.util import FilenameUniqDict

from rst.directives import Visual
from rst.nodes import visual
from utils.assets import AssetsDict
# from client import VisualsClient

__version__ = '0.1'


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
