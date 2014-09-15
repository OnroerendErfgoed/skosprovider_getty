#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
import requests
import warnings

import logging

log = logging.getLogger(__name__)

from skosprovider.providers import VocabularyProvider

from skosprovider_getty.utils import (
    getty_to_skos,
    uri_to_id
)


def _build_keywords(label):
    keyword_list = label.split(" ")
    keywords = ""
    for idx, item in enumerate(keyword_list):
        if idx + 1 == len(keyword_list):
            keywords = keywords + item
        else:
            keywords = keywords + item + " AND "

    return "'" + keywords + "'"


def _build_sparql(getty, keywords, type_c, coll_id, coll_depth):
    getty += ":"
    keywords_x = "luc:term " + keywords
    getty_x = "skos:inScheme " + getty
    if coll_id is None:
        coll_x = ""
    else:
        if coll_depth == 'all':
            coll_x = "gvp:broaderExtended " + getty + coll_id
        elif coll_depth == 'members':
            coll_x = "gvp:broader " + getty + coll_id

    if type_c == 'all':
        type_x = "{?Type rdfs:subClassOf skos:Concept} UNION {?Type rdfs:subClassOf skos:Collection}"
    elif type_c == 'concept':
        type_x = "{?Type rdfs:subClassOf skos:Concept}"
    elif type_c == 'collection':
        type_x = "{?Type rdfs:subClassOf skos:Collection}"

    query = """
        PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gvp: <http://vocab.getty.edu/ontology#>
        PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX gvp_lang: <http://vocab.getty.edu/language/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?Subject ?Term ?Type ?Id {
        ?Subject rdf:type ?Type; dc:identifier ?Id; """ + keywords_x + """; """ + getty_x + """; """ + coll_x + """;.
        """ + type_x + """
        optional {?Subject gvp:prefLabelGVP [skosxl:literalForm ?Term]}}
        """
    print(query)
    return query


class GettyProvider(VocabularyProvider):
    """A provider that can work with the GETTY rdf files of
    http://vocab.getty.edu/

    """

    def __init__(self, metadata, **kwargs):
        """ Constructor of the :class:`skosprovider_getty.providers.GettyProvider`

        :param (dict) metadata: metadata of the provider
        :param kwargs: arguments defining the provider.
            * Typical arguments are  `base_url`, `getty` and `url`.
                The `url` is a composition of the `base_url` and `getty`
            * The :class:`skosprovider_getty.providers.AATProvider`
                is the default :class:`skosprovider_getty.providers.GettyProvider`
        """
        if not 'default_language' in metadata:
            metadata['default_language'] = 'en'
        if 'base_url' in kwargs:
            self.base_url = kwargs['base_url']
        else:
            self.base_url = 'http://vocab.getty.edu/'
        if 'getty' in kwargs:
            self.getty = kwargs['getty']
        else:
            self.getty = 'aat'
        if not 'url' in kwargs:
            self.url = self.base_url + self.getty
        else:
            self.url = kwargs['url']

        super(GettyProvider, self).__init__(metadata, **kwargs)

    def get_by_id(self, id, change_notes=False):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by id

        :param (str) id: integer id of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """
        graph = rdflib.Graph()
        try:
            graph.parse('%s/%s.rdf' % (self.url, id))
            # get the concept
            graph_to_skos = getty_to_skos(graph, change_notes).from_graph()
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

    def get_by_uri(self, uri, change_notes=False):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by uri

        :param (str) uri: string uri of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """

        id = uri_to_id(uri)

        return self.get_by_id(id, change_notes)

    def expand(self, id):
        warnings.warn(
            'This provider does not support this yet. It still in development',
            UserWarning
        )
        return False


    def find(self, query):
        # #  interprete and validate query parameters (label, type and collection)
        # Label
        if 'label' in query:
            label = query['label']
        if not label:
            label = None
        # Type: 'collection','concept' or 'all'
        type_c = 'all'
        if 'type' in query:
            type_c = query['type']
        if type_c not in ('all', 'concept', 'collection'):
            raise ValueError("type: only the following values are allowed: 'all', 'concept', 'collection'")
        #Collection to search in (optional)
        coll_id = None
        coll_depth = None
        if 'collection' in query:
            coll = query['collection']
            if not 'id' in coll:
                raise ValueError("collection: 'id' is required key if a collection-dictionary is given")
            coll_id = coll['id']
            coll_depth = 'members'
            if 'depth' in coll:
                coll_depth = coll['depth']
            if coll_depth not in ('members', 'all'):
                raise ValueError(
                    "collection - 'depth': only the following values are allowed: 'all', 'concept', 'collection'")

        keywords = _build_keywords(label)
        sparql = _build_sparql(self.getty, keywords, type_c, coll_id, coll_depth)

        try:
            #send request to getty
            r = requests.get(self.base_url + "sparql.json", params={"query": sparql}).json()
            #build answer
            answer = []
            for result in r["results"]["bindings"]:
                item = {'id': result["Id"]["value"],
                        'uri': result["Subject"]["value"],
                        'type': result["Type"]["value"],
                        'label': result["Term"]["value"]
                }
                answer.append(item)
            return answer
        except:
            return False

    def get_all(self):
        warnings.warn(
            'This provider does not support this. The amount of results is too large',
            UserWarning
        )
        return False

    def _get_top(self, type='All'):
        """ Returns all top-level facets. The returned values depend on the given type:
            Concept or All (Concepts and Collections). Default All is used.

        :param (str) type: Concepts or All (Concepts and Collections) top facets to return
        :return: A :class:`lst` of concepts (and collections). Each of these is a dict with the id and label keys
        """
        type_concepts = '{?Type rdfs:subClassOf skos:Concept}'
        type = type_concepts if type == "concepts" else type_concepts + ' UNION {?Type rdfs:subClassOf skos:Collection}'
        query = 'SELECT DISTINCT ?Id ?Term {?facet a gvp:Facet; rdf:type ?Type; dc:identifier ?Id; skos:inScheme %s:;.' \
                '%s optional {?facet gvp:prefLabelGVP [skosxl:literalForm ?Term]}}' \
                % (self.getty, type)
        # send request to getty
        r = requests.get(self.base_url + "sparql.json", params={"query": query}).json()
        # build answer
        answer = []
        for result in r["results"]["bindings"]:
            item = {
                'id': result["Id"]["value"],
                'label': {
                    'label': result["Term"]["value"],
                    'language': result["Term"]["xml:lang"] if "xml:lang" in result["Term"] else 'en',
                    'type': 'prefLabel'
                }
            }
            answer.append(item)
        return answer

    def get_top_concepts(self):
        """  Returns all concepts that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts. Each of these is a dict with the id and label keys.
        """
        return self._get_top("concepts")


    def get_top_display(self):
        """  Returns all concepts or collections that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts and collections. Each of these is a dict with the id and label keys.
        """
        return self._get_top()


class AATProvider(GettyProvider):
    """ The Art & Architecture Thesaurus Provider
    A provider that can work with the GETTY AAT rdf files of
    http://vocab.getty.edu/aat
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/aat
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', getty='aat')


class TGNProvider(GettyProvider):
    """ The Getty Thesaurus of Geographic Names
    A provider that can work with the GETTY GNT rdf files of
    http://vocab.getty.edu/tgn
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/tgn
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', getty='tgn')