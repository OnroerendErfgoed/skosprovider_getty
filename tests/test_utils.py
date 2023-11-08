import pytest
import rdflib
from rdflib.namespace import SKOS
from skosprovider.exceptions import ProviderUnavailableException

from skosprovider_getty.utils import GVP
from skosprovider_getty.utils import ISO
from skosprovider_getty.utils import SubClassCollector
from skosprovider_getty.utils import uri_to_graph


class TestUtils:

    def test_uri_to_graph(self):
        uri = 'http://vocab.getty.edu/aat/300007466.rdf'
        res = uri_to_graph(uri)
        assert isinstance(res, rdflib.graph.Graph)

    def test_uri_to_graph2(self):
        uri = 'http://vocab.getty.edu/aat/300007466'
        with pytest.raises(TypeError):
            uri_to_graph(uri)

    def test_uri_to_graph_not_found(self):
        uri = 'http://vocab.getty.edu/aat55/300zzz7466.rdf'
        res = uri_to_graph(uri)
        assert not res

    def test_uri_to_graph_error(self):
        uri = 'http://teeezssst.teeteest.test/aat55/300zzz7466.rdf'
        with pytest.raises(ProviderUnavailableException):
            uri_to_graph(uri)

    def test_get_subclasses(self):
        subclasses = SubClassCollector(GVP)
        list_concept_subclasses = subclasses.get_subclasses(SKOS.Concept)
        assert len(list_concept_subclasses) == 8
        assert SKOS.Concept in list_concept_subclasses

    def test_collect_subclasses_concept(self):
        subclasses = SubClassCollector(rdflib.Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Concept)
        assert len(list_concept_subclasses)
        assert SKOS.Concept in list_concept_subclasses

    def test_collect_subclasses_collection(self):
        subclasses = SubClassCollector(rdflib.Namespace("http://vocab.getty.edu/ontology#"))
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Collection)
        assert len(list_concept_subclasses)
        assert SKOS.Collection in list_concept_subclasses

    def test_collect_subclasses_(self):
        subclasses = SubClassCollector(GVP)
        list_concept_subclasses = subclasses.collect_subclasses(ISO.ThesaurusArray)
        assert len(list_concept_subclasses)
        assert ISO.ThesaurusArray in list_concept_subclasses
