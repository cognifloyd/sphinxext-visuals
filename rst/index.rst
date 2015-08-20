===============
 Test Document
===============

This is a visual:

.. visual:: describe it here


.. visual:: With a caption and no legend
   :caption: This is a *fantastic* caption


.. visual:: With no caption and a legend

   .. legend::

        +---+---+
        | 1 | 2 |
        +===+===+
        | a | b |
        +---+---+

.. visual:: With a caption and a legend
   :caption: Here **is** a caption

   .. legend::

       Here is a legend

.. visual:: A legend and a paragraph
   :caption: do dah

   .. asdf:: asdf

   .. legend::

      perfect legend

   asdf paragraph

   .. asdf:: asdf

.. visual:: no legend with a paragraph
   :caption: do bob

   wonderful world

   .. bogus_directive:: stupid stupid stupid
      arguments continued blab blab
      :option: blablablab
      :otheroption: blablab

   .. od::
      :option: bla

      content in directive

   .. legend::

      asdf
