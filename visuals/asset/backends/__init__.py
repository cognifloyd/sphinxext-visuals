# -*- coding: utf-8 -*-
"""
    visuals.asset.backends
    ~~~~~~~~~~~~~~~~~~~~~~

    This package contains backends that map external services to assets,
    making it possible to store and retrieve assets in something external
    to the rst project.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


class AssetBackend(object):
    """
    An AssetBackend allows the AssetsStateMachine to work with various asset backends.

    For example, there is the one for the visuals web api, and another for placeholders.
    Others could be created for other DAM (Digital Asset Management) systems.

    This provides the interface that each AssetBackend must implement.
    """

    def __init__(self, assets_statemachine):
        """
        :param visuals.assets.statemachine.AssetsStateMachine assets_statemachine:
        """
        self.assets_statemachine = assets_statemachine

    def request_generation(self, assets):
        raise NotImplementedError('must be implemented in subclasses')

    def check_availability(self, assets):
        raise NotImplementedError('must be implemented in subclasses')
