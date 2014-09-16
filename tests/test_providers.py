#!/usr/bin/python
# -*- coding: utf-8 -*-

from skosprovider_getty.providers import (
    AATProvider,
    TGNProvider,
    GettyProvider
)
import unittest


class GettyProviderTests(unittest.TestCase):

    def test_get_by_id_concept(self):
        concept = AATProvider({'id': 'AAT'}).get_by_id('300007466', change_notes=True)
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['type'], 'concept')
        self.assertIsInstance(concept['labels'], list)

        preflabels = [{'nl': 'kerken'}, {'de': 'kirchen (Gebäude)'}]
        preflabels_conc = [{label['language']: label['label']} for label in concept['labels']
                           if label['type'] == 'prefLabel']
        self.assertGreater(len(preflabels_conc), 0)
        for label in preflabels:
            self.assertIn(label, preflabels_conc)

        altlabels = [{'nl': 'kerk'}, {'de': 'kirche (Gebäude)'}]
        altlabels_conc = [{label['language']: label['label']} for label in concept['labels']
                          if label['type'] == 'altLabel']
        self.assertGreater(len(altlabels_conc), 0)
        for label in altlabels:
            self.assertIn(label, altlabels_conc)

        self.assertGreater(len(concept['notes']), 0)

        self.assertEqual(concept['id'], '300007466')
        self.assertEqual(concept['broader'][0], '300007391')
        self.assertIn('300312247', concept['related'])

    def test_get_by_id_collection(self):
        collection = AATProvider({'id': 'AAT'}).get_by_id('300007473')
        collection = collection.__dict__
        self.assertEqual(collection['uri'], 'http://vocab.getty.edu/aat/300007473')
        self.assertEqual(collection['type'], 'collection')
        self.assertIsInstance(collection['labels'], list)
        self.assertIn('<kerken naar vorm>', [label['label'] for label in collection['labels']
                                             if label['language'] == 'nl' and label['type'] == 'prefLabel'])
        self.assertEqual(len(collection['notes']), 0)

    def test_get_by_id_invalid(self):
        concept = AATProvider({'id': 'AAT'}).get_by_id('123')
        self.assertFalse(concept)

    def test_get_by_uri(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_uri('http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['id'], '300007466')

    def test_get_by_id_tgn(self):
        concept = TGNProvider({'id': 'TGN'}).get_by_id('1000063')
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/tgn/1000063')
        self.assertIn('België', [label['label'] for label in concept['labels']
                                 if label['language'] == 'nl' and label['type'] == 'prefLabel'])

    def test_get_all(self):
        self.assertFalse(TGNProvider({'id': 'TGN'}).get_all())

    def test_get_top_display(self):
        top_TGN_display = TGNProvider({'id': 'TGN'}).get_top_display()
        self.assertIsInstance(top_TGN_display, list)
        self.assertGreater(len(top_TGN_display), 0)
        keys_first_display = top_TGN_display[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            self.assertIn(key, keys_first_display)
        self.assertIn('World', [label['label'] for label in top_TGN_display])
        top_AAT_display = AATProvider({'id': 'AAT'}).get_top_display()
        self.assertIsInstance(top_AAT_display, list)
        self.assertGreater(len(top_AAT_display), 0)
        self.assertIn('Styles and Periods Facet', [label['label'] for label in top_AAT_display])

    def test_get_top_concepts(self):
        top_TGN_concepts = TGNProvider({'id': 'TGN'}).get_top_concepts()
        self.assertIsInstance(top_TGN_concepts, list)
        self.assertEqual(len(top_TGN_concepts), 0)

    def test_get_childeren_display(self):
        childeren_tgn_belgie = TGNProvider({'id': 'TGN'}).get_children_display('1000063')
        self.assertIsInstance(childeren_tgn_belgie, list)
        self.assertGreater(len(childeren_tgn_belgie), 0)
        keys_first_display = childeren_tgn_belgie[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            self.assertIn(key, keys_first_display)
        self.assertIn('Amblève', [label['label'] for label in childeren_tgn_belgie])

    def test_expand(self):
        all_childeren_churches = AATProvider({'id': 'AAT'}).expand('300007466')
        childeren_churches = AATProvider({'id': 'AAT'}).get_children_display('300007466')
        self.assertIsInstance(all_childeren_churches, list)
        self.assertGreater(len(all_childeren_churches), 0)
        keys_first_display = all_childeren_churches[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            self.assertIn(key, keys_first_display)
        self.assertIn('300007466', [concept['id'] for concept in all_childeren_churches])
        self.assertGreater(len(all_childeren_churches), len(childeren_churches))

    def test_expand_invalid(self):
        all_childeren_invalid = AATProvider({'id': 'AAT'}).expand('invalid')
        self.assertFalse(all_childeren_invalid)

    def test_expand_collection(self):
        all_childeren_churches_by_fuction = AATProvider({'id': 'AAT'}).expand('300007492')
        self.assertNotIn('300007492', [concept['id'] for concept in all_childeren_churches_by_fuction])


    def test_find_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 26)
        print(len(r))
        print(r)

    def test_find_member_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007494', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 14)
        print(len(r))
        print(r)

    def test_find_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 6)
        print(len(r))
        print(r)

    def test_find_member_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        # self.assertEquals(len(r), 6)
        print(len(r))
        print(r)
