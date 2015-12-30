# -*- coding: utf-8 -*-
"""
    visuals.rst
    ~~~~~~~~~~~

    This package is a namespace package that contains ``visuals.rst``

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from visuals.rst.nodes import visual


def fix_types_on_visual_references(doctree, assets):
    """
    If a visual node is a reference, then node['type'] might be incorrect.
    This makes the definition's type take precedence (if defined)
    :param docutils.nodes.document doctree: The doctree of a particular docname in the project
    :param assets.AssetsDict assets: The list of all assets in the project
    """
    for node in doctree.traverse(visual):
        node_type = assets.get_type(node['visualid'])
        if node_type is None:
            # Then this asset_id doesn't have any definitions.
            # So, leave the defined type as is.
            continue
        elif node.is_ref():
            # All references should match the type on the definition.
            node['type'] = node_type
