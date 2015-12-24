# -*- coding: utf-8 -*-
"""
    visuals.rst.nodes
    ~~~~~~~~~~~~~~~~~

    ReStructuredText document processing logic

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import hashlib

from visuals.rst.nodes import visual
from visuals.utils.assets import AssetLocation
# from visuals.client import VisualsClient


def add_visual_to_assets(visual_node, assets):
    """
    This adds assets to env.assets
    :param visual visual_node: The node to work with.
    :param visuals.utils.assets.AssetsDict assets: The env.assets to add the visuals to
    """
    docname = visual_node['docname']
    asset_id = visual_node['visualid']
    # TODO: Options filtering is done in AssetOptionsDict, but maybe it should be here
    # noinspection PyUnresolvedReferences
    options = visual_node.options
    asset_type = visual_node['type']
    is_ref = visual_node.is_ref()

    # add asset to the asset catalog
    assets.add_asset(docname, asset_id, options, asset_type, is_ref)

    # Make the instance number accessible when parsing the tree
    visual_node['instance'] = len(assets.get_instances(asset_id, docname))
    # Note: every time a doc is purged, all instances in that doc are purged.
    # So, instance numbers should be consistent across runs, based on source order.
    # Since each doc is processed at once, this ordering should be ok in parallel.

    # TODO: Perhaps, if is_ref and definition is available, then mark dependency to definition file in env.dependencies


def fix_types_on_visual_references(doctree, assets):
    """
    If a visual node is a reference, then node['type'] might be incorrect.
    This makes the definition's type take precedence (if defined)
    :param docutils.nodes.document doctree: The doctree of a particular docname in the project
    :param visuals.utils.assets.AssetsDict assets: The list of all assets in the project
    """
    for node in doctree.traverse(visual):
        node_type = assets.get_type(node['visualid'])
        if node_type is None:
            # Then this asset_id doesn't have any definitions.
            # So, leave the defined type as is.
            continue
        elif node.is_ref():
            # All references should match the type on the definition.
            node['type'] = node_type


def process_visuals(app, doctree):
    """
    This should send the request to generate the images storing status/URI if known
    (builder will use placeholder if not done)

    This expects env.assets to be a complete list that will not change.

    :param sphinx.application.Sphinx app: Sphinx Application
    :param nodes.document doctree: The doctree of a particular docname in the project
    :return:
    """
    env = app.builder.env
    """:type env: sphinx.environment.BuildEnvironment"""
    assets = env.assets
    """:type assets: AssetsDict"""

    for node in doctree.traverse(visual):
        node_data = VisualNodeDataHandler(node)

        if node.is_ref():
            response = client.request_asset(node_data.asset_id, node_data.location, node_data.node_type, node_data.options)
        else:
            response = client.request_asset(node_data.asset_id, node_data.location, node_data.node_type, node_data.options,
                                            content_hash=node_data.content_hash)
            # response = client.request_asset(node_data.asset_id, node_data.location, node_data.node_type, node_data.options,
            #                                 content=node_data.content)

        if response.status == response.codes.ok:
            node_data.asset_status.requested = True
        elif response.status == response.codes.not_found:
            pass
        elif response.status == response.codes.not_found:
            pass
        elif response.status == response.codes.not_found:
            pass
        else:
            node_data.asset_status.error = response.error

        if response.uri:
            node_data.asset_status.available = True


def request_asset_metadata(nodes):
    for node in nodes:
        node_data = VisualNodeDataHandler(nodes)
        node_metadata = node_data.get_metadata()


class VisualNodeDataHandler:
    """
    A class that helps with processing visual nodes,
    consolidating much of data gathering logic
    """
    # Variables that should be common across instances
    assets = None
    """:type assets: visuals.utils.assets.AssetsDict"""
    assets_status = None
    """:type assets: visuals.utils.assets.AssetsMetadataDict"""

    @classmethod
    def class_init(cls, assets, assets_status):
        cls.assets = assets
        cls.assets_status = assets_status

    @classmethod
    def class_is_inited(cls):
        return bool(cls.assets and cls.assets_status)

    def __init__(self, node):
        """
        :param visuals.utils.assets.AssetsDict assets: The env.assets to use
        :param visuals.utils.assets.AssetsMetadataDict assets_status: The env.assets_status to use
        """
        if not self.class_is_inited():
            raise Exception('Class was not inited with cls.class_init(...), init it first')

        self.asset_id = node['visualid']
        self.location = AssetLocation(node['docname'], node['instance'])
        self.options = self.assets.get_options(self.asset_id, self.location)
        self.node_type = node['type']

        self.content = node['content_block']
        # content_hash needs to be consistent across Python, PHP, JavaScript, Java, and ...
        self.content_hash = hashlib.md5(self.content)

        self.asset_status = self.assets_status[(self.asset_id, self.location)]
        # TODO:2 Make sure that updating this also updates the copy in assets_status

    def get_metadata(self):
        # TODO:1 I AM HERE (Request metadata here)
        return {}
