# -*- coding: utf-8 -*-
"""
    visuals.rst.nodes
    ~~~~~~~~~~~~~~~~~

    ReStructuredText document tree nodes for Docutils

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import absolute_import

from docutils import nodes

from visuals.asset.visual_asset_bridge import VisualAsset


# noinspection PyPep8Naming
class visual(nodes.General, nodes.Element):
    """ A Visual Node """

    def is_ref(self):
        """
        A reference to a visual is a visual without any content.
        Such a visual must be pre-generated and available somewhere else.

        If the visual has content, then it is a visual definition.
        The visual should be generated, somehow, from whatever is in the content.
        :return bool:
        """
        return not self['content_block']


def visit_visual(self, node):
    """
    self is a sphinx/writer/*Translator which implements docutils.nodes.NodeVisitor
    node is a visual node

    I can't just assume that visual=figure,
    because it might be a screencast (or some other oembed) instead of an image

    This should only add any wrapper stuff (divs in html or similar)
    The Translator will call the appropriate visit_* on subnodes as well,
    so we can just pass most of the time.

    Related visitors:
     self.visit_figure
      self.visit_image
      self.visit_caption
      self.visit_legend

    If I need to prevent visit_/depart_ on all children:
    raise nodes.SkipNode
    This might be especially helpful in text writers

    :param nodes.NodeVisitor self:
    :param visual node:
    """
    # TODO:2 insert oEmbed or downloaded asset or placeholder
    sm = node.assets_statemachine
    """:type sm: AssetsStateMachine"""

    asset = VisualAsset(node)
    oembed = sm.get_oembed(asset)


def depart_visual(self, node):
    """
    See visit_visual
    :param nodes.NodeVisitor self:
    :param visual node:
    """
    pass
