#!/usr/bin/python
'''
This script demonstrates using the TGNProvider to get the concept of
Flanders.
'''

from skosprovider_getty.providers import TGNProvider

aat = TGNProvider(metadata={'id': 'TGN'})

flanders = aat.get_by_id(7018236)

langs = ['en', 'nl', 'es', 'de', 'fr']

print('Label per language')
print('------------------')
for lang in langs:
    label = flanders.label(lang)
    print(lang + ' --> ' + label.language + ': ' + label.label + ' [' + label.type + ']')

print('Labels')
print('------')
for lang in flanders.labels:
    print(lang.language + ': ' + lang.label + ' [' + lang.type + ']')

print('Notes')
print('-----')
for n in flanders.notes:
    print(n.language + ': ' + n.note + ' [' + n.type + ']')
