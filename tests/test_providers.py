#!/usr/bin/python
# -*- coding: utf-8 -*-
import pytest
from rdflib.namespace import SKOS, Namespace

from skosprovider_getty.providers import (
    AATProvider,
    TGNProvider,
    ULANProvider,
    GettyProvider
)
import unittest
from skosprovider_getty.utils import SubClasses

global clazzes, ontologies
clazzes = []
ontologies = {}


class GettyProviderTests(unittest.TestCase):

    def test_get_by_id_concept(self):
        concept = AATProvider({'id': 'AAT'}).get_by_id('300007466', change_notes=True)
        concept = concept.__dict__
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['type'], 'concept')
        self.assertIsInstance(concept['labels'], list)

        preflabels = [{'nl': 'kerken'}, {'de': u'kirchen (Gebäude)'}]
        preflabels_conc = [{label.language: label.label} for label in concept['labels']
                           if label.type == 'prefLabel']
        self.assertGreater(len(preflabels_conc), 0)
        for label in preflabels:
            self.assertIn(label, preflabels_conc)
       
        altlabels = [{'nl': 'kerk'}, {'de': u'kirche (Gebäude)'}]
        altlabels_conc = [{label.language: label.label} for label in concept['labels']
                          if label.type == 'altLabel']
        self.assertGreater(len(altlabels_conc), 0)
        for label in altlabels:
            self.assertIn(label, altlabels_conc)

        self.assertGreater(len(concept['notes']), 0)

        self.assertEqual(concept['id'], '300007466')
        #todo gvp:broader is not a subproperty of skos:broader anymore. This is the reason why there are no broader elements anymore belonging to the Concept...to be decided what to do...
        #self.assertEqual(concept['broader'][0], '300007391')
        self.assertIn('300312247', concept['related'])

    def test_get_by_id_collection(self):
        collection = AATProvider({'id': 'AAT'}).get_by_id('300007473')
        collection = collection.__dict__
        self.assertEqual(collection['uri'], 'http://vocab.getty.edu/aat/300007473')
        self.assertEqual(collection['type'], 'collection')
        self.assertIsInstance(collection['labels'], list)
        self.assertIn(u'<kerken naar vorm>', [label.label for label in collection['labels']
                                             if label.language == 'nl' and label.type == 'prefLabel'])
        self.assertEqual(len(collection['notes']), 0)

    def test_get_by_id_invalid(self):
        concept = AATProvider({'id': 'AAT'}).get_by_id('123')
        self.assertFalse(concept)

    def test_get_by_id_superordinates(self):
        # Default GettyProvider is an AAT provider
        collection = GettyProvider({'id': 'AAT'}).get_by_id('300138225-array')
        assert collection.id == '300138225-array'
        assert '300138225' in collection.superordinates

    def test_get_by_id_subOrdinateArrays(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_id('300138225')
        concept = concept.__dict__
        self.assertEqual(concept['id'], '300138225')
        self.assertIn('300138225-array', concept['subordinate_arrays'])
        #300126352

    def test_get_by_uri(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_uri('http://vocab.getty.edu/aat/300007466')
        concept = concept.__dict__
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['id'], '300007466')

    def test_get_by_id_tgn(self):
        concept = TGNProvider({'id': 'TGN'}).get_by_id('1000063')
        concept = concept.__dict__
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/tgn/1000063')
        self.assertIn(u'België', [label.label for label in concept['labels']
                                 if label.language == 'nl' and label.type == 'prefLabel'])

    def test_get_all(self):
        kwargs = {'language': 'nl'}
        self.assertFalse(TGNProvider({'id': 'TGN'}).get_all(**kwargs))

    def test_get_top_display(self):
        kwargs = {'language': 'nl'}
        top_TGN_display = TGNProvider({'id': 'TGN', 'default_language': 'en'}).get_top_display(**kwargs)
        self.assertIsInstance(top_TGN_display, list)
        self.assertGreater(len(top_TGN_display), 0)
        keys_first_display = top_TGN_display[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            self.assertIn(key, keys_first_display)
        self.assertIn(u'World', [label['label'] for label in top_TGN_display])
        top_AAT_display = AATProvider({'id': 'AAT', 'default_language': 'nl'}).get_top_display()
        self.assertIsInstance(top_AAT_display, list)
        self.assertGreater(len(top_AAT_display), 0)
        self.assertIn(u'Facet Stijlen en perioden', [label['label'] for label in top_AAT_display])

    def test_get_top_concepts(self):
        kwargs = {'language': 'nl'}
        top_TGN_concepts = TGNProvider({'id': 'TGN'}).get_top_concepts(**kwargs)
        self.assertIsInstance(top_TGN_concepts, list)
        self.assertEqual(len(top_TGN_concepts), 0)

    def test_get_childeren_display(self):
        kwargs = {'language': 'nl'}
        childeren_tgn_belgie = TGNProvider({'id': 'TGN', 'default_language': 'nl'}).get_children_display('1000063', **kwargs)
        self.assertIsInstance(childeren_tgn_belgie, list)
        self.assertGreater(len(childeren_tgn_belgie), 0)
        keys_first_display = childeren_tgn_belgie[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            self.assertIn(key, keys_first_display)
        self.assertIn(u'Brussels Hoofdstedelijk Gewest', [label['label'] for label in childeren_tgn_belgie])

    def test_expand(self):
        all_childeren_churches = AATProvider({'id': 'AAT'}).expand('300007466')
        self.assertIsInstance(all_childeren_churches, list)
        self.assertGreater(len(all_childeren_churches), 0)
        self.assertIn('300007466', all_childeren_churches)

    def test_expand_invalid(self):
        all_childeren_invalid = AATProvider({'id': 'AAT'}).expand('invalid')
        self.assertFalse(all_childeren_invalid)

    def test_expand_collection(self):
        all_childeren_churches_by_fuction = AATProvider({'id': 'AAT'}).expand('300007494')
        self.assertIsInstance(all_childeren_churches_by_fuction, list)
        self.assertGreater(len(all_childeren_churches_by_fuction), 0)
        self.assertNotIn('300007494', all_childeren_churches_by_fuction)

    def test_find_without_label(self):
        r = AATProvider({'id': 'AAT'}).find({'type': 'concept', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)

    def test_find_wrong_type(self):
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {'type': 'collectie', 'collection': {'id': '300007466', 'depth': 'all'}})

    def test_find_no_collection_id(self):
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {'type': 'collection', 'collection': {'depth': 'all'}})

    def test_find_wrong_collection_depth(self):
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {'type': 'concept', 'collection': {'id': '300007466', 'depth': 'allemaal'}})

    def test_find_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Concept')

    def test_find_multiple_keywords(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church abbey', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Concept')

    def test_find_member_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept', 'collection': {'id': '300007494', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Concept')

    def test_find_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Collection')

    def test_find_concepts(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Concept')

    def test_find_concepts_kerk_zh(self):
        r = AATProvider({'id': 'AAT', 'default_language': 'zh'}).find({'label': 'kerk', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Concept')

    def test_find_concepts_kerk_language(self):
        kwargs = {'language': 'nl'}
        result = AATProvider({'id': 'AAT'}).find({'label': 'kerk', 'type': 'concept'}, **kwargs)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        labels = []
        for res in result:
            self.assertEqual(res['type'], 'Concept')
            labels.append(res['label'])
        self.assertIn("kerken", labels)

    def test_find_concepts_kerk(self):
        r1 = AATProvider({'id': 'AAT'}).find({'label': 'kerk', 'type': 'concept'})
        r2 = AATProvider({'id': 'AAT', 'default_language': 'en'}).find({'label': 'kirche', 'type': 'concept'})
        r3 = AATProvider({'id': 'AAT', 'default_language': 'nl'}).find({'label': 'kerk', 'type': 'concept'})

        self.assertIsInstance(r1, list)
        self.assertIsInstance(r2, list)
        self.assertIsInstance(r3, list)
        self.assertGreater(len(r1), 0)
        self.assertGreater(len(r2), 0)
        self.assertGreater(len(r3), 0)
        for res in r1:
            self.assertIn('church', res['label'].lower())
            self.assertEqual(res['type'], 'Concept')
        for res in r2:
            self.assertIn('church', res['label'].lower())
            self.assertEqual(res['type'], 'Concept')
        for res in r3:
            self.assertIn('kerk', res['label'].lower())
            self.assertEqual(res['type'], 'Concept')

    def test_find_member_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection', 'collection': {'id': '300007466', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            self.assertEqual(res['type'], 'Collection')

    def test_answer_wrong_query(self):
        provider = GettyProvider({'id': 'test'}, vocab_id='aat', url='http://vocab.getty.edu/aat')
        self.assertRaises(ValueError, provider._get_answer, "Wrong SPARQL query")

    def test_ontology_subclasses(self):
        subclasses = SubClasses(Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Concept)
        self.assertEqual(len(list_concept_subclasses), 7)
        list_collection_subclasses = subclasses.collect_subclasses(SKOS.Collection)
        self.assertEqual(len(list_collection_subclasses), 4)

class ULANProviderTests:

    def test_ulan_exists(self):
        ulan = ULANProvider({'id': 'ULAN'})
        assert isinstance(ulan, ULANProvider)

    def test_ulan_get_braem(self):
        ulan = ULANProvider({'id': 'ULAN'})
        braem = ulan.get_by_id(500082691)
        assert braem.id == 500082691
        assert 'Braem' in braem.label

    def test_ulan_search_braem(self):
        ulan = ULANProvider({'id': 'ULAN'})
        res = ulan.find({'label': 'braem'})
        assert any([a for a in res if a.id == 500082691])

