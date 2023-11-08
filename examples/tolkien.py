#!/usr/bin/python
'''
This script demonstrates using the ULANProvider to get the concept of
J.R.R. Tolkien.
'''

from skosprovider_getty.providers import ULANProvider

ulan = ULANProvider(metadata={'id': 'ULAN'})

tolkien = ulan.get_by_id(500112201)

langs = ['en', 'nl', 'und']

print('Label per language')
print('------------------')
for lang in langs:
    label = tolkien.label(lang)
    print(lang + ' --> ' + label.language + ': ' + label.label + ' [' + label.type + ']')

print('Labels')
print('------')
for lang in tolkien.labels:
    print(lang.language + ': ' + lang.label + ' [' + lang.type + ']')
