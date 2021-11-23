#!/usr/bin/python
'''
This script demonstrates retrieving subclasses for a certain class.
'''


from skosprovider_getty.utils import SubClassCollector

from skosprovider_getty.utils import GVP, ISO, SKOS

sc = SubClassCollector(GVP)

sc.collect_subclasses(SKOS.Concept)
print(sc.get_subclasses(SKOS.Concept))

sc.collect_subclasses(SKOS.Collection)
print(sc.get_subclasses(SKOS.Collection))

sc.collect_subclasses(SKOS.OrderedCollection)
print(sc.get_subclasses(SKOS.OrderedCollection))

sc.collect_subclasses(SKOS.OrderedCollection)
print(sc.get_subclasses(SKOS.OrderedCollection))

sc.collect_subclasses(ISO.ThesaurusArray)
print(sc.get_subclasses(ISO.ThesaurusArray))

skosc = SubClassCollector(SKOS)
skosc.collect_subclasses(SKOS.Collection)
print(skosc.get_subclasses(SKOS.Collection))
