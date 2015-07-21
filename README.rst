============================
Visuals Extension for Sphinx
============================

.. |Visuals| replace:: the Visuals API

This extension interacts with |Visuals|.

|Visuals| should make it easier to integrate visuals into your ReStructuredText documents.
The process of creating visuals, like screenshots, clashes with the documentation workflow.
The workflows, processes, and tooling for image creation and writing are very different,
so |Visuals| makes it easier to tackle each process and workflow separately. Eventually,
we'd like to make it possible to automate the creation of visuals, like screenshots,
wherever possible. |Visuals| will be the entry point for such automation.

Requirements
------------

- Sphinx 1.3

Additions to ReStructuredText
-----------------------------

Possibly add a visual domain to add things like:
- ``visual:screenshot:``
- ``visual:toolbar:``
- ``visual:button:``
- ``visual:icon:``

These would document a visual element in directives, and link to the description in roles.

There might also be a simple way to create substitutions for specific elements automatically to
include miniatures of buttons and icons and such... See the visual role for more thinking.

Directives
^^^^^^^^^^

.. rst:directive:: .. visual:: <short description>

		.. visual:: <short description>
		   (options)

		   content

	The ``<short description>`` acts like an id for the image. It should be unique per file.

	The content block should include additional directives.
	It could even include the directives ``.. caption::`` and ``.. legend::`` if they make sense
	for this visual. If a caption and/or legend is included, this acts like a figure directive
	instead of an image directive.

	Everything else will be passed to |Visual| to get a URI that can be embedded, probably via
	oEmbed.

Roles
^^^^^

.. rst:role:: visual

	This is for inline visuals. Generated images will be restricted to images that can be easily
	inlined, like icons or buttons. If there is no directive in the file that describes the
	indicated visual, then the id will be sent to |Visual| and someone will have to manually create it.

	This will need additional thought to figure out how this needs to work.

Thanks
------

The `TYPO3 Association`_ funded the initial development of this.

.. TYPO3 Association: http://typo3.org
