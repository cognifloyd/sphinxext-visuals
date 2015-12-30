# -*- coding: utf-8 -*-
"""
    visuals.asset.backends.visuals
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This package contains an asset backend that uses the Visuals web service.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from visuals.asset.visual_asset_bridge import VisualAsset
# from visuals.client import VisualsClient
from visuals.rst import visual


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
        asset = VisualAsset(node)

        if node.is_ref():
            response = client.request_asset(asset.id, asset.location, asset.type, asset.options)
        else:
            response = client.request_asset(asset.id, asset.location, asset.type, asset.options,
                                            content_hash=asset.content_hash)
            # response = client.request_asset(asset.asset_id, asset.location, asset.node_type, asset.options,
            #                                 content=asset.content)

        if response.state == response.codes.ok:
            asset.state.requested = True
        elif response.state == response.codes.not_found:
            pass
        elif response.state == response.codes.not_found:
            pass
        elif response.state == response.codes.not_found:
            pass
        else:
            asset.state.error = response.error

        if response.uri:
            asset.state.available = True