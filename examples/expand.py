#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
This script demonstrates using the AATProvider to expand a collection
'''

from skosprovider_getty.providers import AATProvider

results = AATProvider({'id': 'AAT', 'default_language': 'nl'}).expand('300007466')

print('Results')
print('------')
for result in results:
    print(result)