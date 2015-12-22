# -*- coding: utf-8 -*-
"""
    visuals.sphinx_ext
    ~~~~~~~~~~~~~~~~~~

    This contains sphinx-specific utility functions

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from os import path
# noinspection PyUnresolvedReferences,PyPep8Naming
from six.moves import cPickle as pickle


def pickle_doctree(env, docname, doctree):
    """
    save the parsed doctree (copied from the end of env.read_doc()
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    :param string docname: The docname
    :param docutils.nodes.document doctree: The docname's doctree
    """
    doctree_filename = env.doc2path(docname, env.doctreedir, '.doctree')
    dirname = path.dirname(doctree_filename)
    if not path.isdir(dirname):
        os.makedirs(dirname)
    f = open(doctree_filename, 'wb')
    try:
        pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)
    finally:
        f.close()


def sphinx_emit(app, event, *args):
    """
    This emits a signal in Sphinx, if Sphinx is running. app might be none.

    :param sphinx.application.Sphinx app: Sphinx Application
    :param string event: represents an event registered with Sphinx
    :param args:
    :return:
    """
    # app is only available when app.update() is running
    if app is not None:
        app.emit(event, *args)