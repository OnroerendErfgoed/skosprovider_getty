.. _general:

Introduction
============

This library offers an implementation of the :class:`skosprovider.providers.VocabularyProvider` interface based on the Getty Vocabularies
This provider can be used to get a :term:`SKOS`
vocabulary out of the Getty vocabularies.

Supported Getty thesauri:

*The Art & Architecture Thesaurus (AAT) by use of :class:`skosprovider_getty.providers.AATProvider`

*The Getty Thesaurus of Geographic Names (TGN) by use of :class:`skosprovider_getty.providers.TGNProvider`

Using GettyProviders
====================

Using AATProvider
-----------------

The :class:`AATProvider` is a skosprovider for the AAT Getty vocabulary (The Art & Architecture Thesaurus)
Here you can find an example how to use the :class:`AATProvider`:

.. literalinclude:: /../../examples/churches.py
   :language: python

Using TGNProvider
-----------------

The :class:`TGNProvider` is a skosprovider for the TGN Getty vocabulary (The Getty Thesaurus of Geographic Names)
Here you can find an example how to use the :class:`AATProvider`:

.. literalinclude:: /../../examples/flanders.py
   :language: python

More exaples of usages
======================

Using find()
------------
see method description in :ref:`api`

.. literalinclude:: /../../examples/find.py
   :language: python

Using expand()
--------------
see method description in :ref:`api`

.. literalinclude:: /../../examples/expand.py
   :language: python