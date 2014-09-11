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
        con.notes = _create_from_subject_typelist(graph, sub, Note.valid_types)
        clist.append(con)

    for sub, pred, obj in graph.triples((None, RDF.type, SKOS.Collection)):
        uri = str(sub)
        col = Collection(int(re.findall('\d+', uri)[0]), uri=uri)
        col.members = _create_from_subject_predicate(graph, sub, SKOS.member)
        col.labels = _create_from_subject_typelist(graph, sub, Label.valid_types)
        col.notes = _create_from_subject_typelist(graph, sub, Note.valid_types)
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
    for p in typelist:
        term=SKOS.term(p)
        list.extend(_create_from_subject_predicate(graph, subject,term))
    return list

def _create_from_subject_predicate(graph, subject, predicate):
    list = []
    for s, p, o in graph.triples((subject, predicate, None)):
        type = predicate.split('#')[-1]
        if Label.is_valid_type(type):
            o = _create_label(o, type)
        elif Note.is_valid_type(type):
            o = _create_note(o, type)
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

def _create_note(uri, type):

    note_graph = None

    try:

        note_graph = rdflib.Graph()
        note_graph.parse('%s.rdf' % uri)

    except:
        log.debug('Parse error for %s, probably no records found' % uri)

    if note_graph:
        note = ''
        language = 'en'

        # for http://vocab.getty.edu/aat/rev/
        for s, p, o in note_graph.triples((uri, DC.type, None)):
            note += decode_literal(o)
        for s, p, o in note_graph.triples((uri, DC.description, None)):
            note += ': %s' % decode_literal(o)
        for s, p, o in note_graph.triples((uri, PROV.startedAtTime, None)):
            note += ' at %s ' % decode_literal(o)

        # http://vocab.getty.edu/aat/scopeNote
        for s, p, o in note_graph.triples((uri, RDF.value, None)):
            note += o
            language = o.language

        return Note(note, type, language)
    else:
        return None

def decode_literal(literal):
    if isinstance(literal, str):
        return literal.encode('utf-8').decode('utf-8')
    else:
        return literal.encode('utf-8')