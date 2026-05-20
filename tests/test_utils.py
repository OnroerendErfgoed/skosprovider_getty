import pytest
import rdflib
from rdflib.namespace import SKOS
from requests.exceptions import ConnectionError
from skosprovider.exceptions import ProviderUnavailableException
from skosprovider.skos import Label
from skosprovider.skos import Note

from skosprovider_getty.utils import GVP
from skosprovider_getty.utils import ISO
from skosprovider_getty.utils import SubClassCollector
from skosprovider_getty.utils import _create_from_subject_predicate
from skosprovider_getty.utils import _create_from_subject_typelist
from skosprovider_getty.utils import _create_label
from skosprovider_getty.utils import _create_note
from skosprovider_getty.utils import _get_super_ordinates
from skosprovider_getty.utils import conceptscheme_from_uri
from skosprovider_getty.utils import do_get_request
from skosprovider_getty.utils import hierarchy_notetypes
from skosprovider_getty.utils import things_from_graph
from skosprovider_getty.utils import uri_to_id
from skosprovider_getty.utils import uri_to_graph
import skosprovider_getty.utils as utils_mod


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
        subclasses = SubClassCollector(
            rdflib.Namespace('http://vocab.getty.edu/ontology#')
        )
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Concept)
        assert len(list_concept_subclasses)
        assert SKOS.Concept in list_concept_subclasses

    def test_collect_subclasses_collection(self):
        subclasses = SubClassCollector(
            rdflib.Namespace('http://vocab.getty.edu/ontology#')
        )
        list_concept_subclasses = subclasses.collect_subclasses(SKOS.Collection)
        assert len(list_concept_subclasses)
        assert SKOS.Collection in list_concept_subclasses

    def test_collect_subclasses_(self):
        subclasses = SubClassCollector(GVP)
        list_concept_subclasses = subclasses.collect_subclasses(ISO.ThesaurusArray)
        assert len(list_concept_subclasses)
        assert ISO.ThesaurusArray in list_concept_subclasses

    def test_conceptscheme_from_uri(self, monkeypatch):
        graph = rdflib.Graph()
        uri = 'http://example.com/aat/'
        graph.add((rdflib.URIRef(uri), rdflib.namespace.RDFS.label, rdflib.Literal('AAT')))
        monkeypatch.setattr(utils_mod, 'uri_to_graph', lambda *args, **kwargs: graph)
        cs = conceptscheme_from_uri(uri, session=None)
        assert cs.uri == uri
        assert cs.labels[0].label == 'AAT'

    def test_create_helpers(self):
        graph = rdflib.Graph()
        subject = rdflib.URIRef('http://example.com/concept/1')
        note_uri = rdflib.URIRef('http://example.com/note/1')
        graph.add((subject, SKOS.prefLabel, rdflib.Literal('Kerk', lang='nl')))
        graph.add((subject, SKOS.note, note_uri))
        graph.add((note_uri, rdflib.namespace.RDF.value, rdflib.Literal('Some note', lang='en')))
        labels = _create_from_subject_typelist(graph, subject, ['prefLabel'])
        notes = _create_from_subject_typelist(graph, subject, ['note'])
        assert isinstance(labels[0], Label)
        assert isinstance(notes[0], Note)

    def test_create_label_invalid_lang(self):
        class DummyLiteral:
            language = 'in valid'

            @staticmethod
            def toPython():
                return 'abc'

        label = _create_label(DummyLiteral(), 'prefLabel')
        assert label.language == 'und'

    def test_create_note_variants(self):
        graph = rdflib.Graph()
        note_uri = rdflib.URIRef('http://example.com/note/2')
        graph.add((note_uri, rdflib.namespace.RDF.value, rdflib.Literal('scope', lang='en')))
        graph.add((note_uri, rdflib.namespace.DC.type, rdflib.Literal('change')))
        graph.add((note_uri, rdflib.namespace.DC.description, rdflib.Literal('details')))
        graph.add((note_uri, rdflib.URIRef('http://www.w3.org/ns/prov#startedAtTime'), rdflib.Literal('now')))
        note = _create_note(graph, note_uri, 'note', change_notes=True)
        assert isinstance(note, Note)
        assert 'scope' in note.note
        assert _create_note(graph, rdflib.URIRef('http://example.com/rev/1'), 'note') is None

    def test_get_super_ordinates_and_request_helpers(self):
        class DummyResponse:
            status_code = 200
            encoding = None

            def __init__(self, payload):
                self._payload = payload
                self.content = b'{}'

            def json(self):
                return self._payload

        class DummySession:
            def get(self, *args, **kwargs):
                return DummyResponse(
                    {'results': {'bindings': [{'s': {'value': 'http://example.com/aat/123'}}]}}
                )

        cs = type('CS', (), {'uri': 'http://example.com/aat/'})
        ret = _get_super_ordinates(cs, rdflib.URIRef('http://example.com/aat/1'), session=DummySession())
        assert ret == ['123']

        r = do_get_request('http://example.com', session=DummySession())
        assert r.encoding == 'utf-8'

    def test_do_get_request_errors(self):
        class FailingSession:
            def __init__(self, exc):
                self.exc = exc

            def get(self, *args, **kwargs):
                raise self.exc

        with pytest.raises(ProviderUnavailableException):
            do_get_request('http://example.com', session=FailingSession(ConnectionError()))

    def test_do_get_request_500(self):
        class ErrorResponse:
            status_code = 500
            content = b'boom'
            encoding = 'utf-8'

        class ErrorSession:
            def get(self, *args, **kwargs):
                return ErrorResponse()

        with pytest.raises(ProviderUnavailableException):
            do_get_request('http://example.com', session=ErrorSession())

    def test_uri_to_id_and_notetypes(self):
        assert uri_to_id('http://example.com/aat/12') == '12'
        assert uri_to_id('just-an-id') == 'just-an-id'
        assert hierarchy_notetypes(['prefLabel', 'note']) == ['prefLabel', 'note']

    def test_things_from_graph(self, monkeypatch):
        graph = rdflib.Graph()
        concept_uri = rdflib.URIRef('http://example.com/aat/10')
        collection_uri = rdflib.URIRef('http://example.com/aat/20')
        graph.add((concept_uri, rdflib.namespace.RDF.type, SKOS.Concept))
        graph.add((concept_uri, SKOS.prefLabel, rdflib.Literal('Concept label', lang='en')))
        graph.add((collection_uri, rdflib.namespace.RDF.type, SKOS.Collection))
        graph.add((collection_uri, SKOS.prefLabel, rdflib.Literal('Collection label', lang='en')))
        graph.add((collection_uri, SKOS.member, concept_uri))

        class DummySubClasses:
            def get_subclasses(self, clazz):
                return [clazz]

        cs = type('CS', (), {'uri': 'http://example.com/aat/'})
        monkeypatch.setattr(utils_mod, '_get_super_ordinates', lambda *args, **kwargs: [])
        things = things_from_graph(graph, DummySubClasses(), cs, session=None)
        assert len(things) == 2

    def test_create_from_subject_predicate_uri(self):
        graph = rdflib.Graph()
        subject = rdflib.URIRef('http://example.com/aat/1')
        obj = rdflib.URIRef('http://example.com/aat/2')
        graph.add((subject, SKOS.related, obj))
        res = _create_from_subject_predicate(graph, subject, SKOS.related)
        assert res == ['2']
