# -*- coding: utf-8 -*-
"""
    visuals.asset.backends.placeholder
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This package contains an asset backend that returns placeholder assets.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from visuals.asset.backends import AssetBackend


class PlaceholderBackend(AssetBackend):
    name = 'placeholder'
    priority = 999  # Try other backends first. This backend is 'available' for all.
    enabled_by_default = True

    def request_generation(self, assets):
        needs_placeholder = [asset for asset in list(assets) if asset.state.placeholder]
        self.statemachine.mark_requested(needs_placeholder)

    def check_availability(self, assets):
        needs_placeholder = [asset for asset in list(assets) if asset.state.placeholder]
        self.statemachine.mark_available(needs_placeholder)
