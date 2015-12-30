# -*- coding: utf-8 -*-
"""
    visuals.assets.statemachine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Asset processing logic

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from visuals.asset.backends import AssetBackend


class AssetState(object):
    """
    This holds stateful information about the process of getting/making an asset.

    Be judicious with what is included here as this is meant to be pickled with env.
    Do not include things that might be large or that get pickled with a node
    such as node['content']
    """

    def __init__(self):
        self.requested = False
        self.available = False
        self.downloaded = False
        self.placeholder = False
        self.error = None


class AssetsStateMachine(object):
    """
    A state machine for multiple assets.
    It manages the states of a list of assets, tracking state in AssetState objects.
    """

    backends_config = {}
    """backends_config should be injected by the consumer of this object, if available."""

    def __init__(self):
        self.backends = []
        """Ordered list of backend instances"""

        # TODO:1 Select Adapter based on voting or something, w/ different backend per type
        possible_backends = AssetBackend.__subclasses__()
        backends = []
        for backend in possible_backends:
            if backend.is_enabled(self.backends_config.get(backend.name, {})):
                backends.append(
                        (backend.priority, backend)
                )

        backends.sort(key=lambda b: b[0])

        for priority, backend in backends:
            self.backends.append(backend(self))

    def request_asset_generation(self, asset_defs):
        not_requested = []
        for asset in asset_defs:
            if asset.state.requested is False:
                not_requested.append(asset)

        # This should make requests (GET w/ content hash & PUT w/ content)
        for backend in self.backends:
            backend.request_generation(not_requested)
            backend.check_availability(asset_defs)

    def ensure_available(self, assets):
        not_available = []
        for asset in assets:
            if not asset.state.available:
                not_available.append(asset)

        for backend in self.backends:
            backend.check_availability(asset)

    def retrieve_oembed_or_download(self, assets):
        for asset in assets:
            asset.node
            # TODO:2 oembed or download
            pass

    def get_oembed(self, asset):
        # TODO:2 oembed
        pass

    def mark_for_placeholder_on_unavailable(self, assets):
        needs_placeholder = []
        for asset in assets:
            if not asset.state.available:
                needs_placeholder.append(asset)

        self.placeholder_needed(needs_placeholder)

    @staticmethod
    def placeholder_needed(assets):
        for asset in list(assets):
            asset.state.placeholder = True

    @staticmethod
    def placeholder_not_needed(assets):
        for asset in list(assets):
            asset.state.placeholder = False

    @staticmethod
    def mark_requested(assets):
        for asset in list(assets):
            asset.state.requested = True

    @staticmethod
    def mark_not_requested(assets):
        for asset in list(assets):
            asset.state.requested = False

    @staticmethod
    def mark_available(assets):
        for asset in list(assets):
            asset.state.available = True

    @staticmethod
    def mark_not_available(assets):
        for asset in list(assets):
            asset.state.available = False

    @staticmethod
    def mark_downloaded(assets):
        for asset in list(assets):
            asset.state.downloaded = True

    @staticmethod
    def mark_not_downloaded(assets):
        for asset in list(assets):
            asset.state.downloaded = False

    @staticmethod
    def clear_errors(assets):
        for asset in list(assets):
            asset.state.error = None
