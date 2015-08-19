# -*- coding: utf-8 -*-
"""
    visuals.sphinx_ext
    ~~~~~~~~~~~~~~~~~~

    This package is a namespace package that contains ``visuals``
    an extension for Sphinx.

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.states import Inliner
from docutils.statemachine import ViewList
import re


def make_caption_for_directive(directive, caption):
    """
    Creates a caption for the given directive

    Based on sphinx.directives.code.container_wrapper()

    :param directive: Directive
    :param caption: str
    :return: nodes.caption
    """
    assert isinstance(directive, Directive)

    parsed = nodes.Element()
    directive.state.nested_parse(ViewList([caption], source=''),
                                 directive.content_offset, parsed)
    caption_node = nodes.caption(parsed[0].rawsource, '',
                                 *parsed[0].children)
    caption_node.source = parsed[0].source
    caption_node.line = parsed[0].line
    return caption_node

def make_directive_pattern():
    """ Copied from docutils.parsers.rst.states.Body.explicit.constructs[(directive,<here>)] """
    return re.compile(r"""
                      \.\.[ ]+          # explicit markup start
                      (%s)              # directive name
                      [ ]?              # optional space
                      ::                # directive delimiter
                      ([ ]+|$)          # whitespace or end of line
                      """ % Inliner.simplename, re.VERBOSE | re.UNICODE)
