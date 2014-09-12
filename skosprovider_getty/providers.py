#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
import requests
import warnings
import re

import logging
log = logging.getLogger(__name__)

from skosprovider.providers import VocabularyProvider

from skosprovider_getty.utils import (
    from_graph
)

#todo: ATT en TGN with different constructors who overwrite the GettyProvider



class GettyProvider(VocabularyProvider):
    '''A provider that can work with the GETTY rdf files of
    http://vocab.getty.edu/

    '''

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

    def get_by_id(self, id, include_revision_notes=False):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by id

        :param (int) id: integer id of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """
        graph = rdflib.Graph()
        try:
            graph.parse('%s/%s.rdf' % (self.url, id))
            # get the concept
            graph_to_skos = from_graph(graph)
            concept = graph_to_skos[0]
            return concept

        # for python2.7 this is urllib2.HTTPError
        # for python3 this is urllib.error.HTTPError
        except Exception as err:
            if hasattr(err, 'code'):
                if err.code == 404:
                    return None
            else:
                raise


    def get_by_uri(self, uri):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by uri

        :param (str) uri: string uri of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """

        id = int(re.findall('\d+', uri)[0])

        return self.get_by_id(id)

    def expand(self, id):
        warnings.warn(
            'This provider does not support this yet. It still in developement',
             UserWarning
        )
        return False


    def find(self, query):
        '''Find concepts that match a certain query.

        Currently query is expected to be a dict, so that complex queries can
        be passed. You can use this dict to search for concepts or collections
        with a certain label, with a certain type and for concepts that belong
        to a certain collection.

        .. code-block:: python

            # Find anything that has a label of church.
            provider.find({'label': 'church'}

            # Find all concepts that are a part of collection 5.
            provider.find({'type': 'concept', 'collection': {'id': 5})

            # Find all concepts, collections or children of these
            # that belong to collection 5.
            provider.find({'collection': {'id': 5, 'depth': 'all'})

        :param query: A dict that can be used to express a query. The following
            keys are permitted:

            * `label`: Search for something with this label value. An empty \
                label is equal to searching for all concepts.
            * `type`: Limit the search to certain SKOS elements. If not \
                present `all` is assumed:

                * `concept`: Only return :class:`skosprovider.skos.Concept` \
                    instances.
                * `collection`: Only return \
                    :class:`skosprovider.skos.Collection` instances.
                * `all`: Return both :class:`skosprovider.skos.Concept` and \
                    :class:`skosprovider.skos.Collection` instances.
            * `collection`: Search only for concepts belonging to a certain \
                collection. This argument should be a dict with two keys:

                * `id`: The id of a collection. Required.
                * `depth`: Can be `members` or `all`. Optional. If not \
                    present, `members` is assumed, meaning only concepts or \
                    collections that are a direct member of the collection \
                    should be considered. When set to `all`, this method \
                    should return concepts and collections that are a member \
                    of the collection or are a narrower concept of a member \
                    of the collection.

        :returns: A :class:`lst` of concepts and collections. Each of these
            is a dict with the following keys:

            * id: id within the conceptscheme
            * uri: :term:`uri` of the concept or collection
            * type: concept or collection
            * label: A label to represent the concept or collection. It is \
                determined by looking at the `**kwargs` parameter, the default \
                language of the provider and finally falls back to `en`.
        '''

        #todo interprete query parameters + which getty vocaulairy
        label = query['label']
        type = query['type']
        collection = query['collection']

        #todo build sparql query
        keywords = '"church* AND abbey*"'
        data = {"query": """PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gvp: <http://vocab.getty.edu/ontology#>
        PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX gvp_lang: <http://vocab.getty.edu/language/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?Subject ?Term ?Parents ?ScopeNote ?Type {
        ?Subject luc:term""" + keywords + """; a ?typ.
        ?typ rdfs:subClassOf gvp:Subject; rdfs:label ?Type.
        optional {?Subject gvp:prefLabelGVP [skosxl:literalForm ?Term]}
        optional {?Subject gvp:parentStringAbbrev ?Parents}
        optional {?Subject skos:scopeNote [dct:language gvp_lang:en; rdf:value ?ScopeNote]}}"""
                }

        #send request to getty
        r = requests.get("http://vocab.getty.edu/sparql.json", params=data).json()

        #todo build answer
        answer = []
        for result in r["results"]["bindings"]:
            item = {'id': result["Subject"]["value"],
                    'uri': result["Subject"]["value"],
                    'type': type,
                    'label': result["Term"]["value"]
                    }
            answer.append(item)
        return answer

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