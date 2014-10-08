#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib

from skosprovider.skos import (
    Concept,
    Collection,
    Label,
    Note,
    ConceptScheme)

import logging
log = logging.getLogger(__name__)

from rdflib.namespace import RDF, SKOS, DC
PROV = rdflib.Namespace('http://www.w3.org/ns/prov#')
ISO = rdflib.Namespace('http://purl.org/iso25964/skos-thes#')

class getty_to_skos():

    def __init__(self, conceptscheme=None, change_notes=False):
        self.change_notes = change_notes
        self.conceptscheme = conceptscheme
        self.graph = None

    def conceptscheme_from_uri(self, conceptscheme_uri):
        self.graph = uri_to_graph('%s.rdf' % (conceptscheme_uri))
        # get the conceptscheme
        conceptscheme = ConceptScheme(conceptscheme_uri)
        #todo rdf from conceptscheme cannot be found so labels and notes are not available
        if self.graph is not False:
            conceptscheme.labels = self._create_from_subject_typelist(conceptscheme_uri, Label.valid_types)
            conceptscheme.notes = self._create_from_subject_typelist(conceptscheme_uri, hierarchy_notetypes(Note.valid_types))
        return conceptscheme

    def things_from_graph(self, graph):
        self.graph = graph
        clist = []
        for sub, pred, obj in graph.triples((None, RDF.type, SKOS.Concept)):
            uri = str(sub)
            con = Concept(uri_to_id(uri), uri=uri)
            con.broader = self._create_from_subject_predicate(sub, SKOS.broader)
            con.narrower = self._create_from_subject_predicate(sub, SKOS.narrower)
            con.related = self._create_from_subject_predicate(sub, SKOS.related)
            con.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            con.notes = self._create_from_subject_typelist(sub, hierarchy_notetypes(Note.valid_types))
            con.subordinate_arrays = self._get_members(self._create_from_subject_predicate(sub, ISO.subordinateArray))
            con.concept_scheme = self.conceptscheme
            clist.append(con)

        for sub, pred, obj in graph.triples((None, RDF.type, SKOS.Collection)):
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

    def _get_members(self, arr):
        member_list = []
        if len(arr) > 0:
            id = arr[0]
            uri = self.conceptscheme.uri + '/' + id
            graph = uri_to_graph(uri)
            for s, p, o in graph.triples((None, SKOS.member, None)):
                o = uri_to_id(o)
                if o:
                    member_list.append(o)
        return member_list

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

