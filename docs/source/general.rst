.. _general:

Introduction
============

This library offers an implementation of the 
:class:`skosprovider.providers.VocabularyProvider` interface based on the 
`Getty Vocabularies <http://vocab.getty.edu>`_. It reduces the complex 
vocabularies like :term:`AAT` and :term:`TGN` to a basic :term:`SKOS` version
of them. 

Supported Getty thesauri:

* The `Art & Architecture Thesaurus (AAT)` by use of the 
  :class:`skosprovider_getty.providers.AATProvider`.
* The `Getty Thesaurus of Geographic Names (TGN)` by use of the 
  :class:`skosprovider_getty.providers.TGNProvider`.
* The `Union List of Artist Names (ULAN)` by use of the
  :class:`skosprovider_getty.providers.ULANProvider`.

Installation
============

To be able to use this library you need to have a modern version of Python 
installed. Currently we're supporting versions 2.7, 3.3 and 3.4 of Python.

This easiest way to install this library is through pip or easy install:

.. code-block:: bash    
    
    $ pip install skosprovider_getty

This will download and install :mod:`skosprovider_getty` and a few libraries it 
depends on. 

Using the providers
===================

Using AATProvider
-----------------

The :class:`~skosprovider_getty.providers.AATProvider` is a provider for 
the :term:`AAT`. It's use is identical to all other SKOSProviders.

.. literalinclude:: ../../examples/churches.py
   :language: python

Using TGNProvider
-----------------

The :class:`~skosprovider_getty.providers.TGNProvider` is a provider for 
the :term:`TGN`. It's use is identical to all other SKOSProviders.

.. literalinclude:: ../../examples/flanders.py
   :language: python

Finding concepts or collections
-------------------------------

See the :meth:`skosprovider_getty.providers.GettyProvider.find` method for
a detailed description of how this works.

.. literalinclude:: ../../examples/find.py
   :language: python

Using expand()
--------------

The expand methods return the id's of all the concepts that are narrower 
concepts of a certain concept or collection.

See the :meth:`skosprovider_getty.providers.GettyProvider.expand` method for
a detailed description of how this works.

.. literalinclude:: ../../examples/expand.py
   :language: python
