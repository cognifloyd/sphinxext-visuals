# -*- coding: utf-8 -*-
"""
    sphinx.util
    ~~~~~~~~~~~

    Utility functions for Sphinx.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


class VisualsClient(object):
    """
    Client for the visuals API. A dummy for now.
    """
    def __init__(self):
        pass

    def geturi(docname, visualid):
        return 'http://placehold.it/500x100?text=' + docname + '.' + '+'.join(visualid.split())


