1.2.0 (2023-11-08)
------------------

- Include the three Getty Conceptschemes in the code to make instantiating 
  the providers less dependent on the Getty services being up and running. (#86)
- Drop support for Python 3.8 and add support for 3.11

1.1.0 (2022-08-17)
------------------

- Drop python 3.6, 3.7 support and add support for 3.8, 3.9 and 3.10
- Upgrade RDFLib to 6.2.0

1.0.0 (2021-12-14)
------------------

- Drop python 2 support
- Upgrade all requirements (#86)

0.5.1 (2020-10-06)
------------------

- Prevent get_by_uri erroring on non-Getty URI's (#77)
- Remove reference to nose.collector
- Remove pyup integration

0.5.0 (2020-08-06)
------------------

- Compatibile with `SkosProvider 0.7.0 <http://skosprovider.readthedocs.io/en/0.7.0/>`_. (#59)
- Prevent unnecessary loading of conceptschemes. (#56)
- Update to RDFlib 5.0.0 (#69)
- Supports Python 2.7, 3.6, 3.7 and 3.8. Last version to support Python 2.

0.4.2 (2017-09-06)
------------------

- Really stop loading the conceptscheme while initialising the provider.

0.4.1 (2017-09-06)
------------------

- Stop loading the conceptscheme while initialising the provider.

0.4.0 (2017-07-15)
------------------

- Stop collecting SKOS Concept and Collection subclasses. They are now included
  in the code base since they seem to have become rather stable and this reduces
  the startup time of the provider significantly. (#28)
- Add support for python 3.6 when testing.

0.3.1 (2016-09-14)
------------------

- Handle a bug with private language tags. Currently not recognised by the
  language_tags library. The Getty services do use them. When encountered, we
  fall back to the undeterminded language. (#26, #27)

0.3.0 (2016-08-11)
------------------

- Upgrade to skosprovider 0.6.0. (#13)
- Add support for the `ULAN <http://vocab.getty.edu/ulan>`_ vocabulary. (#22)
- Add support for sorting. (#24)
- Allow configuring the requests session in use. (#25)

0.2.1 (2015-03-10)
------------------

- Introduce language support. Until now it was impossible to pass in a language
  parameter to certain methods. This was not only a missing feature, but also a
  bug since the VocabularyProvider interface requires that a client can pass in 
  extra keywords. (#16)
- iso-thes:superordinates get fetched from the SPARQL store. (#17)
- All network requests now go through requests. (#13)
- Some documentation improvements. (#15)

0.2.0 (2014-12-22)
------------------

- Compatibile with `SkosProvider 0.5.x <http://skosprovider.readthedocs.org/en/0.5.0>`_.
- Now uses the IANA language code `und` for labels in an unknown language.
- Now throws a ProviderUnavailableException when the Getty vocab services can't
  be reached.
- Handle superordinates and subordinate arrays.
- Error handling and bugfixes.

0.1.0 (2014-09-30)
------------------

- Initial version
- Contains providers for `AAT <http://vocab.getty.edu/aat>`_ and 
  `TGN <http://vocab.getty.edu/tgn>`_ vocabularies.
- Compatible with `SkosProvider 0.3.0 <http://skosprovider.readthedocs.org/en/0.3.0>`_.
