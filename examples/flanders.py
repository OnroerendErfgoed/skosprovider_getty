#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
This script demonstrates using the TGNProvider to get the concept of
Flanders.
'''

from skosprovider_getty.providers import TGNProvider

aat = TGNProvider(metadata={'id': 'TGN'})

flanders = aat.get_by_id(7018236)

lang = ['en', 'nl', 'es', 'de', 'fr']

print('Label per language')
print('------------------')
for l in lang:
    label = flanders.label(l)
    print(l + ' --> ' + label.language + ': ' + label.label + ' [' + label.type + ']')

print('Labels')
print('------')
for l in flanders.labels:
   print(l.language + ': ' + l.label + ' [' + l.type + ']')

print('Notes')
print('-----')
for n in flanders.notes:
    print(n.language + ': ' + n.note + ' [' + n.type + ']')
