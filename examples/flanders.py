#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
This script demonstrates using the TGNProvider to get the concept of
Flanders.
'''

from skosprovider_getty.providers import TGNProvider

aat = TGNProvider(metadata={'id': 'TGN'})

churches = aat.get_by_id(7018236)

lang = ['en', 'nl', 'es', 'de']

print('Labels')
print('------')
for l in churches.labels:
   print(l.language + ': ' + l.label + ' [' + l.type + ']')

print('Notes')
print('-----')
for n in churches.notes:
    print(n.language + ': ' + n.note + ' [' + n.type + ']')
