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
from utils.assets import AssetsDict, AssetsMetadataDict
# from client import VisualsClient

__version__ = '0.1'


def assets_init(app):
    """
    visual assets are externally sourced from some DAM (digital asset manager)
    or are externally generated as would be done through the visuals API.
    That lead to the following design decisions:

    This uses app.env.assets* because both app.builder.images and app.env.images:
    - are too widely used throughout sphinx to modify safely
    - deal with local image files (copy from source files to output)
    - require that the image files exist in the project's source files
    - assume that the image files are relative to the docname that includes them

    This uses AssetsDict instead of FilenameUniqDict because we don't need filenames

    Sphinx's image infrastructure also took care of:
    - select alternative image types
    - image translation
    - additional image-related post processing and transforms
    These might need to be replaced in visuals.

    :param sphinx.application.Sphinx app: Sphinx Application
    """

    # the primary list of all visual assets, extracted from the doctree.
    app.env.assets = AssetsDict()

    # asset generation status (use placeholder if not done)
    app.env.assets_status = AssetsMetadataDict()
    # the final uri or oembed block with info for builder
    app.env.assets_final = AssetsMetadataDict()
    # TODO: Maybe this should be made with a slice from assets_status
    # TODO: Maybe the final stuff should go in the builder


def assets_purge_doc(app, docname):
    """
    This triggers the assets merge in the environment
    :param docname: see AssetsDict.purge_doc
    :param sphinx.application.Sphinx app: Sphinx Application
    """
    app.env.assets.purge_doc(docname)


def assets_add_visual(app, visual_node):
    """
    This triggers the assets merge in the environment
    :param visual visual_node: The node to work with.
    :param sphinx.application.Sphinx app: Sphinx Application
    """
    docname = visual_node['docname']
    asset_id = visual_node['visualid']
    # TODO: Options filtering is done in AssetOptionsDict, but maybe it should be here
    options = visual_node.options
    asset_type = visual_node['type']
    is_ref = visual_node.is_ref()

    app.env.assets.add_asset(docname, asset_id, options, asset_type, is_ref)


def assets_merge(app, docnames, other):
    """
    This triggers the assets merge in the environment
    :param sphinx.application.Sphinx app: Sphinx Application
    :param docnames: see AssetsDict.merge_other
    :param other: see AssetsDict.merge_other
    """
    app.env.assets.merge_other(docnames, other)


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
    app.connect('builder-inited', assets_init)
    app.connect('env-purge-doc', assets_purge_doc)
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

    app.connect('visual-node-generated', assets_add_visual)

    # Phase 1: Reading
    #   docutils transforms
    # app.add_transform(VisualsTransform)

    # NOTE: use transforms (above) to manipulate image nodes:
    # - after source-read event
    # - before process_images (which runs before doctree-read event)

    # Phase 1: Reading
    #   sphinx post-processing
    app.connect('doctree-read', process_visuals)

    # Phase 3: Resolving
    #   sphinx final stage before writing
    app.connect('doctree-resolved', resolve_visuals)
    app.connect('env-merge-info', assets_merge)

    # Phase 4: Writing
    #   docutils writer visitors: see docutils parsing in Phase 1

    return {'version': __version__, 'parallel_read_safe': True}
