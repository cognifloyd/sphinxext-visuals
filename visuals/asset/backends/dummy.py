# -*- coding: utf-8 -*-
"""
    visuals.asset.backends.dummy
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This package contains an asset backend that returns dummy data.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from random import choice as random_choice

from visuals.asset.backends import AssetBackend

# For now only photos
dummy_assets = {
    'something new': {          # New image, waiting to be processed
        'status': 'new',
        'uri': None,
        'type': None
    },
    'something processing': {   # processing uploaded data
        'status': 'processing',
        'uri': None,
        'type': None
    },
    'something generating': {   # generating the image
        'status': 'generating',
        'uri': None,
        'type': 'Photo'
    },
    'something uploading': {    # generated, uploading somewhere (cdn, etc)
        'status': 'uploading',
        'uri': None,
        'type': 'Photo'
    },
    'something done': {          # Generated, available at
        'status': 'done',
        'use_oembed': 'True',
        'uri': 'embed.ly/something',
        'type': 'Photo'
    },
    'something failed': {
        'status': 'failed',
        'error': 'some error message',
        'uri': None
    }
}


class DummyBackend(AssetBackend):

    def __init__(self, assets_statemachine):
        super().__init__(assets_statemachine)
        self.assets = dummy_assets

    def _random_asset_key(self):
        return random_choice(list(self.assets.keys()))

    # asset attributes
    #     asset.id        # ignore for dummy
    #     asset.options         #
    #     asset.type            # photo, ...
    #     asset.content_hash    # only definitions
    #     asset.content         # only if hash unrecognized

    def request_generation(self, assets):
        self.assets_statemachine.mark_requested(assets)

    def check_availability(self, assets):
        for asset in list(assets):
            remote_asset = self.assets[self._random_asset_key()]
            if remote_asset['status'] == 'done':
                self.assets_statemachine.mark_available(asset)

