#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
from skosprovider.providers import VocabularyProvider

import logging
log = logging.getLogger(__name__)

from skosprovider_getty.utils import (
    from_graph
)

import warnings

import re


class GettyProvider(VocabularyProvider):

    def __init__(self, metadata, **kwargs):
        if not 'default_language' in metadata:
            metadata['default_language'] = 'en'
        if 'base_url' in kwargs:
            self.base_url = kwargs['base_url']
        else:
            self.base_url = 'http://vocab.getty.edu/%s'
        if 'getty' in kwargs:
            self.getty = kwargs['getty']
        else:
            self.getty = 'att'
        if not 'url' in kwargs:
            self.url = self.base_url % self.getty
        else:
            self.url = kwargs['url']

        super(GettyProvider, self).__init__(metadata, **kwargs)

    def get_by_id(self, id):

        graph = rdflib.Graph()
        graph.parse('%s/%s.rdf' % (self.url, id))
        # get the concept
        graph_to_skos = from_graph(graph)
        concept = graph_to_skos[0]

        return concept

    def get_by_uri(self, uri):

        id = int(re.findall('\d+', uri)[0])

        return self.get_by_id(id)

    def expand(self, id):
        warnings.warn(
            'This provider does not support this yet. It still in developement',
             UserWarning
        )
        return False


    def find(self, query):
        warnings.warn(
        'This provider does not support this yet. It still in developement',
         UserWarning
        )
        return False

    def get_all(self):
        warnings.warn(
        'This provider does not support this yet. It still in developement',
         UserWarning
        )
        return False

    def get_top_concepts(self):
        warnings.warn(
        'This provider does not support this yet. It still in developement',
         UserWarning
        )
        return False