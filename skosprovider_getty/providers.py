#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
import requests
import tempfile

from rdflib.namespace import RDF, SKOS

from skosprovider.providers import VocabularyProvider

from skosprovider.skos import (
    Concept,
    Collection
)

#class GettyProvider(VocabularyProvider):
class GettyProvider():

    def __init__(self, metadata, **kwargs):

        if not 'default_language' in metadata:
            metadata['default_language'] = 'nl'
        if 'base_url' in kwargs:
            self.base_url = kwargs['base_url']
        else:
            self.base_url = 'http://vocab.getty.edu/aat/'

        #super(GettyProvider, self).__init__(metadata, **kwargs)


    def get_by_id(self, id):

        # download rdf to a temporally file
        # create tempfile
        rdf_file = tempfile.NamedTemporaryFile()
        try:
            # get data of id
            r = requests.get('%s%d.nt' % (self.base_url, id))
            # write data to temporally file
            rdf_file.write(r.text)
            rdf_file.flush()

            # parse the rdf to the rdf graph
            graph = rdflib.Graph()
            graph.parse(rdf_file.name, format='nt')
            rdf_file.close()

            # get the concept
            provider = RDFProvider({'id': 'test', 'conceptscheme_id': 1}, graph)

            # concept = provider.get_by_id(provider)

            concept = provider.list[0]

            return concept

        except:
            raise
        finally:
            # always delete temporally file
            rdf_file.close()


# todo repeating RDFProvider for skosprovider_rdf because problems with labels and notes


'''
This module contains an RDFProvider, an implementation of the
:class:`skosprovider.providers.VocabularyProvider` interface that uses a
:class:`rdflib.graph.Graph` as input.
'''

import logging
log = logging.getLogger(__name__)

from skosprovider.providers import MemoryProvider
from skosprovider.skos import (
    Concept,
    Collection,
    Label,
    Note
)

from rdflib.namespace import RDF, SKOS


class RDFProvider(MemoryProvider):
    '''
    A simple vocabulary provider that use an :class:`rdflib.graph.Graph`
    as input. The provider expects a RDF graph with elements that represent
    the SKOS concepts and collections.

    Please be aware that this provider needs to load the entire graph in memory.
    '''

    def __init__(self, metadata, graph, **kwargs):
        super(RDFProvider, self).__init__(metadata, [], **kwargs)
        self.conceptscheme_id = metadata.get(
            'conceptscheme_id', metadata.get('id')
        )
        self.graph = graph
        self.list = self._from_graph()

    def _from_graph(self):
        clist = []
        for sub, pred, obj in self.graph.triples((None, RDF.type, SKOS.Concept)):
            uri = str(sub)
            con = Concept(uri, uri=uri)
            con.broader = self._create_from_subject_predicate(sub, SKOS.broader)
            con.narrower = self._create_from_subject_predicate(sub, SKOS.narrower)
            con.related = self._create_from_subject_predicate(sub, SKOS.related)
            con.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            #con.notes = self._create_from_subject_typelist(sub, Note.valid_types)
            clist.append(con)

        for sub, pred, obj in self.graph.triples((None, RDF.type, SKOS.Collection)):
            uri = str(sub)
            col = Collection(uri, uri=uri)
            col.members = self._create_from_subject_predicate(sub, SKOS.member)
            col.labels = self._create_from_subject_typelist(sub, Label.valid_types)
            clist.append(col)
        self._fill_member_of(clist)

        return clist

    def _fill_member_of(self, clist):
        collections = list(set([c for c in clist if isinstance(c, Collection)]))
        for col in collections:
            for c in clist:
                 if c.id in col.members:
                    c.member_of.append(col.id)
                    break;

    def _create_from_subject_typelist(self,subject,typelist):
        list=[]
        for p in typelist:
            term=SKOS.term(p)
            list.extend(self._create_from_subject_predicate(subject,term))
        return list

    def _create_from_subject_predicate(self, subject, predicate):
        list = []
        for s, p, o in self.graph.triples((subject, predicate, None)):
            type = predicate.split('#')[-1]
            if Label.is_valid_type(type):
                o = self._create_label(o, type)
            elif Note.is_valid_type(type):
                o = self._create_note(o, type)
            else:
                o = str(o)
            list.append(o)
        return list

    def _create_label(self, literal, type):
        if not Label.is_valid_type(type):
            raise ValueError(
                'Type of Label is not valid.'
            )
        language = literal.language
        if language is None:
            return None
        else:
            language.encode('utf-8')
        return Label(literal.encode('utf-8'), type, language)

    def _create_note(self, literal, type):
        if not Note.is_valid_type(type):
            raise ValueError(
                'Type of Note is not valid.'
            )
        language = literal.language
        if language is None:
            return None
        else:
            language.encode('utf-8')
        return Note(literal.encode('utf-8'), type, language)
