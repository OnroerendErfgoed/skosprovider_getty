# -*- coding: utf-8 -*-
import unittest
import rdflib
from skosprovider.exceptions import ProviderUnavailableException
from skosprovider_getty.utils import uri_to_graph, SubClassCollector


class UtilsTests(unittest.TestCase):

    def test_uri_to_graph(self):
        uri = 'http://vocab.getty.edu/aat/300007466.rdf'
        res = uri_to_graph(uri)
        self.assertIsInstance(res, rdflib.graph.Graph)

    def test_uri_to_graph2(self):
        uri = 'http://vocab.getty.edu/aat/300007466'
        self.assertRaises(TypeError, uri_to_graph, uri)

    def test_uri_to_graph_not_found(self):
        uri = 'http://vocab.getty.edu/aat55/300zzz7466.rdf'
        res = uri_to_graph(uri)
        self.assertFalse(res)

    def test_uri_to_graph_error(self):
        uri = 'http://teeezssst.teeteest.test/aat55/300zzz7466.rdf'
        self.assertRaises(ProviderUnavailableException, uri_to_graph, uri)

    def test_collect_subclasses(self):
        from rdflib.namespace import SKOS
        subclasses = SubClassCollector(rdflib.Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Concept)
        self.assertEqual(len(list_concept_subclasses), 8)
