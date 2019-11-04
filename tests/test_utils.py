# -*- coding: utf-8 -*-
import pytest
import rdflib
from skosprovider.exceptions import ProviderUnavailableException
from skosprovider_getty.utils import uri_to_graph, SubClassCollector


class TestUtils(object):

    def test_uri_to_graph(self):
        uri = 'http://vocab.getty.edu/aat/300007466.rdf'
        res = uri_to_graph(uri)
        assert isinstance(res, rdflib.graph.Graph)

    def test_uri_to_graph2(self):
        uri = 'http://vocab.getty.edu/aat/300007466'
        with pytest.raises(TypeError):
            res = uri_to_graph(uri)

    def test_uri_to_graph_not_found(self):
        uri = 'http://vocab.getty.edu/aat55/300zzz7466.rdf'
        res = uri_to_graph(uri)
        assert not res

    def test_uri_to_graph_error(self):
        uri = 'http://teeezssst.teeteest.test/aat55/300zzz7466.rdf'
        with pytest.raises(ProviderUnavailableException):
            res = uri_to_graph(uri)

    def test_get_subclasses(self):
        from rdflib.namespace import SKOS
        subclasses = SubClassCollector(rdflib.Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.get_subclasses(SKOS.Concept)
        assert len(list_concept_subclasses) == 8
        assert SKOS.Concept in list_concept_subclasses

    def test_collect_subclasses(self):
        from rdflib.namespace import SKOS
        subclasses = SubClassCollector(rdflib.Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Concept)
        assert len(list_concept_subclasses) == 8
        assert SKOS.Concept in list_concept_subclasses
