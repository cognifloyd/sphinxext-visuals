# -*- coding: utf-8 -*-
"""
    visuals.sphinx_ext
    ~~~~~~~~~~~~~~~~~~

    This package is a namespace package that contains ``visuals``
    an extension for Sphinx.

    Naming convention (event_*) for the functions in this file borrowed from:
    github.com/Robpol86/sphinxcontrib-imgur (MIT License)

    :copyright: Copyright 2015 by the contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import absolute_import
from os import path

from docutils import nodes
# from docutils.transforms import Transform
from sphinx.util import copy_static_entry
from sphinx.util.osutil import ensuredir

from visuals import package_dir
from visuals.rst.directives import Visual
from visuals.rst.nodes import visual, visit_visual, depart_visual
from visuals.rst.processing import add_visual_to_assets, fix_types_on_visual_references, process_visuals, \
    request_asset_metadata, VisualNodeDataHandler
from visuals.utils.assets import AssetsDict, AssetsMetadataDict, AssetStatus
from visuals.utils.sphinx import sphinx_emit, pickle_doctree

__version__ = '0.1'


def event_builder_inited(app):
    """
    visual assets are externally sourced from some DAM (digital asset manager)
    or are externally generated as would be done through the visuals API.
    That leads to the following design decisions:

    This uses app.env.assets* because both app.builder.images and app.env.images:
    - are too widely used throughout sphinx to modify safely
    - deal with local image files (copy from source files to output)
    - require that the image files exist in the project's source files
    - assume that the image files are relative to the docname that includes them

    Sphinx's image infrastructure also took care of:
    - select alternative image types
    - image translation
    - additional image-related post processing and transforms
    These might need to be replaced in visuals.

    NOTE: If anything needs to be pickled (reused between runs), put it in doctrees or env:
          doctrees and env get pickled, but builder does not.

    :param sphinx.application.Sphinx app: Sphinx Application
    """

    # the primary list of all visual assets, extracted from the doctree.
    assets = app.env.assets = AssetsDict()
    assets_status = app.env.assets_status = AssetsMetadataDict()
    # NOTE: before using assets_status, run:
    #       app.env.assets_status.update_or_init_from_assets(app.env.assets, AssetStatus)

    VisualNodeDataHandler.class_init(assets, assets_status)

    # the final uri or oembed block with info for builder
    app.builder.assets = {}

    # TODO: It might be good to have a Dict that is not per instance, but per asset.
    app.builder.assets_instances = {}


def event_env_purge_doc(app, docname):
    """
    This triggers the assets merge in the environment
    :param docname: see AssetsDict.purge_doc
    :param sphinx.application.Sphinx app: Sphinx Application
    """
    env = app.env
    """:type env: sphinx.environment.BuildEnvironment"""

    env.assets.purge_doc(docname)
    if docname in env.found_docs:
        # assets_status will cache the doc in assets_status.fallback
        env.assets_status.purge_doc(docname)
    else:
        # the docname was probably deleted, so really ignore it.
        env.assets_status.purge_doc(docname, purge_in_fallback=True)


def event_visual_node_generated(app, visual_node):
    """
    Modify the visual_node, as required without shoving everything into visual itself.

    :param sphinx.application.Sphinx app: Sphinx Application
    :param visual visual_node: The just generated visual node
    """
    # TODO: Maybe move the type-specific visual processing here? (eg image runs Figure/Image)
    pass


def event_doctree_read(app, doctree):
    """
    Visuals processing at the "doctree-read" event

    Runs once per doc (one doctree per docname)

    :param sphinx.application.Sphinx app: Sphinx Application
    :param nodes.document doctree: The doctree of a particular docname in the project
    """
    assets = app.env.assets
    """:type assets: AssetsDict"""
    assets_status = app.env.assets_status
    """:type assets_status: AssetsMetadataDict"""

    def_nodes = []
    for visual_node in doctree.traverse(visual):
        """:type visual_node: visual"""
        add_visual_to_assets(assets, visual_node)

        if not visual_node.is_ref():
            def_nodes.append(visual_node)

        node_data = VisualNodeDataHandler(visual_node)
        node_metadata = node_data.get_metadata()

    metadata = []
    metadata.extend(request_asset_metadata(def_nodes))
    # TODO:1 Request asset def metadata (GET w/ content hash & PUT content)


def event_env_merge_info(app, docnames, other):
    """
    This triggers the assets merge in the environment
    :param sphinx.application.Sphinx app: Sphinx Application
    :param list docnames: Only include asset instances in these docnames
    :param sphinx.environment.BuildEnvironment other: The other Sphinx Environment to be merged
    """
    app.env.assets.merge_other(docnames, other.assets)
    app.env.assets_status.merge_other(docnames, other.assets_status)


def event_env_updated(app, env):
    """
    This emits some additional sphinx events to allow additional processing
    after "Phase 1: Read", but before the env is pickled (which happens during
    "Phase 2: Consistency Checks").

    :param sphinx.application.Sphinx app: Sphinx Application
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    """
    sphinx_emit(app, 'before-doctree-extra-processing', app, env)

    # TODO:PARALLEL add parallel processing with ParallelTasks or see sphinx.builders.linkcheck
    # from sphinx.util.parallel import ParallelTasks, parallel_available
    # if parallel_available and app.parallel > 1:  # based on sphinx.environment #598
    #   nproc = app.parallel
    #
    # env.asset_tasks = ParallelTasks(nproc)

    for docname in env.all_docs:
        doctree = env.get_doctree(docname)
        # Return True if the doctree needs to be re-pickled.
        re_pickle = sphinx_emit(app, 'doctree-extra-processing', app, env, docname, doctree)
        if True in re_pickle:
            pickle_doctree(env, docname, doctree)

    # merge parallel:
    # env.asset_tasks.join()

    sphinx_emit(app, 'before-pickle-env', app, env)


def event_before_doctree_extra_processing(app, env):
    """
    Adds the asset status tracking dicts
    :param sphinx.application.Sphinx app: Sphinx Application
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    """
    assets = env.assets
    """:type assets: AssetsDict"""
    assets_status = env.assets_status
    """:type assets_status: AssetsMetadataDict"""

    assets_status.update_or_init_from_assets(assets, AssetStatus)


def event_doctree_extra_processing(app, env, docname, doctree):
    """
    Secondary pass through all doctrees, after Read phase, before env pickling.

    Runs once per doc (one doctree per docname)

    env.assets should be complete by this point.

    :param sphinx.application.Sphinx app: Sphinx Application
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    :param string docname: The name of the doc that the doctree represents
    :param nodes.document doctree: The doctree of a particular docname in the project
    :return boolean: True if doctree needs to be re-pickled.
    """
    assets = env.assets
    """:type assets: AssetsDict"""

    fix_types_on_visual_references(doctree, assets)

    # TODO:1 Request visual metadata for ref & def
    process_visuals(app, doctree)
    return False


def event_before_pickle_env(app, env):
    """

    :param sphinx.application.Sphinx app: Sphinx Application
    :param sphinx.environment.BuildEnvironment env: Sphinx Environment
    """
    # TODO:2 Transfer metadata env => builder (pickled in env, not in builder)
    pass


def event_doctree_resolved(app, doctree, docname):
    """
    This should recheck for any visuals that need to be rendered
    For those, it sends the full visual content (if needed)
    and marks the visual as a placeholder

    :param sphinx.application.Sphinx app: Sphinx Application
    :param nodes.document doctree: The doctree of all docs in the project
    :param str docname: the path/filename relative to project (without extension)
    """
    # TODO:2 Retrieve oEmbed or Download Asset or Mark for placeholder
    # for node in doctree.traverse(visual):
    #     visual['placeholder'] = True
    pass


def monkey_patch_builder_finish(app):
    """
    Though html-collect-pages is an event at about the right point
    to copy the placeholder image, it is not called for latex or texinfo.

    So, monkey patch it!

    :param sphinx.application.Sphinx app: Sphinx Application
    """
    builder = app.builder
    """:type builder: sphinx.builders.Builder"""

    # Only monkey patch if the builder supports images
    if builder.supported_image_types:

        def copy_visual_placeholder(self):
            """
            based on builders.html.copy_image_files

            :param sphinx.builders.Builder self:
            """

            outdir = path.join(self.outdir, self.imagedir)
            ensuredir(outdir)
            source = path.join(package_dir, 'theme', 'default', 'static', 'FFFFFF-0.png')
            try:
                copy_static_entry(source, outdir, self)
            except Exception as err:
                self.warn('cannot copy image file %r: %s' %
                          (source, err))

        def finish(self):
            """
            :param sphinx.builders.Builder self:
            """
            # TODO:2 Make sure monkey patch worked
            super().finish()
            self.finish_tasks.add_task(copy_visual_placeholder)

        builder.finish = finish


def event_build_finished(app, exception):
    """
    Do any necessary cleanup, such as cleaning up downloads

    Or handle any raised exceptions (including cleanup due to exception)

    :param sphinx.application.Sphinx app: Sphinx Application
    :param None|Exception exception:
    :return:
    """
    # TODO: Cleanup and/or handle exceptions
    pass


def setup(app):
    """ sphinx setup that runs before builder is loaded
    :param sphinx.application.Sphinx app: Sphinx Application
    """
    # Phase 0: Initialization
    #   sphinx init
    app.connect('builder-inited', event_builder_inited)
    app.add_config_value('visuals_local_temp_image', 'http://example.com/placeholder-uri', 'env')

    # Phase 1: Reading
    #   docutils parsing (and writer visitors for Phase 4)
    app.add_node(visual,
                 html=(visit_visual, depart_visual),
                 latex=(visit_visual, depart_visual),
                 text=(visit_visual, depart_visual))

    app.add_directive('visual', Visual)
    app.add_event('visual-node-inited')
    app.add_event('visual-caption-and-legend-extracted')
    app.add_event('visual-node-generated')

    app.connect('visual-node-generated', event_visual_node_generated)

    # NOTE: use transforms to manipulate image nodes:
    # - after source-read event
    # - before process_images (which runs before doctree-read event)

    # Phase 1: Reading
    #   Sphinx start reading
    # app.connect('env-get-outdated', event_env_get_outdated)
    app.connect('env-purge-doc', event_env_purge_doc)
    #   docutils transforms (per docname)
    # app.add_transform(Transform)
    #   sphinx post-processing (per docname)
    app.connect('doctree-read', event_doctree_read)
    #   sphinx post-processing (per parallel read: multiple docnames)
    app.connect('env-merge-info', event_env_merge_info)
    #   after docutils parsing (env-updated is where the entire project has been parsed)
    app.connect('env-updated', event_env_updated)
    app.add_event('before-doctree-extra-processing')
    app.add_event('doctree-extra-processing')
    app.add_event('before-pickle-env')

    app.connect('before-doctree-extra-processing', event_before_doctree_extra_processing)
    app.connect('doctree-extra-processing', event_doctree_extra_processing)
    app.connect('before-pickle-env', event_before_pickle_env)

    # Phase 2: Consistency Checks
    #   No sphinx events.

    # Phase 3: Resolving
    #   sphinx final stage before writing
    app.connect('doctree-resolved', event_doctree_resolved)

    # Phase 4: Writing
    #   docutils writer visitors: see docutils parsing in Phase 1

    #   builder-inited event used here to influence Phase 4's finish tasks.
    #   which, as a hack, is logically separate from event_builder_inited
    app.connect('builder-inited', monkey_patch_builder_finish)

    #   cleanup / handle exceptions
    app.connect('build-finished', event_build_finished)

    # TODO:PARALLEL Make sure that everything really is parallel safe (parallel is important!)
    return {'version': __version__, 'parallel_read_safe': True}
