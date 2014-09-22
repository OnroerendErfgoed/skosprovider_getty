#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
This script demonstrates using the AATProvider to find the concepts that are a member of a collection with 'church' in their label
'''

from skosprovider_getty.providers import AATProvider

results = AATProvider({'id': 'AAT', 'default_language': 'nl'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007466', 'depth': 'all'}})

print('Results')
print('------')
for result in results:
    print(result)

