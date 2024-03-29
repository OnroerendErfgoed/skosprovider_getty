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
installed.

This easiest way to install this library is through pip.

.. code-block:: bash    
    
    $ pip install skosprovider_getty

This will download and install :mod:`skosprovider_getty` and a few libraries it 
depends on. 

Using the providers
===================

A provider provides access to a single thesaurus or conceptscheme. You can 
use the :class:`skosprovider_getty.providers.GettyProvider` directly
by passing it a set of configuration options. Or you can use the more specific
subclasses that come pre-configured with some of the configuration. For most
users, this is the preferred method.

Using AATProvider
-----------------

The :class:`~skosprovider_getty.providers.AATProvider` is a provider for 
the :term:`AAT`. Its use is identical to all other SKOSProviders.

.. literalinclude:: ../../examples/churches.py
   :language: python

Using TGNProvider
-----------------

The :class:`~skosprovider_getty.providers.TGNProvider` is a provider for 
the :term:`TGN`. Its use is identical to all other SKOSProviders.

.. literalinclude:: ../../examples/flanders.py
   :language: python

Using ULANProvider
------------------

The :class:`~skosprovider_getty.providers.ULANProvider` is a provider for 
the :term:`ULAN`. Its use is identical to all other SKOSProviders.

.. literalinclude:: ../../examples/tolkien.py
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
