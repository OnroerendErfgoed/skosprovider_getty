#!/usr/bin/python
import unittest

import pytest
import requests
from skosprovider.exceptions import ProviderUnavailableException

from skosprovider_getty.providers import AATProvider
from skosprovider_getty.providers import GettyProvider
from skosprovider_getty.providers import TGNProvider
from skosprovider_getty.providers import ULANProvider

global clazzes, ontologies
clazzes = []
ontologies = {}


class GettyProviderConfigTests():

    def _get_provider(self):
        # Default GettyProvider is an AAT provider
        return GettyProvider(
            {'id': 'AAT'}
        )

    def test_set_custom_session(self):
        sess = requests.Session()
        # Default GettyProvider is an AAT provider
        provider = AATProvider({'id': 'AAT'}, session=sess)
        assert sess == provider.session

    def test_allowed_instance_scopes(self):
        # Default GettyProvider is an AAT provider
        provider = AATProvider({'id': 'AAT'})
        assert provider.allowed_instance_scopes == [
            'single', 'threaded_thread'
        ]

    def test_override_instance_scopes(self):
        # Default GettyProvider is an AAT provider
        provider = GettyProvider(
            {'id': 'AAT'},
            allowed_instance_scopes=['single']
        )
        assert provider.allowed_instance_scopes == ['single']

    def test_concept_scheme_is_cached(self):
        provider = self._get_provider()
        assert provider._conceptscheme is None
        cs = provider.concept_scheme
        assert provider._conceptscheme == cs

    def test_get_vocabulary_uri(self):
        provider = self._get_provider()
        assert 'http://vocab.getty.edu/aat/' == provider.get_vocabulary_uri()

    def test_get_vocabulary_uri_does_not_load_cs(self):
        provider = self._get_provider()
        assert provider._conceptscheme is None
        assert 'http://vocab.getty.edu/ulan/' == provider.get_vocabulary_uri()
        assert provider._conceptscheme is None


class GettyProviderBasicTests():

    def _get_provider(self):
        return GettyProvider(
            {'id': 'AAT'},
            base_url = 'http://vocab.getty.edu',
            vocab_id = 'aat'
        )

    def test_get_by_id_concept(self):
        provider = self._get_provider()
        concept = provider.get_by_id('300007466', change_notes=True)
        assert concept.uri == 'http://vocab.getty.edu/aat/300007466'
        assert concept.type == 'concept'
        assert isinstance(concept.labels, list)

        preflabels = [{'nl': 'kerken'}, {'de': 'Kirche (Gebäude)'}]
        preflabels_conc = [{label.language: label.label} for label in concept.labels
                           if label.type == 'prefLabel']
        assert len(preflabels_conc) > 0
        for label in preflabels:
            assert label in preflabels_conc

        altlabels = [{'nl': 'kerk'}, {'de': 'kirchen (Gebäude)'}]
        altlabels_conc = [{label.language: label.label} for label in concept.labels
                          if label.type == 'altLabel']
        assert len(altlabels_conc) > 0
        for label in altlabels:
            assert label in altlabels_conc

        assert len(concept.notes)

        assert concept.id == '300007466'
        # todo gvp:broader is not a subproperty of skos:broader anymore. This is the
        #  reason why there are no broader elements anymore belonging to the Concept...
        #  to be decided what to do...
        # self.assertEqual(concept['broader'][0], '300007391')
        assert '300312247' in concept['related']

    def test_get_by_id_collection(self):
        # Default GettyProvider is an AAT provider
        collection = GettyProvider({'id': 'AAT'}).get_by_id('300007473')
        assert collection is not False
        assert collection.uri == 'http://vocab.getty.edu/aat/300007473'
        assert collection.type == 'collection'
        assert '<kerken naar vorm>' in [
            label.label for label in collection.labels if label.language == 'nl' and label.type == 'prefLabel']
        assert len(collection.notes) == 0

    def test_get_by_id_invalid(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_id('123')
        assert not concept

    def test_get_by_id_superordinates(self):
        # Default GettyProvider is an AAT provider
        collection = GettyProvider({'id': 'AAT'}).get_by_id('300138225-array')
        assert collection.id == '300138225-array'
        assert '300138225' in collection.superordinates

    def test_get_by_id_subOrdinateArrays(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_id('300138225')
        assert concept.id == '300138225'
        assert '300138225-array' in concept['subordinate_arrays']
        # 300126352

    def test_get_by_uri(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_uri('http://vocab.getty.edu/aat/300007466')
        concept = concept.__dict__
        self.assertEqual(concept['uri'], 'http://vocab.getty.edu/aat/300007466')
        self.assertEqual(concept['id'], '300007466')

    def test_get_by_uri_invalid(self):
        # Default GettyProvider is an AAT provider
        concept = GettyProvider({'id': 'AAT'}).get_by_uri('urn:skosprovider:5')
        self.assertFalse(concept)
        concept = GettyProvider({'id': 'AAT'}).get_by_uri('https://id.erfgoed.net/thesauri/materialen/7')
        self.assertFalse(concept)


class AATProviderTests(unittest.TestCase):

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
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {
            'type': 'collectie', 'collection': {'id': '300007466', 'depth': 'all'}})

    def test_find_no_collection_id(self):
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {
            'type': 'collection', 'collection': {'depth': 'all'}})

    def test_find_wrong_collection_depth(self):
        self.assertRaises(ValueError, AATProvider({'id': 'AAT'}).find, {
            'type': 'concept', 'collection': {'id': '300007466', 'depth': 'allemaal'}})

    def test_find_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept',
                                             'collection': {'id': '300007466', 'depth': 'all'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            assert res['type'] == 'concept'

    def test_find_multiple_keywords(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church abbey', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            assert res['type'] == 'concept'

    def test_find_member_concepts_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept',
                                             'collection': {'id': '300007494', 'depth': 'members'}})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            assert res['type'] == 'concept'

    def test_find_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection',
                                             'collection': {'id': '300007466', 'depth': 'all'}})
        assert len(r) > 0
        for res in r:
            assert res['type'] == 'collection'

    def test_find_concepts(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            assert res['type'] == 'concept'

    def test_find_concepts_kerk_zh(self):
        r = AATProvider({'id': 'AAT', 'default_language': 'zh'}).find({'label': 'kerk', 'type': 'concept'})
        self.assertIsInstance(r, list)
        self.assertGreater(len(r), 0)
        for res in r:
            assert res['type'] == 'concept'

    def test_find_concepts_kerk_language(self):
        kwargs = {'language': 'nl'}
        result = AATProvider({'id': 'AAT'}).find({'label': 'kerk', 'type': 'concept'}, **kwargs)
        assert len(result) > 0
        labels = []
        for res in result:
            assert res['type'] == 'concept'
            labels.append(res['label'])
        assert "kerken" in labels

    def test_find_concepts_kerk(self):
        r1 = AATProvider({'id': 'AAT'}).find({'label': 'kerk', 'type': 'concept'})
        r2 = AATProvider({'id': 'AAT', 'default_language': 'en'}).find({'label': 'kirche', 'type': 'concept'})
        r3 = AATProvider({'id': 'AAT', 'default_language': 'nl'}).find({'label': 'kerk', 'type': 'concept'})

        assert len(r1) > 0
        assert len(r2) > 0
        assert len(r3) > 0
        for res in r1:
            assert 'church' in res['label'].lower()
            assert res['type'] == 'concept'
        for res in r2:
            assert 'church' in res['label'].lower()
            assert res['type'] == 'concept'
        for res in r3:
            assert 'kerk' in res['label'].lower()
            assert res['type'] == 'concept'

    def test_find_member_collections_in_collection(self):
        r = AATProvider({'id': 'AAT'}).find({'label': 'church', 'type': 'collection',
                                             'collection': {'id': '300007466', 'depth': 'members'}})
        assert len(r) > 0
        for res in r:
            assert res['type'] == 'collection'

    def test_find_matches(self):
        r = AATProvider({'id': 'AAT'}).find({'matches': {'uri': 'http://id.loc.gov/authorities/subjects/sh85123119'}})
        assert len(r) == 1
        assert r[0]['type'] == 'concept'
        assert r[0]['uri'] == 'http://vocab.getty.edu/aat/300191778'

    def test_find_closematches(self):
        r = AATProvider({'id': 'AAT'}).find(
            {'matches': {'uri': 'http://id.loc.gov/authorities/subjects/sh85123119', 'type': 'close'}})
        assert len(r) == 1
        assert r[0]['type'] == 'concept'
        assert r[0]['uri'] == 'http://vocab.getty.edu/aat/300191778'

    def test_find_matches_no_uri(self):
        with pytest.raises(ValueError):
            AATProvider({'id': 'AAT'}).find({'matches': {'type': 'close'}})

    def test_answer_wrong_query(self):
        with pytest.raises(ProviderUnavailableException):
            provider = GettyProvider({'id': 'test'}, vocab_id='aat', url='http://vocab.getty.edu/aat')
            provider._get_answer("Wrong SPARQL query")


class ULANProviderTests():

    def test_ulan_exists(self):
        ulan = ULANProvider({'id': 'ULAN'})
        assert isinstance(ulan, ULANProvider)

    def test_ulan_get_braem(self):
        ulan = ULANProvider({'id': 'ULAN'})
        braem = ulan.get_by_id(500082691)
        assert braem.id == '500082691'
        assert braem.label is not None
        assert 'Braem' in braem.label('nl').label

    def test_ulan_search_braem(self):
        ulan = ULANProvider({'id': 'ULAN'})
        res = ulan.find({'label': 'braem'})
        assert any([a for a in res if a['id'] == '500082691'])

    def test_ulan_search_braem_custom_sort(self):
        ulan = ULANProvider({'id': 'ULAN'})
        res = ulan.find({'label': 'braem'}, sort='id')
        assert ['500082691', '500331524'] == [a['id'] for a in res]
        res = ulan.find({'label': 'braem'}, sort='label', sort_order='desc')
        assert ['500331524', '500082691'] == [a['id'] for a in res]
        res = ulan.find({'label': 'braem'}, sort='sortlabel', sort_order='desc')
        assert ['500331524', '500082691'] == [a['id'] for a in res]


class TGNProviderTests():

    def test_tgn_exists(self):
        tgn = TGNProvider({'id': 'TGN'})
        assert isinstance(tgn, TGNProvider)

    def test_get_by_id_tgn(self):
        concept = TGNProvider({'id': 'TGN'}).get_by_id('1000063')
        concept = concept.__dict__
        assert concept.uri  == 'http://vocab.getty.edu/tgn/1000063'
        assert 'België' in [label.label for label in concept['labels']
                                 if label.language == 'nl' and label.type == 'prefLabel']

    def test_get_all(self):
        kwargs = {'language': 'nl'}
        assert not TGNProvider({'id': 'TGN'}).get_all(**kwargs)

    def test_get_top_display(self):
        kwargs = {'language': 'nl'}
        top_TGN_display = TGNProvider({'id': 'TGN', 'default_language': 'en'}).get_top_display(**kwargs)
        assert isinstance(top_TGN_display, list)
        assert len(top_TGN_display) > 0
        keys_first_display = top_TGN_display[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            assert key in keys_first_display
        assert 'World' in [label['label'] for label in top_TGN_display]
        top_AAT_display = AATProvider({'id': 'AAT', 'default_language': 'nl'}).get_top_display()
        assert isinstance(top_AAT_display, list)
        assert len(top_AAT_display) > 0
        assert 'Facet Stijlen en perioden' in [label['label'] for label in top_AAT_display]

    def test_get_top_concepts(self):
        kwargs = {'language': 'nl'}
        top_TGN_concepts = TGNProvider({'id': 'TGN'}).get_top_concepts(**kwargs)
        assert isinstance(top_TGN_concepts, list)
        assert len(top_TGN_concepts) > 0

    def test_get_childeren_display(self):
        kwargs = {'language': 'nl'}
        childeren_tgn_belgie = TGNProvider({'id': 'TGN', 'default_language': 'nl'}
                                           ).get_children_display('1000063', **kwargs)
        assert isinstance(childeren_tgn_belgie, list)
        assert len(childeren_tgn_belgie) > 0
        keys_first_display = childeren_tgn_belgie[0].keys()
        for key in ['id', 'type', 'label', 'uri']:
            assert key in keys_first_display
        assert 'Brussels Hoofdstedelijk Gewest' in [label['label'] for label in childeren_tgn_belgie]
