# -*- coding: utf-8 -*-
'''
This module contains classes that implement 
:class:`skosprovider.providers.VocabularyProvider` against the LOD version of
the Getty Vocabularies (AAT, TGN and ULAN).

.. note::
    | At initialisation, the Getty providers will search which gvp-classes of the gvp-ontology are a subclass of skos-classes.
    | This can cause a time delay of several seconds at startup.

'''

import requests
import warnings
import logging

from language_tags import tags
from requests.exceptions import ConnectionError
from skosprovider.exceptions import ProviderUnavailableException
from skosprovider.providers import VocabularyProvider
from skosprovider_getty.utils import (
    uri_to_id, uri_to_graph, conceptscheme_from_uri, things_from_graph, get_subclasses)


class GettyProvider(VocabularyProvider):
    """A provider that can work with the GETTY rdf files of
    http://vocab.getty.edu/

    """

    def __init__(self, metadata, **kwargs):
        """ Constructor of the :class:`skosprovider_getty.providers.GettyProvider`

        :param (dict) metadata: metadata of the provider
        :param kwargs: arguments defining the provider.
            * Typical arguments are  `base_url`, `vocab_id` and `url`.
                The `url` is a composition of the `base_url` and `vocab_id`
            * The :class:`skosprovider_getty.providers.AATProvider`
                is the default :class:`skosprovider_getty.providers.GettyProvider`
        """
        if not 'default_language' in metadata:
            metadata['default_language'] = 'en'
        if 'base_url' in kwargs:
            self.base_url = kwargs['base_url']
        else:
            self.base_url = 'http://vocab.getty.edu/'
        if 'vocab_id' in kwargs:
            self.vocab_id = kwargs['vocab_id']
        else:
            self.vocab_id = 'aat'
        if not 'url' in kwargs:
            self.url = self.base_url + self.vocab_id
        else:
            self.url = kwargs['url']
        self.subclasses = get_subclasses()
        concept_scheme = conceptscheme_from_uri(self.url)
        super(GettyProvider, self).__init__(metadata, concept_scheme=concept_scheme, **kwargs)

    def _get_language(self, **kwargs):
        if 'language' in kwargs:
            return kwargs['language']
        return self.metadata['default_language']

    def get_by_id(self, id, change_notes=False):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by id

        :param (str) id: integer id of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """
        graph = uri_to_graph('%s/%s.rdf' % (self.url, id))
        if graph is False:
            return False
        # get the concept
        things = things_from_graph(graph, self.subclasses, self.concept_scheme)
        if len(things) == 0:
            return False
        c = things[0]
        return c


    def get_by_uri(self, uri, change_notes=False):
        """ Get a :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Collection` by uri

        :param (str) uri: string uri of the :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`
        :return: corresponding :class:`skosprovider.skos.Concept` or :class:`skosprovider.skos.Concept`.
            Returns None if non-existing id
        """

        id = uri_to_id(uri)

        return self.get_by_id(id, change_notes)

    def find(self, query, **kwargs):
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
        # #  interprete and validate query parameters (label, type and collection)
        # Label
        label = None
        if 'label' in query:
            label = query['label']
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
                    "collection - 'depth': only the following values are allowed: 'members', 'all'")

        #build sparql query
        coll_x = ""
        if coll_id is not None and coll_depth == 'all':
            coll_x = "gvp:broaderExtended " + self.vocab_id + ":" + coll_id + ";"
        elif coll_id is not None and coll_depth == 'members':
            coll_x = "gvp:broader " + self.vocab_id + ":" + coll_id + ";"


        type_values = "((?Type = skos:Concept) || (?Type = skos:Collection))"
        if type_c == 'concept':
            type_values = "(?Type = skos:Concept)"
        elif type_c == 'collection':
            type_values = "(?Type = skos:Collection)"
        query = """
            SELECT ?Subject ?Term ?Type ?Id (lang(?Term) as ?Lang) {
            ?Subject rdf:type ?Type; dc:identifier ?Id; %s  skos:inScheme %s:; %s.
                            OPTIONAL {
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term]}
                          }
            FILTER(%s)
            }""" % (self._build_keywords(label), self.vocab_id, coll_x, type_values)
        return self._get_answer(query, **kwargs)


    def get_all(self, **kwargs):
        """
        Not supported: This provider does not support this. The amount of results is too large
        """
        warnings.warn(
            'This provider does not support this. The amount of results is too large',
            UserWarning
        )
        return False

    def _get_answer(self, query, **kwargs):
        # send request to getty
        """ Returns the results of the Sparql query to a :class:`lst` of concepts and collections.
            The return :class:`lst`  can be empty.

        :param query (str): Sparql query
        :returns: A :class:`lst` of concepts and collections. Each of these
            is a dict with the following keys:
            * id: id within the conceptscheme
            * uri: :term:`uri` of the concept or collection
            * type: concept or collection
            * label: A label to represent the concept or collection.
        """
        request = self.base_url + "sparql.json"
        try:
            res = requests.get(request, params={"query": query})
        except ConnectionError as e:
            raise ProviderUnavailableException("Request could not be executed - Request: %s - Params: %s" % (request, query))
        if res.status_code == 404:
            raise ProviderUnavailableException("Service not found (status_code 404) - Request: %s - Params: %s" % (request, query))
        if not res.encoding:
            res.encoding = 'utf-8'
        r = res.json()
        d = {}
        for result in r["results"]["bindings"]:
            uri = result["Subject"]["value"]
            if "Term" in result:
                label = result["Term"]["value"]
            else:
                label = "<not available>"
            item = {
            'id': result["Id"]["value"],
            'uri': uri,
            'type': result["Type"]["value"].rsplit('#', 1)[1],
            'label': label,
            'lang': result["Lang"]["value"]
            }

            if uri not in d:
                d[uri] = item
            if tags.tag(d[uri]['lang']).format == tags.tag(self._get_language(**kwargs)).format:
                pass
            elif tags.tag(item['lang']).format == tags.tag(self._get_language(**kwargs)).format:
                d[uri] = item
            elif tags.tag(item['lang']).language and (tags.tag(item['lang']).language.format == tags.tag(self._get_language()).language.format):
                d[uri] = item
            elif tags.tag(item['lang']).format == tags.tag('en').format:
                d[uri] = item
        return list(d.values())


    def _get_top(self, type='All', **kwargs):
        """ Returns all top-level facets. The returned values depend on the given type:
            Concept or All (Concepts and Collections). Default All is used.

        :param (str) type: Concepts or All (Concepts and Collections) top facets to return
        :return: A :class:`lst` of concepts (and collections).
        """

        if type == "concepts" :
            type_values = "(?Type = skos:Concept)"
        else:
            type_values = "((?Type = skos:Concept) || (?Type = skos:Collection))"

        query = """SELECT ?Subject ?Id ?Type ?Term (lang(?Term) as ?Lang)
                {
                ?Subject a gvp:Facet; rdf:type ?Type;
                 dc:identifier ?Id; skos:inScheme %s:;.
                 OPTIONAL {
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term]}
                          }
                FILTER (%s)
                }""" % (self.vocab_id, type_values)
        return self._get_answer(query, **kwargs)

    def get_top_concepts(self, **kwargs):
        """  Returns all concepts that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts.
        """
        return self._get_top("concepts", **kwargs)


    def get_top_display(self, **kwargs):
        """  Returns all concepts or collections that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts and collections.
        """
        return self._get_top(**kwargs)

    def get_children_display(self, id, **kwargs):
        """ Return a list of concepts or collections that should be displayed under this concept or collection.

        :param str id: A concept or collection id.
        :returns: A :class:`lst` of concepts and collections.
        """
        broader = 'broader'
        type_values = "((?Type = skos:Concept) || (?Type = skos:Collection))"

        query = """SELECT ?Subject ?Id ?Type ?Term (lang(?Term) as ?Lang)
                {
                ?Subject rdf:type ?Type;
                dc:identifier ?Id; skos:inScheme %s:; gvp:%s %s:%s;.
                OPTIONAL {
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term]}
                          }
                FILTER(%s)
                }""" % (self.vocab_id, broader, self.vocab_id, id, type_values)

        return self._get_answer(query, **kwargs)

    def expand(self, id):
        """ Expand a concept or collection to all it's narrower concepts.
            If the id passed belongs to a :class:`skosprovider.skos.Concept`,
            the id of the concept itself should be include in the return value.

        :param str id: A concept or collection id.
        :returns: A :class:`lst` of id's. Returns false if the input id does not exists
        """

        query = """SELECT DISTINCT ?Id{
                {
                ?Subject dc:identifier ?Id; skos:inScheme %s:; gvp:broaderExtended %s;.
                }
                UNION
                {
                VALUES ?Id {'%s'}
                ?Subject dc:identifier ?Id; skos:inScheme %s:; rdf:type skos:Concept.
                }
                }
                """ % (self.vocab_id, self.vocab_id + ":" + id, id, self.vocab_id)

        print (query)
        res = requests.get(self.base_url + "sparql.json", params={"query": query})
        res.encoding = 'utf-8'
        r = res.json()

        result = [result['Id']['value'] for result in r['results']['bindings']]
        if len(result) == 0 and self.get_by_id(id) is False:
            return False
        return result

    # def _get_language_filter(self):
    #     return "(lang(?Term)='en' || lang(?Term)='" + self._get_language() + "')"

    def _build_keywords(self, label):
            if label is None:
                return ""
            keyword_list = label.split(" ")
            keywords = ""
            for idx, item in enumerate(keyword_list):
                if idx + 1 == len(keyword_list):
                    keywords = keywords + item
                else:
                    keywords = keywords + item + " AND "

            return "luc:term '" + keywords + "';"


class AATProvider(GettyProvider):
    """ The Art & Architecture Thesaurus Provider
    A provider that can work with the GETTY AAT rdf files of
    http://vocab.getty.edu/aat
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/aat
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', vocab_id='aat')


class TGNProvider(GettyProvider):
    """ The Getty Thesaurus of Geographic Names
    A provider that can work with the GETTY TGN rdf files of
    http://vocab.getty.edu/tgn
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/tgn
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', vocab_id='tgn')


class ULANProvider(GettyProvider):
    """ Union List of Artist Names

    A provider that can work with the GETTY ULAN rdf files of
    http://vocab.getty.edu/ulan
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/ulan
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', vocab_id='ulan')
