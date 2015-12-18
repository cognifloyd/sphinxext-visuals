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


class AssetsDict(dict):
    """
    A dictionary of AssetTuples indexed by asset_id

    Parts of the AssetsDict:
        {asset_id:
            AssetTuple(
                type,
                location=AssetLocationTuple(docname, instance),
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
                location = AssetLocationTuple(docname, instance)
                # noinspection PyProtectedMember
                self[asset_id] = self[asset_id]._replace(type=asset_type, location=location)
            return

        if is_ref:
            location = None
            # in the AssetDict, asset_type only applies to asset definitions, not references.
            # node['type'] should still be accessible on reference nodes if needed.
            asset_type = None
        else:
            location = AssetLocationTuple(docname, 0)

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
            (asset_id, AssetLocationTuple(docname, instance_index))

        :param list docnames: Only include asset instances in these docnames
        :return list: list of all asset instances (definitions & references)
        """
        instance_list = []
        for asset_id, (asset_type, location, instances) in list(self.items()):
            for docname in list(instances.keys()):
                if docnames is not None and docname not in docnames:
                    continue
                for index in range(len(instances[docname])):
                    instance_list.append((asset_id, AssetLocationTuple(docname, index)))
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
                    instance_location = AssetLocationTuple(docname, index)
                    if instance_location is not location:
                        ref_list.append((asset_id, AssetLocationTuple(docname, index)))
        return ref_list

    def get_type(self, asset_id):
        return self[asset_id].type

    def get_instances(self, asset_id, docname):
        return self[asset_id].instances[docname]

    def get_options(self, asset_id, location):
        return self[asset_id].instances[location.docname][location.instance]


AssetTuple = namedtuple('AssetTuple',
                        ['type',      # The asset type (generally, an oembed type)
                         'location',  # an AssetLocationTuple
                         'instances'  # an AssetInstancesDict
                         ])

AssetLocationTuple = namedtuple('AssetLocationTuple', ['docname', 'instance'])
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
