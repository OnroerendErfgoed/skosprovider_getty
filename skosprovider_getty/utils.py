#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib

from skosprovider.skos import (
    Concept,
    Collection,
    Label,
    Note
)

import logging
log = logging.getLogger(__name__)

from rdflib.namespace import RDF, SKOS, DC
PROV = rdflib.Namespace('http://www.w3.org/ns/prov#')

class getty_to_skos():

    def __init__(self, graph, change_notes=False):
        self.graph = graph
        self.change_notes = change_notes

    def from_graph(self):
        clist = []
        for sub, pred, obj in self.graph.triples((None, RDF.type, SKOS.Concept)):
            uri = str(sub)
            con = Concept(uri_to_id(uri), uri=uri)
            con.broader = self._create_from_subject_predicate(sub, SKOS.broader)
            con.narrower = self._create_from_subject_predicate(sub, SKOS.narrower)
            con.related = self._create_from_subject_predicate(sub, SKOS.related)
            con.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            con.notes = self._create_from_subject_typelist(sub, hierarchy_notetypes(Note.valid_types))
            clist.append(con)

        for sub, pred, obj in self.graph.triples((None, RDF.type, SKOS.Collection)):
            uri = str(sub)
            col = Collection(uri_to_id(uri), uri=uri)
            col.members = self._create_from_subject_predicate(sub, SKOS.member)
            col.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            col.notes = self._create_from_subject_typelist(sub, hierarchy_notetypes(Note.valid_types))
            clist.append(col)

        return clist

    def _create_from_subject_typelist(self, subject,typelist):
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
                if literal_to_str(o) not in note_uris:
                    note_uris.append(literal_to_str(o))
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
        return Label(literal_to_str(literal), type, language)

    def _create_note(self, uri, type):
        if not self.change_notes and '/rev/' in uri:
            return None
        else:
            note = ''
            language = 'en'

            # http://vocab.getty.edu/aat/scopeNote
            for s, p, o in self.graph.triples((uri, RDF.value, None)):
                note += literal_to_str(o)
                language = o.language

            # for http://vocab.getty.edu/aat/rev/
            for s, p, o in self.graph.triples((uri, DC.type, None)):
                note += literal_to_str(o)
            for s, p, o in self.graph.triples((uri, DC.description, None)):
                note += ': %s' % literal_to_str(o)
            for s, p, o in self.graph.triples((uri, PROV.startedAtTime, None)):
                note += ' at %s ' % literal_to_str(o)

            return Note(note, type, language)

def literal_to_str(literal):
    # the literals are of different type in python 2.7 and python 3
    if isinstance(literal, str):
        return str(literal)
    else:
        return literal.encode('utf-8')

def hierarchy_notetypes(list):
    # A getty scopeNote wil be of type skos.note and skos.scopeNote
    # To avoid doubles and to make sure the the getty scopeNote will have type skos.scopeNote and not skos.note,
    # the skos.note will be added at the end of the list
    index_note = list.index('note')
    if index_note != -1:
        list.pop(index_note)
        list.append('note')
    return list

def uri_to_id(uri):
    return uri.strip('/').rsplit('/',1)[1]