# -*- coding: utf-8 -*-
"""
    visuals.utils
    ~~~~~~~~~~~~~

    Utility functions for Visuals

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import ChainMap


class DeepChainMapWithFallback(ChainMap):
    """
    Variant of ChainMap that allows direct updates to inner scopes. Based on DeepChainMap from:
    https://docs.python.org/3/library/collections.html#chainmap-examples-and-recipes

    This modifies the above mentioned DeepChainMap as follows:
    * allows updates to the given dicts, but does not add any new keys
    * if a new key is used, it is redirected to fallback.
    * if a key is deleted, it will be deleted from both fallback and the other dict.
    * maps may be named and accessed via attributes:
        a = DeepChainMap(b={})
        a.b  # is the b from above
    """

    def __init__(self, *maps, **kwmaps):
        named_maps = []
        for name in kwmaps:
            setattr(self, name, kwmaps[name])
            named_maps.append(getattr(self, name))
        # keyword maps should come first
        all_maps = []
        all_maps.extend(named_maps)
        all_maps.extend(list(maps))

        self.fallback = {}

        super().__init__(*all_maps)

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        # Don't modify any of self.maps by default
        self.fallback[key] = value

    def __delitem__(self, key):
        # If the key exists in both fallback and another dict, this deletes both.
        if self.fallback and key in self.fallback:
            del self.fallback[key]

        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)

    def __missing__(self, key):
        # used to get from the fallback
        if self.fallback and key in self.fallback:
            return self.fallback[key]
        raise KeyError(key)

    def popitem(self):
        """
        Remove and return an item pair from the first map that has an item.
        Raise KeyError if all maps in self.maps are empty.
        Ignores the fallback.
        """
        for m in self.maps:
            try:
                return m.popitem()
            except KeyError:
                continue
        raise KeyError('No keys found in any of the mappings (without checking fallback).')

    def pop(self, key, *args):
        """
        Remove *key* from the first map that has it and return its value.
        Raise KeyError if *key* not in any of self.maps.
        Ignores the fallback.
        """
        for m in self.maps:
            try:
                return m.pop(key, *args)
            except KeyError:
                continue
        raise KeyError('Key not found in the any of the mappings (without checking fallback): {!r}'.format(key))

    def clear(self):
        # Does not clear fallback.
        for m in self.maps:
            m.clear()

    def clear_all(self):
        self.fallback.clear()
        self.clear()
