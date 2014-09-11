#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
import requests
import tempfile

from skosprovider.providers import VocabularyProvider

import logging
log = logging.getLogger(__name__)

from skosprovider_getty.utils import (
    from_graph
)

from rdflib.namespace import RDF, SKOS

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


    # todo: id's of broader, narrower and the concept itself are now uri's
    def get_by_id(self, id):

        graph = rdflib.Graph()
        graph.parse('%s%d.rdf' % (self.base_url, id))

        # get the concept
        graph_to_skos = from_graph(graph)

        concept = graph_to_skos[0]

        return concept


