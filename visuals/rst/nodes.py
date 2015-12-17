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
