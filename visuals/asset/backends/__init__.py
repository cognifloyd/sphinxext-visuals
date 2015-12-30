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
    config = {}
    """Sane default config for the backend (override if needed)."""
    name = 'not-implemented'
    """Simple string name for the backend (override)."""
    priority = None
    """Numerical priority of this backend, 0 through 999 (override)."""

    def __init__(self, statemachine):
        """
        :param visuals.assets.statemachine.AssetsStateMachine statemachine:
        """
        self.statemachine = statemachine

    def request_generation(self, assets):
        raise NotImplementedError('must be implemented in subclasses')

    def check_availability(self, assets):
        raise NotImplementedError('must be implemented in subclasses')

    @classmethod
    def is_enabled(cls, config):
        """
        This should indicate whether or not the backend can be used.
        This can be used to check config or make sure that the backend is available,
        reachable, or whatever.
        :param dict config: dictionary of config options for this backend.
        :return: bool
        """
        # subclasses should only apply_config if is_enabled will return True
        # cls.apply_config(config)
        return False

    @classmethod
    def apply_config(cls, config):
        if 'priority' in config:
            cls.priority = config.pop('priority')
        cls.config.update(config)
