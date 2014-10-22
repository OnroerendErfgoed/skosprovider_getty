#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
from rdflib.graph import Graph
from rdflib.term import URIRef

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

class getty_to_skos():

    def __init__(self, conceptscheme_uri, change_notes=False):
        self.change_notes = change_notes
        self.conceptscheme = self._conceptscheme_from_uri(conceptscheme_uri)
        self.graph = None
        self.subclasses =SubClasses(gvp)
        self.subclasses.collect_subclasses(SKOS.Concept)
        self.subclasses.collect_subclasses(SKOS.Collection)

    def _conceptscheme_from_uri(self, conceptscheme_uri):
        base_url = conceptscheme_uri.strip('/').rsplit('/', 1)[0]
        subject = conceptscheme_uri.strip('/') + "/"
        self.graph = uri_to_graph('%s.rdf' % (subject))
        # get the conceptscheme
        conceptscheme = ConceptScheme(subject)
        conceptscheme.notes = []
        conceptscheme.labels = []
        if self.graph is not False:
            for s, p, o in self.graph.triples((URIRef(subject), RDFS.label, None)):
                label = Label(o.toPython(), "prefLabel", 'en')
                conceptscheme.labels.append(label)
        return conceptscheme

    def things_from_graph(self, graph):
        self.graph = graph
        clist = []
        concept_graph = Graph()
        collection_graph = Graph()
        for sc in self.subclasses.get_subclasses(SKOS.Concept):
            concept_graph += graph.triples((None, RDF.type, sc))
        for sc in self.subclasses.get_subclasses(SKOS.Collection):
            collection_graph += graph.triples((None, RDF.type, sc))
        for sub, pred, obj in concept_graph.triples((None, RDF.type, None)):
            uri = str(sub)
            con = Concept(uri_to_id(uri), uri=uri)
            con.broader = self._create_from_subject_predicate(sub, SKOS.broader)
            con.narrower = self._create_from_subject_predicate(sub, SKOS.narrower)
            con.related = self._create_from_subject_predicate(sub, SKOS.related)
            con.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            con.notes = self._create_from_subject_typelist(sub, hierarchy_notetypes(Note.valid_types))
            for k in con.matches.keys():
                con.matches[k] = self._create_from_subject_predicate(sub, URIRef(SKOS + k +'Match'))
            con.subordinate_arrays = self._create_from_subject_predicate(sub, ISO.subordinateArray)
            #con.subordinate_arrays = self._get_members(self._create_from_subject_predicate(sub, ISO.subordinateArray))
            con.concept_scheme = self.conceptscheme
            clist.append(con)

        for sub, pred, obj in collection_graph.triples((None, RDF.type, None)):
            uri = str(sub)
            col = Collection(uri_to_id(uri), uri=uri)
            col.members = self._create_from_subject_predicate(sub, SKOS.member)
            col.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            col.notes = self._create_from_subject_typelist(sub, hierarchy_notetypes(Note.valid_types))
            col.superordinates = self._create_from_subject_predicate(sub, ISO.superOrdinate)
            col.concept_scheme = self.conceptscheme
            clist.append(col)

        return clist

    def _create_from_subject_typelist(self, subject, typelist):
        list=[]
        note_uris = []
        for p in typelist:
            term = SKOS.term(p)
            list.extend(self._create_from_subject_predicate(subject, term, note_uris))
        return list

    def _create_from_subject_predicate(self, subject, predicate, note_uris=None):
        list = []
        for s, p, o in self.graph.triples((subject, predicate, None)):
            type = predicate.split('#')[-1]
            if Label.is_valid_type(type):
                o = self._create_label(o, type)
            elif Note.is_valid_type(type):
                if o.toPython() not in note_uris:
                    note_uris.append(o.toPython())
                    o = self._create_note(o, type)
                else:
                    o = None
            else:
                o = uri_to_id(o)
            if o:
                list.append(o)
        return list

    def _create_label(self, literal, type):
        language = literal.language
        if language is None:
            return None
        return Label(literal.toPython(), type, language)

    def _create_note(self, uri, type):
        if not self.change_notes and '/rev/' in uri:
            return None
        else:
            note = u''
            language = 'en'

            # http://vocab.getty.edu/aat/scopeNote
            for s, p, o in self.graph.triples((uri, RDF.value, None)):
                note += o.toPython()
                language = o.language

            # for http://vocab.getty.edu/aat/rev/
            for s, p, o in self.graph.triples((uri, DC.type, None)):
                note += o.toPython()
            for s, p, o in self.graph.triples((uri, DC.description, None)):
                note += ': %s' % o.toPython()
            for s, p, o in self.graph.triples((uri, PROV.startedAtTime, None)):
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
            graph = rdflib.Graph()
            result = graph.parse(str(self.namespace))
            self.ontology_graphs[self.namespace] = graph
        g = self.ontology_graphs[self.namespace]
        for sub, pred, obj in g.triples((None, RDFS.subClassOf, None)):
            self._is_subclass_of(sub, clazz)
        return self.subclasses[clazz]

    def _is_subclass_of(self, subject, clazz):
        namespace = subject.split('#')[0] +"#"
        if subject in self.subclasses[clazz]:
            return True
        if namespace not in self.ontology_graphs:
            graph = rdflib.Graph()
            result = graph.parse(str(namespace))
            self.ontology_graphs[namespace] = graph
        g = self.ontology_graphs[namespace]
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
    graph = rdflib.Graph()
    try:
        graph.parse(uri)
        return graph
    # for python2.7 this is urllib2.HTTPError
    # for python3 this is urllib.error.HTTPError
    except Exception as err:
        if hasattr(err, 'code'):
            if err.code == 404:
                return False
        else:
            raise

