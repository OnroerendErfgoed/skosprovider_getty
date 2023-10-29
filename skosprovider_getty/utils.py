'''
This module contains utility functions for :mod:`skosprovider_getty`.
'''
import logging

import rdflib
import requests
from rdflib.graph import Graph
from rdflib.namespace import DC
from rdflib.namespace import RDF
from rdflib.namespace import RDFS
from rdflib.namespace import SKOS
from rdflib.term import URIRef
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from skosprovider.exceptions import ProviderUnavailableException
from skosprovider.skos import Collection
from skosprovider.skos import Concept
from skosprovider.skos import ConceptScheme
from skosprovider.skos import Label
from skosprovider.skos import Note

log = logging.getLogger(__name__)


PROV = rdflib.Namespace('http://www.w3.org/ns/prov#')
ISO = rdflib.Namespace('http://purl.org/iso25964/skos-thes#')
GVP = rdflib.Namespace('http://vocab.getty.edu/ontology#')


def conceptscheme_from_uri(conceptscheme_uri, **kwargs):
    '''
    Read a SKOS Conceptscheme from a :term:`URI`

    :param string conceptscheme_uri: URI of the conceptscheme.
    :rtype: skosprovider.skos.ConceptScheme
    '''

    # get the conceptscheme
    # ensure it only ends in one slash
    conceptscheme_uri = conceptscheme_uri.strip('/') + '/'
    s = kwargs.get('session', requests.Session())
    graph = uri_to_graph('%s.rdf' % (conceptscheme_uri), session=s)

    notes = []
    labels = []
    if graph is not False:
        for s, p, o in graph.triples((URIRef(conceptscheme_uri), RDFS.label, None)):
            label = Label(o.toPython(), "prefLabel", 'en')
            labels.append(label)

    conceptscheme = ConceptScheme(
        conceptscheme_uri,
        labels=labels,
        notes=notes
    )
    return conceptscheme


def things_from_graph(graph, subclasses, conceptscheme, **kwargs):
    s = kwargs.get('session', requests.Session())
    valid_label_types = Label.valid_types[:]
    valid_label_types.remove('sortLabel')
    graph = graph
    clist = []
    concept_graph = Graph()
    collection_graph = Graph()
    for sc in subclasses.get_subclasses(SKOS.Concept):
        concept_graph += graph.triples((None, RDF.type, sc))
    for sc in subclasses.get_subclasses(SKOS.Collection):
        collection_graph += graph.triples((None, RDF.type, sc))
    for sub, pred, obj in concept_graph.triples((None, RDF.type, None)):
        uri = str(sub)
        matches = {}
        for k in Concept.matchtypes:
            matches[k] = _create_from_subject_predicate(graph, sub, SKOS[k + 'Match'])
        con = Concept(
            uri_to_id(uri),
            uri=uri,
            concept_scheme=conceptscheme,
            labels=_create_from_subject_typelist(graph, sub, valid_label_types),
            notes=_create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types)),
            sources=[],
            broader=_create_from_subject_predicate(graph, sub, SKOS.broader),
            narrower=_create_from_subject_predicate(graph, sub, SKOS.narrower),
            related=_create_from_subject_predicate(graph, sub, SKOS.related),
            subordinate_arrays=_create_from_subject_predicate(graph, sub, ISO.subordinateArray),
            matches=matches
        )
        clist.append(con)

    for sub, pred, obj in collection_graph.triples((None, RDF.type, None)):
        uri = str(sub)
        col = Collection(
            uri_to_id(uri),
            uri=uri,
            concept_scheme=conceptscheme,
            labels=_create_from_subject_typelist(graph, sub, valid_label_types),
            notes=_create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types)),
            sources=[],
            members=_create_from_subject_predicate(graph, sub, SKOS.member),
            superordinates=_get_super_ordinates(conceptscheme, sub, session=s)
        )
        clist.append(col)

    return clist


def _create_from_subject_typelist(graph, subject, typelist):
    list = []
    note_uris = []
    for p in typelist:
        term = SKOS.__getitem__(p)
        list.extend(_create_from_subject_predicate(graph, subject, term, note_uris))
    return list


def _get_super_ordinates(conceptscheme, sub, **kwargs):
    ret = []
    s = kwargs.get('session', requests.Session())
    query = """PREFIX ns:<{}>
    SELECT * WHERE {{?s iso-thes:subordinateArray ns:{}}}""".format(conceptscheme.uri, uri_to_id(sub))
    url = conceptscheme.uri.strip('/').rsplit('/', 1)[0] + "/sparql.json"
    res = do_get_request(url, s, params={'query': query})
    r = res.json()
    for result in r["results"]["bindings"]:
        ret.append(uri_to_id(result["s"]["value"]))
    return ret


def _create_from_subject_predicate(graph, subject, predicate, note_uris=None):
    list = []
    for s, p, o in graph.triples((subject, predicate, None)):
        type = predicate.split('#')[-1]
        if Label.is_valid_type(type):
            o = _create_label(o, type)
        elif Note.is_valid_type(type):
            if o.toPython() not in note_uris:
                note_uris.append(o.toPython())
                o = _create_note(graph, o, type, False)
            else:
                o = None
        else:
            o = uri_to_id(o)
        if o:
            list.append(o)
    return list


def _create_label(literal, type):
    language = literal.language
    if language is None:
        language = 'und'
    try:
        lang = Label(literal.toPython(), type, language)
    except ValueError:
        log.warning('Received a label with an invalid language tag: %s.', language)
        lang = Label(literal.toPython(), type, 'und')
    return lang


def _create_note(graph, uri, type, change_notes=False):
    if not change_notes and '/rev/' in uri:
        return None
    else:
        note = ''
        language = 'en'

        # http://vocab.getty.edu/aat/scopeNote
        for s, p, o in graph.triples((uri, RDF.value, None)):
            note += o.toPython()
            language = o.language

        # for http://vocab.getty.edu/aat/rev/
        for s, p, o in graph.triples((uri, DC.type, None)):
            note += o.toPython()
        for s, p, o in graph.triples((uri, DC.description, None)):
            note += ': %s' % o.toPython()
        for s, p, o in graph.triples((uri, PROV.startedAtTime, None)):
            note += ' at %s ' % o.toPython()

        return Note(note, type, language)


class SubClassCollector:
    '''
    A utility class to collect all the subclasses of a certain Class from an ontology file.
    '''

    def __init__(self, namespace):
        self.ontology_graphs = {}
        self.namespace = namespace
        self.init_skos()

    def init_skos(self):
        self.subclasses = {}
        self.subclasses[SKOS.Concept] = [
            SKOS.Concept,
            GVP.Concept,
            GVP.PhysPlaceConcept,
            GVP.PhysAdminPlaceConcept,
            GVP.AdminPlaceConcept,
            GVP.PersonConcept,
            GVP.UnknownPersonConcept,
            GVP.GroupConcept
        ]
        self.subclasses[SKOS.Collection] = [
            SKOS.Collection,
            SKOS.OrderedCollection,
            ISO.ThesaurusArray,
            GVP.Hierarchy,
            GVP.Facet,
            GVP.GuideTerm
        ]

    def get_subclasses(self, clazz):
        '''
        Get all registered subclasses for a class.

        :param clazz: An RDF class
        :return: A list of all subclasses, including the original class.
        '''
        return self.subclasses[clazz]

    def collect_subclasses(self, clazz):
        '''
        Collect all subclasses for a class and override the registered classes.

        Since this requires fetching ontology files, it might take a while.

        :param clazz: An RDF class
        :return: A list of all subclasses, including the original class.
        '''
        self.subclasses[clazz] = [clazz]
        if self.namespace not in self.ontology_graphs:
            try:
                graph = rdflib.Graph()
                graph.parse(str(self.namespace), format="application/rdf+xml")
                self.ontology_graphs[self.namespace] = graph
            except:  # pragma: no cover # noqa: E722
                self.ontology_graphs[self.namespace] = None
        g = self.ontology_graphs[self.namespace]
        if g is not None:
            for sub, pred, obj in g.triples((None, RDFS.subClassOf, None)):
                self._is_subclass_of(sub, clazz)
        return self.subclasses[clazz]

    def _is_subclass_of(self, subject, clazz):
        namespace = subject.split('#')[0] + "#"
        if subject in self.subclasses[clazz]:
            return True
        if namespace not in self.ontology_graphs:
            try:
                graph = rdflib.Graph()
                graph.parse(str(namespace), format="application/rdf+xml")
                self.ontology_graphs[namespace] = graph
            except:  # pragma: no cover # noqa: E722
                self.ontology_graphs[namespace] = None
        g = self.ontology_graphs[namespace]
        if g is not None:
            for sub, pred, obj in g.triples((subject, RDFS.subClassOf, None)):
                if obj in self.subclasses[clazz]:
                    self.subclasses[clazz].append(subject)
                    return True
                if obj == clazz:
                    self.subclasses[clazz].append(subject)
                    return True
                if self._is_subclass_of(obj, clazz):
                    return True
        return False


def hierarchy_notetypes(list):
    # A getty scopeNote wil be of type skos.note and skos.scopeNote
    # To avoid doubles and to make sure the getty scopeNote will have type skos.scopeNote and not skos.note,
    # the skos.note will be added at the end of the list
    index_note = list.index('note')
    if index_note != -1:
        list.pop(index_note)
        list.append('note')
    return list


def uri_to_id(uri):
    try:
        return uri.strip('/').rsplit('/', 1)[1]
    except IndexError:
        return uri


def uri_to_graph(uri, **kwargs):
    '''
    :param string uri: :term:`URI` where the RDF data can be found.
    :rtype: rdflib.Graph or `False` if the URI does not exist
    :raises skosprovider.exceptions.ProviderUnavailableException: if the
        getty.edu services are down
    '''
    s = kwargs.get('session', requests.Session())
    graph = rdflib.Graph()
    res = do_get_request(uri, s)
    if res.status_code == 404:
        return False
    graph.parse(data=res.content, format="application/rdf+xml")
    return graph


def do_get_request(url, session=None, headers=None, params=None):
    if not session:
        session = requests.Session()
    try:
        res = session.get(url, headers=headers, params=params)
    except ConnectionError:
        raise ProviderUnavailableException(f"Request could not be executed due to connection issues- Request: {url}")
    except Timeout:  # pragma: no cover
        raise ProviderUnavailableException(f"Request could not be executed due to timeout - Request: {url}")
    if res.status_code >= 500:
        raise ProviderUnavailableException(
            f"Request could not be executed due to server issues - Request: {url}. Response: {res.content}.")
    if not res.encoding:
        res.encoding = 'utf-8'
    return res
