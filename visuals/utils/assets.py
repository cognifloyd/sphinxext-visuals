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

from collections import namedtuple, UserDict


class AssetsDict(dict):
    """
    A dictionary of AssetTuples indexed by assetid

    Parts of the AssetsDict:
        {assetid:
            AssetTuple(
                type,
                location=AssetLocationTuple(docname, instance),
                instances={docname:
                    [AssetOptionsDict]  # This is an ordered list of instance options
                }
            )}

    example access:
        assets['some id'].type
        assets['some id'].location.docname
        assets['some id'].location.instance
        assets['some id'].instances['doc'][0]['height']

    Some logic based on sphinx.util.FilenameUniqDict
    """
    def add_asset(self, docname, asset_id, options, asset_type=None):
        asset_options = AssetOptionsDict(options)
        if asset_id in self:
            instances = self[asset_id].instances[docname]
            instance = len(instances)
            instances.append(asset_options)
            if asset_type is not None and self[asset_id].type is None:
                location = AssetLocationTuple(docname, instance)
                self[asset_id] = self[asset_id]._replace(type=asset_type, location=location)
            return

        if asset_type is not None:
            location = None
        else:
            location = AssetLocationTuple(docname, 0)

        self[asset_id] = AssetTuple(asset_type, location, {docname: [asset_options]})
        return

    def purge_doc(self, docname):
        for asset_id, (asset_type, (defdoc, instance), instances) in list(self.items()):
            if docname in instances:
                del instances[docname]
            if defdoc == docname:
                if not instances:
                    del self[asset_id]
                else:  # the doc that defined this was purged, but something is still using it.
                    self[asset_id] = self[asset_id]._replace(type=None, location=None)

    def merge_other(self, docnames, other):
        for asset_id, (asset_type, location, instances) in list(other.items()):
            if location and asset_id in self and self[asset_id].location:
                assert self[asset_id].location == location
                # The definition location can only be defined once.
            for doc in instances & docnames:
                for options in instances[doc]:
                    self.add_asset(doc, asset_id, options, asset_type)


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


class AssetsMetadataDict(UserDict):
    """
    An dictionary that tracks metadata about each asset instance in an AssetsDict.

    This initializes as an empty dict.
    Before using, pass your AssetsDict into populate() which also runs clear().
    """
    def __init__(self):
        self._locked = False
        super().__init__()

    def populate(self, assets):
        self.clear()
        for asset_id, (asset_type, location, instances) in list(assets.items()):
            for docname in list(instances.keys()):
                for index in range(len(instances[docname])):
                    # noinspection PyTypeChecker
                    self[(asset_id, AssetLocationTuple(docname, index))] = None
        self._locked = True

    def clear(self):
        self._locked = False
        super().clear()

    def __setitem__(self, key, value):
        if key in self or self._locked is False:
            self.data[key] = value
        else:
            error
