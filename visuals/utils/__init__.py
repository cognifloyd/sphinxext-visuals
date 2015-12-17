# -*- coding: utf-8 -*-
"""
    visuals.utils
    ~~~~~~~~~~~~~

    Utility functions for Visuals

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import ChainMap


class DeepChainMap(ChainMap):
    """
    Variant of ChainMap that allows direct updates to inner scopes.

    Source:
    https://docs.python.org/3/library/collections.html#chainmap-examples-and-recipes
    """

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)
