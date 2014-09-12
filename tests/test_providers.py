#!/usr/bin/python
# -*- coding: utf-8 -*-

from skosprovider_getty.providers import (
    ATTProvider,
    TGNProvider
)
import unittest

class GettyProviderTests(unittest.TestCase):

    def test_get_by_id_concept(self):
        concept = ATTProvider({'id': 'AAT'}).get_by_id(300007466, change_notes=True)
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['type'], 'concept')
        self.assertIsInstance(concept['labels'], list)

        preflabels = [{'nl':'kerken'}, {'de':'kirchen (Gebäude)'}]
        preflabels_conc = [{label['language']: label['label']} for label in concept['labels']
                           if label['type'] == 'prefLabel']
        self.assertGreater(len(preflabels_conc), 0)
        for label in preflabels:
            self.assertIn(label, preflabels_conc)

        altlabels = [{'nl':'kerk'}, {'de':'kirche (Gebäude)'}]
        altlabels_conc = [{label['language']: label['label']} for label in concept['labels']
                          if label['type'] == 'altLabel']
        self.assertGreater(len(altlabels_conc), 0)
        for label in altlabels:
            self.assertIn(label, altlabels_conc)

        self.assertGreater(len(concept['notes']), 0)

        self.assertEqual(concept['id'], '300007466')
        self.assertEqual(concept['broader'][0], '300007391')
        self.assertIn('300312247', concept['related'])

    def test_get_by_id_invalid(self):
        concept = ATTProvider({'id': 'AAT'}).get_by_id(123)
        self.assertIsNone(concept)

    def test_get_by_uri(self):
        concept = ATTProvider({'id': 'AAT'}).get_by_uri('http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['id'], '300007466')


    def test_get_by_id_tgn(self):
        concept = TGNProvider({'id': 'TGN'}).get_by_id(1000063)
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/tgn/1000063')
        self.assertIn('België', [label['label'] for label in concept['labels'] if label['language'] == 'nl' and label['type'] == 'prefLabel'])

    def test_find_concepts_in_collection(self):
        r = ATTProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 26)
        print(len(r))
        print(r)

    def test_find_member_concepts_in_collection(self):
        r = ATTProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007494', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 14)
        print(len(r))
        print(r)

    def test_find_collections_in_collection(self):
        r = ATTProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 6)
        print(len(r))
        print(r)

    def test_find_member_collections_in_collection(self):
        r = ATTProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 6)
        print(len(r))
        print(r)
