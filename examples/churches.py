#!/usr/bin/python
'''
This script demonstrates using the AATProvider to get the concept of
Churches.
'''

from skosprovider_getty.providers import AATProvider

aat = AATProvider(metadata={'id': 'AAT'})

churches = aat.get_by_id('300007466')

langs = ['en', 'nl', 'es', 'de', 'fr']

print('Label per language')
print('------------------')
for lang in langs:
    label = churches.label(lang)
    print(lang + ' --> ' + label.language + ': ' + label.label + ' [' + label.type + ']')

print('All Labels')
print('----------')
for lang in churches.labels:
    print(lang.language + ': ' + lang.label + ' [' + lang.type + ']')

print('All Notes')
print('---------')
for n in churches.notes:
    print(n.language + ': ' + n.note + ' [' + n.type + ']')
