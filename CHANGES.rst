0.3.0 (2016-??-??)
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
