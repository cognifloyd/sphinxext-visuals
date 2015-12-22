# -*- coding: utf-8 -*-
"""
    visuals.rst.nodes
    ~~~~~~~~~~~~~~~~~

    ReStructuredText document processing logic

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
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


def fix_types_on_visual_references(app, env):
    """
    If a visual node is a reference, then node['type'] might be incorrect.
    This makes the definition's type take precedence (if defined)

    :param sphinx.application.Sphinx app: Sphinx Application
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    """
    for docname in env.all_docs:
        for node in env.get_doctree(docname).traverse(visual):
            node_type = env.assets.get_type(node['visualid'])
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


    # TODO: This is Serial, use Parallel...
    # from sphinx.util.parallel import ParallelTasks, parallel_available
    # if parallel_available and app.parallel > 1:  # based on sphinx.environment #598
    #   nproc = app.parallel
    #
    # env.asset_tasks = ParallelTasks(nproc)

    for node in doctree.traverse(visual):
        asset_id = node['visualid']
        location = AssetLocation(node['docname'], node['instance'])
        options = assets.get_options(asset_id, location)
        content = node['content_block']
        node_type = node['type']

        asset_status = env.assets_status[(asset_id, location)]

        if node.is_ref():
            response = client.request_asset(asset_id, location, node_type, options)
        else:
            response = client.request_asset(asset_id, location, node_type, options, content_hash=hash(content))
            # response = client.request_asset(asset_id, location, node_type, options, content=content)

        if response.status == response.codes.ok:
            asset_status.requested = True
        elif response.status == response.codes.not_found:
            pass
        elif response.status == response.codes.not_found:
            pass
        elif response.status == response.codes.not_found:
            pass
        else:
            asset_status.error = response.error

        if response.uri:
            asset_status.available = True

