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

import re

# todo: default exclude change notes --> from_graph in class

# todo: id not always int --> id_from_uri uri.strip('/').rsplit('/',1)[1]

# todo repeating RDFProvider for skosprovider_rdf because problems with labels and notes

def from_graph(graph):
    clist = []
    for sub, pred, obj in graph.triples((None, RDF.type, SKOS.Concept)):
        uri = str(sub)
        con = Concept(int(re.findall('\d+', uri)[0]), uri=uri)
        con.broader = _create_from_subject_predicate(graph, sub, SKOS.broader)
        con.narrower = _create_from_subject_predicate(graph, sub, SKOS.narrower)
        con.related = _create_from_subject_predicate(graph, sub, SKOS.related)
        con.labels = _create_from_subject_typelist(graph, sub, Label.valid_types)
        con.notes = _create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types))
        clist.append(con)

    for sub, pred, obj in graph.triples((None, RDF.type, SKOS.Collection)):
        uri = str(sub)
        col = Collection(int(re.findall('\d+', uri)[0]), uri=uri)
        col.members = _create_from_subject_predicate(graph, sub, SKOS.member)
        col.labels = _create_from_subject_typelist(graph, sub, Label.valid_types)
        col.notes = _create_from_subject_typelist(graph, sub, hierarchy_notetypes(Note.valid_types))
        clist.append(col)
    _fill_member_of(clist)

    return clist

def _fill_member_of(clist):
    collections = list(set([c for c in clist if isinstance(c, Collection)]))
    for col in collections:
        for c in clist:
             if c.id in col.members:
                c.member_of.append(int(re.findall('\d+', col.i)[0]))
                break

def _create_from_subject_typelist(graph, subject,typelist):
    list=[]
    note_uris = []
    for p in typelist:
        term=SKOS.term(p)
        list.extend(_create_from_subject_predicate(graph, subject, term, note_uris))
    return list

def _create_from_subject_predicate(graph, subject, predicate, note_uris=None):
    list = []
    for s, p, o in graph.triples((subject, predicate, None)):
        type = predicate.split('#')[-1]
        if Label.is_valid_type(type):
            o = _create_label(o, type)
        elif Note.is_valid_type(type):
            if decode_literal(o) not in note_uris:
                note_uris.append(decode_literal(o))
                o = _create_note(graph, o, type)
            else:
                o = None
        else:
            o = int(re.findall('\d+', o)[0])
        if o:
            list.append(o)
    return list

def _create_label(literal, type):
    if not Label.is_valid_type(type):
        raise ValueError(
            'Type of Label is not valid.'
        )
    language = literal.language
    if language is None:
        return None
    return Label(decode_literal(literal), type, language)

def _create_note(graph, uri, type):

    try:

        note = ''
        language = 'en'

        # http://vocab.getty.edu/aat/scopeNote
        for s, p, o in graph.triples((uri, RDF.value, None)):
            note += decode_literal(o)
            language = o.language

        # for http://vocab.getty.edu/aat/rev/
        for s, p, o in graph.triples((uri, DC.type, None)):
            note += decode_literal(o)
        for s, p, o in graph.triples((uri, DC.description, None)):
            note += ': %s' % decode_literal(o)
        for s, p, o in graph.triples((uri, PROV.startedAtTime, None)):
            note += ' at %s ' % decode_literal(o)

        return Note(note, type, language)

    # for python2.7 this is urllib2.HTTPError
    # for python3 this is urllib.error.HTTPError
    except Exception as err:
        if hasattr(err, 'code'):
            if err.code == 404:
                return None
        else:
            raise

def decode_literal(literal):
    # the literals are of different type in python 2.7 and python 3
    if isinstance(literal, str):
        return literal.encode('utf-8').decode('utf-8')
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