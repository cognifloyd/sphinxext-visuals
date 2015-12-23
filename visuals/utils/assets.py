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

from collections import namedtuple

from visuals.utils import DeepChainMapWithFallback


AssetTuple = namedtuple('AssetTuple',
                        ['type',      # The asset type (generally, an oembed type)
                         'location',  # an AssetLocation
                         'instances'  # a dict of asset instances
                         ])

AssetLocation = namedtuple('AssetLocation', ['docname', 'instance'])
"""
Identifies the location of a particular instance of an asset in a given doc.
instance is normally 0, unless it is not the first instance of the asset in the doc.
For cases where doc has multiple copies of the same asset.
"""


class AssetOptionsDict(dict):
    """
    A dictionary of asset options that are relevant for asset generation or sizing
    Example keys:
        height
        width
        scale

    Some options are not needed, so we drop them
    """
    explicitly_allowed_keys = ['height', 'width', 'scale']
    filtered_keys = [
        # Image directive:
        'alt', 'align', 'name', 'target', 'class',
        # Figure directive:
        'figwidth', 'figclass',
        # Visual directive
        'caption', 'type'
    ]
    # TODO: This is specific to how it's used in visuals. Make it more general if needed.

    def __init__(self, options):
        assert isinstance(options, dict)
        # TODO: Can this support an iterable too?
        filtered = set(options.keys()) - set(self.filtered_keys)
        for filtered_key in filtered:
            del options[filtered_key]
        super().__init__(options)


class AssetStatus(object):

    def __init__(self):
        self.requested = False
        self.available = False
        self.downloaded = False
        self.error = None


class AssetsDict(dict):
    """
    A dictionary of AssetTuples indexed by asset_id

    Parts of the AssetsDict:
        {asset_id:
            AssetTuple(
                type,
                location=AssetLocation(docname, instance),
                instances={docname:
                    [AssetOptionsDict]  # This is an ordered list of instance options
                }
            )}

    Asset instances includes both definitions and references.
    An asset reference only has location in (docname + index) in AssetTuple.instances.
    An asset definition has its location in AssetTuple.location, not just in instances.
    Assets can have references without definitions, suggesting that the asset is defined externally.

    example access:
        assets['some id'].type
        assets['some id'].location.docname
        assets['some id'].location.instance
        assets['some id'].instances['doc'][0]['height']

    Some logic based on sphinx.util.FilenameUniqDict
    """

    def add_asset(self, docname, asset_id, options, asset_type, is_ref=False):
        asset_options = AssetOptionsDict(options)
        if asset_id in self:
            instances = self[asset_id].instances[docname]
            instance = len(instances)
            instances.append(asset_options)
            if not is_ref and self[asset_id].location is None:
                location = AssetLocation(docname, instance)
                # noinspection PyProtectedMember
                self[asset_id] = self[asset_id]._replace(type=asset_type, location=location)
            return

        if is_ref:
            location = None
            # in the AssetDict, asset_type only applies to asset definitions, not references.
            # node['type'] should still be accessible on reference nodes if needed.
            asset_type = None
        else:
            location = AssetLocation(docname, 0)

        self[asset_id] = AssetTuple(asset_type, location, {docname: [asset_options]})
        return

    def purge_doc(self, docname):
        """
        :param list docname: Exclude all assets related to this docname
        """
        for asset_id, (asset_type, (definition_docname, definition_index), instances) in list(self.items()):
            if docname in instances:
                del instances[docname]
            if definition_docname == docname:
                if not instances:
                    del self[asset_id]
                else:  # the doc that defined this was purged, but something is still using it.
                    # noinspection PyProtectedMember
                    self[asset_id] = self[asset_id]._replace(type=None, location=None)

    def merge_other(self, docnames, other):
        """
        For use during the env-merge-info sphinx event

        :param list docnames: Only include asset instances in these docnames
        :param AssetsDict other: the AssetsDict that should merge into this one
        :return:
        """
        for asset_id, (asset_type, location, instances) in list(other.items()):
            if location and asset_id in self and self[asset_id].location:
                assert self[asset_id].location == location
                # The definition location can only be defined once.
            for doc in instances & docnames:
                for options in instances[doc]:
                    self.add_asset(doc, asset_id, options, asset_type)

    def list_instances(self, docnames=None):
        """
        This returns a list of either all or a filtered set of asset instances.
        If docnames is provided, only the docnames in that list will be included.
        Otherwise, all instances of all assets will be included.

        The list contains tuples of the form:
            (asset_id, AssetLocation(docname, instance_index))

        :param list docnames: Only include asset instances in these docnames
        :return list: list of all asset instances (definitions & references)
        """
        instance_list = []
        for asset_id, (asset_type, location, instances) in list(self.items()):
            for docname in list(instances.keys()):
                if docnames is not None and docname not in docnames:
                    continue
                for index in range(len(instances[docname])):
                    instance_list.append((asset_id, AssetLocation(docname, index)))
        # TODO: Make this a generator instead
        return instance_list

    def list_definitions(self, docnames=None):
        """
        :param list docnames: Only include asset instances in these docnames
        :return list: list of all asset definitions
        """
        def_list = []
        for asset_id, (asset_type, location, instances) in list(self.items()):
            if location is None or docnames is not None and location.docname not in docnames:
                continue
            def_list.append((asset_id, location))
        # TODO: Make this a generator instead
        return def_list

    def list_references(self, docnames=None):
        """
        :param list docnames: Only include asset instances in these docnames
        :return list: list of all asset references
        """
        ref_list = []
        for asset_id, (asset_type, location, instances) in list(self.items()):
            for docname in list(instances.keys()):
                if docnames is not None and docname not in docnames:
                    continue
                for index in range(len(instances[docname])):
                    instance_location = AssetLocation(docname, index)
                    if instance_location is not location:
                        ref_list.append((asset_id, AssetLocation(docname, index)))
        # TODO: Make this a generator instead
        return ref_list

    def get_type(self, asset_id):
        return self[asset_id].type

    def get_instances(self, asset_id, docname):
        return self[asset_id].instances[docname]

    def get_options(self, asset_id, location):
        return self[asset_id].instances[location.docname][location.instance]


class AssetsMetadataDict(DeepChainMapWithFallback):
    """
    The AssetsMetadataDict is a combination of a definition dict and a references dict.
    """

    def __init__(self):
        super().__init__(defs={}, refs={})

    def purge_doc(self, docname, purge_in_fallback=False):
        """
        Moves all docs related to this docname into the fallback, excluding them from
        defs and refs. If purge_in_fallback, then exclude them from the fallback as well.

        :param list docname: Exclude all assets related to this docname
        :param purge_in_fallback: Exclude all assets in fallback too, not just defs and refs.
        """
        for asset in self:  # does not iterate through fallback
            if asset[1].docname == docname:
                if purge_in_fallback:
                    del self[asset]
                else:
                    self.fallback[asset] = self.pop(asset)
                    # TODO: Does purge_doc need to do something different if fallback already has that asset?
                    #       If the docname was deleted (vs just being refreshed) then we'll need to drop this here.

    def merge_other(self, docnames, other):
        """
        For use during the env-merge-info sphinx event

        This makes a (potentially dangerous) assumption:
            if other has it, then it's probably newer, so overwrite anything in this one.
            Therefore, the last other merged wins, even though the order of merging is indeterminate.

        :param list docnames: Only include asset instances in these docnames
        :param AssetsMetadataDict other: the AssetsMetadataDict that should merge into this one
        """
        for asset in other.defs:
            if asset[1].docname in docnames:
                self.defs[asset] = other.defs[asset]
        for asset in other.refs:
            if asset[1].docname in docnames:
                self.refs[asset] = other.refs[asset]
        if other.fallback:
            for asset in other.fallback:
                if asset[1].docname in docnames:
                    self[asset] = other[asset]

    def update_or_init_from_assets(self, assets, default_value=None):
        """
        This uses assets to generate the keys for this dict.
        If there are entries in fallback, use those first, then use default_value.

        If default_value is callable, it will be called each time its used.
        This allows for instantiating a class as each value of the dictionary.

        :param AssetsDict assets: The assets that will initialize the assets_status
        :param default_value: The default value to use when initializing each entry (eg AssetStatus)
        """
        def default():
            if callable(default_value):
                return default_value()
            else:
                return default_value

        # Don't overwrite any pre-existing status
        for asset in assets.list_definitions():
            self.defs.setdefault(asset, self.fallback.pop(asset, default()))
        for asset in assets.list_references():
            self.refs.setdefault(asset, self.fallback.pop(asset, default()))
        if self.fallback:
            # There shouldn't be anything else in fallback at this point unless merging...
            # This logic might be pointless... TODO: test whether this does anything
            fallback = self.fallback
            self.fallback = {}
            for asset in fallback:
                self.setdefault(asset, fallback.pop(asset))
