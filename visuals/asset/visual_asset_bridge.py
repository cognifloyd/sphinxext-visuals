# -*- coding: utf-8 -*-
"""
    visuals.asset.visual_asset_bridge
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains a bridge between the restructured text Visual, and the underlying asset concept.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import hashlib

from visuals.asset import AssetLocation
from visuals.asset.statemachine import AssetState


class AssetOptionsDict(dict):
    """
    A dictionary of asset options that are relevant for asset generation or sizing
    Example keys:
        height
        width
        scale

    Some options are not needed, so we drop them
    """
    # unused for now, but included for reference:
    # explicitly_allowed_keys = ['height', 'width', 'scale']
    filtered_keys = [
        # Image directive:
        'alt', 'align', 'name', 'target', 'class',
        # Figure directive:
        'figwidth', 'figclass',
        # Visual directive
        'caption', 'type'
    ]
    # NOTE: This is specific to how it's used in visuals.
    #       Make it more general if needed.

    def __init__(self, options):
        assert isinstance(options, dict)
        filtered = set(options.keys()) - set(self.filtered_keys)
        options_filtered = options.copy()
        for filtered_key in filtered:
            del options_filtered[filtered_key]
        super().__init__(options_filtered)


class VisualAsset(object):
    """
    An asset representation of the visual node.

    Not all asset data comes from the node, so, this asset
    retrieves gets its data from wherever it needs to.

    This is not meant to be persisted, but is an in-memory
    representation to help with node processing.
    """
    # Variables that should be common across instances
    assets = None
    """:type assets: visuals.asset.AssetsDict"""
    assets_state = None
    """:type assets_state: visuals.asset.AssetsMetadataDict"""

    @classmethod
    def class_init(cls, assets, assets_state):
        cls.assets = assets
        cls.assets_state = assets_state

    @classmethod
    def class_is_inited(cls):
        return bool(cls.assets and cls.assets_state)

    def __init__(self, node):
        """
        Initializes this in memory asset, and adds relevant info to the assets dict
        :param visual node: The visual node.
        """
        if not self.class_is_inited():
            raise Exception('Class was not inited with cls.class_init(...), init it first')

        self.node = node

        self.is_ref = node.is_ref()

        if not self.is_ref:
            self.content = node['content_block']
            # content_hash needs to be consistent across Python, PHP, JavaScript, Java, and ...
            self.content_hash = hashlib.md5(self.content)

        self.id = node['visualid']
        self.type = node['type']
        docname = node['docname']
        self.options = AssetOptionsDict(node.options)
        # once initialized with add_asset (below), this can also be retrieved with:
        # assets.get_options(self.id, self.location)

        if 'instance' not in node:  # Then the node has not been registered in assets.

            self.assets.add_asset(docname, self.id, self.options, self.type, self.is_ref)

            # Make the instance number accessible when parsing the tree
            node['instance'] = len(self.assets.get_instances(self.id, docname))
            # Note: every time a doc is purged, all instances in that doc are purged.
            # So, instance numbers should be consistent across runs, based on source order.
            # Since each doc is processed at once, this ordering should be ok in parallel.

        self.location = AssetLocation(docname, node['instance'])

        # Since assets was just barely populated, assets_state will only be populated if it was
        # pickled with a previous run. Getting now probably won't work, so set it if needed.
        asset_state_key = (self.id, self.location)

        self.state = self.assets_state.get(asset_state_key, None)
        """:type self.state: visuals.asset.statemachine.AssetState"""

        if self.state is None:
            if self.is_ref:
                self.state = self.assets_state.refs.setdefault(asset_state_key, AssetState())
            else:
                self.state = self.assets_state.defs.setdefault(asset_state_key, AssetState())