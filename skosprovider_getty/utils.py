# -*- coding: utf-8 -*-

'''
This module contains utility functions for :mod:`skosprovider_getty`.
'''
import requests
import rdflib
from rdflib.graph import Graph
from rdflib.term import URIRef
from requests.packages.urllib3.exceptions import ConnectionError
from skosprovider.exceptions import ProviderUnavailableException

from skosprovider.skos import (
    Concept,
    Collection,
    Label,
    Note,
    ConceptScheme)

import logging

log = logging.getLogger(__name__)

from rdflib.namespace import RDFS, RDF, SKOS, DC

PROV = rdflib.Namespace('http://www.w3.org/ns/prov#')
ISO = rdflib.Namespace('http://purl.org/iso25964/skos-thes#')
gvp = rdflib.Namespace('http://vocab.getty.edu/ontology#')


def get_subclasses():
    subclasses = SubClasses(gvp)
    subclasses.collect_subclasses(SKOS.Concept)
    subclasses.collect_subclasses(SKOS.Collection)
    return subclasses


def conceptscheme_from_uri(conceptscheme_uri):
    '''
    Read a SKOS Conceptscheme from a :term:`URI`

    :param string conceptscheme_uri: URI of the conceptscheme.
    :rtype: skosprovider.skos.ConceptScheme
    '''

    # get the conceptscheme
    graph = uri_to_graph('%s.rdf' % (conceptscheme_uri))

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


def things_from_graph(graph, subclasses, conceptscheme):
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
            con.matches[k] = _create_from_subject_predicate(graph, sub, URIRef(SKOS + k + 'Match'))
        con = Concept(
            uri_to_id(uri),
            uri=uri,
            concept_scheme = conceptscheme,
            labels = _create_from_subject_typelist(graph, sub, Label.valid_types),
            notes = _create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types)),
            sources = [],
            broader = _create_from_subject_predicate(graph, sub, SKOS.broader),
            narrower = _create_from_subject_predicate(graph, sub, SKOS.narrower),
            related = _create_from_subject_predicate(graph, sub, SKOS.related),
            subordinate_arrays = _create_from_subject_predicate(graph, sub, ISO.subordinateArray),
            matches=matches
        )
        clist.append(con)

    for sub, pred, obj in collection_graph.triples((None, RDF.type, None)):
        uri = str(sub)
        col = Collection(
            uri_to_id(uri),
            uri=uri,
            concept_scheme = conceptscheme,
            labels = _create_from_subject_typelist(graph, sub, Label.valid_types),
            sources = [],
            notes = _create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types)),
            members = _create_from_subject_predicate(graph, sub, SKOS.member),
            col.superordinates = _get_super_ordinates(conceptscheme, sub)
        )
        clist.append(col)

    return clist


def _create_from_subject_typelist(graph, subject, typelist):
    list = []
    note_uris = []
    for p in typelist:
        term = SKOS.term(p)
        list.extend(_create_from_subject_predicate(graph, subject, term, note_uris))
    return list


def _get_super_ordinates(conceptscheme, sub):
    list = []

    query = """PREFIX ns:<%s>
    SELECT * WHERE {?s iso-thes:subordinateArray ns:%s}""" % (conceptscheme.uri, uri_to_id(sub))
    request = conceptscheme.uri.strip('/').rsplit('/', 1)[0] + "/sparql.json"
    try:
        res = requests.get(request, params={"query": query})
    except ConnectionError as e:
        raise ProviderUnavailableException("Request could not be executed - Request: %s - Params: %s" % (request, query))
    if res.status_code == 404:
        raise ProviderUnavailableException("Service not found (status_code 404) - Request: %s - Params: %s" % (request, query))
    if not res.encoding:
        res.encoding = 'utf-8'
    r = res.json()
    for result in r["results"]["bindings"]:
        list.append(uri_to_id(result["s"]["value"]))
    return list


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
    return Label(literal.toPython(), type, language)


def _create_note(graph, uri, type, change_notes=False):
    if not change_notes and '/rev/' in uri:
        return None
    else:
        note = u''
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


class SubClasses:
    def __init__(self, namespace):
        self.subclasses = {}
        self.ontology_graphs = {}
        self.namespace = namespace

    def get_subclasses(self, clazz):
        return self.subclasses[clazz]

    def collect_subclasses(self, clazz):
        if clazz not in self.subclasses:
            self.subclasses[clazz] = []
        if self.namespace not in self.ontology_graphs:
            try:
                graph = rdflib.Graph()
                result = graph.parse(str(self.namespace), format="application/rdf+xml")
                self.ontology_graphs[self.namespace] = graph
            except:
                self.ontology_graphs[self.namespace] = None
        g = self.ontology_graphs[self.namespace]
        if not g is None:
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
                result = graph.parse(str(namespace), format="application/rdf+xml")
                self.ontology_graphs[namespace] = graph
            except:
                self.ontology_graphs[namespace] = None
        g = self.ontology_graphs[namespace]
        if not g is None:
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
    return uri.strip('/').rsplit('/', 1)[1]


def uri_to_graph(uri):
    '''
    :param string uri: :term:`URI` where the RDF data can be found.
    :rtype: rdflib.Graph
    :raises skosprovider.exceptions.ProviderUnavailableException: if the
        getty.edu services are down
    '''
    graph = rdflib.Graph()
    try:
        res = requests.get(uri)
    except requests.ConnectionError as e:
        raise ProviderUnavailableException("URI not available: %s" % uri)
    if res.status_code == 404:
        return False
    graph.parse(data=res.content)
    return graph

