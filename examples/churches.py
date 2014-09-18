# -*- coding: utf-8 -*-
'''
This script demonstrates using the AATProvider to get the concept of
Churches.
'''

from skosprovider_getty.providers import AATProvider

aat = AATProvider(metadata={'id': 'AAT'})

churches = aat.get_by_id(300007466)

lang = ['en', 'nl', 'es', 'de']

print('Labels')
print('------')
for l in churches.labels:
   print(l.language + ': ' + l.label.decode('utf-8') + ' [' + l.type + ']')

print('Notes')
print('-----')
for n in churches.notes:
    print(n.language + ': ' + n.note.decode('utf-8') + ' [' + n.type + ']')
