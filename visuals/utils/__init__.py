# -*- coding: utf-8 -*-
"""
    visuals.utils
    ~~~~~~~~~~~~~

    Utility functions for Visuals

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


# def make_nondirective_pattern():
#     """"""
#     return re.compile()


def make_dummy_directive(directive_name,
                         has_content=True,
                         option_spec=None,
                         optional_arguments=1,
                         final_argument_whitespace=True,
                         **kwargs):
    """
    Creates a dummy_directive that does not have a usable run()
    This makes it possbile to do some manual processing of directives with
    self.state.parse_directive_* (where self.state = docutils.parsers.rst.states.Body)

    Defaults differ from Directive defaults because we don't know what content will exist
    in the dummy_directive. So, we assume has_content, no options, and one long argument.

    Any additional **kwargs will be applied as dummy_directive.name = value
    """
    dummy_directive = Directive(directive_name, None, None, None, None, None, None, None, None)
    dummy_directive.has_content = has_content
    dummy_directive.option_spec = option_spec
    dummy_directive.optional_arguments = optional_arguments
    dummy_directive.final_argument_whitespace = final_argument_whitespace
    for name, value in kwargs:
        dummy_directive.__setattr__(name, value)

    return dummy_directive


def list_directives_in_block(content_offset, content_block, type_limit=None, limit=None):
    """
    Find all the directives in the given block of content, returning a list of where they start.

    :param int content_offset: Initial offset (0-based lineno) in source (typically self.content_offset)
    :param docutils.statemachine.StringList content_block: A list of lines in the content block
    :param list type_limit: a list of allowed directive types/names
    :param int limit: stop processing directives after this many matches
    :return: list[(int, int, str, re.__Match)]
    """

    if type_limit is not None:
        assert isinstance(type_limit, list)
    if limit is not None and limit < 1:
        limit = None

    directive_pattern = make_directive_pattern()
    directives_in_block = []

    for source, line_offset, line in content_block.xitems():
        offset_in_block = line_offset - content_offset
        directive_first_line_match = directive_pattern.match(line)
        if directive_first_line_match:
            directive_name = directive_first_line_match.group(1)

            if type_limit and directive_name not in type_limit:
                continue

            directives_in_block.append(
                (offset_in_block, line_offset, directive_name, directive_first_line_match)
            )

        if limit is not None and len(directives_in_block) == limit:
            break

    return directives_in_block
