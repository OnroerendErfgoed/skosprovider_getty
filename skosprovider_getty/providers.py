#!/usr/bin/python
# -*- coding: utf-8 -*-
import rdflib
import requests
import warnings
import logging
from skosprovider.providers import VocabularyProvider
from skosprovider_getty.utils import (
    getty_to_skos,
    uri_to_id
)

log = logging.getLogger(__name__)


def _build_keywords(label):
    keyword_list = label.split(" ")
    keywords = ""
    for idx, item in enumerate(keyword_list):
        if idx + 1 == len(keyword_list):
            keywords = keywords + item
        else:
            keywords = keywords + item + " AND "

    return "'" + keywords + "'"

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
        if 'vocab_id' in kwargs:
            self.vocab_id = kwargs['vocab_id']
        else:
            self.vocab_id = 'aat'
        if not 'url' in kwargs:
            self.url = self.base_url + self.vocab_id
        else:
            self.url = kwargs['url']

        super(GettyProvider, self).__init__(metadata, **kwargs)

    def _get_language(self, **kwargs):
        return self.metadata['default_language']

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
                    return False
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

        #build sparql query
        coll_x = ""
        if coll_id is not None and coll_depth == 'all':
            coll_x = "gvp:broaderExtended " + self.vocab_id + ":" + coll_id
        elif coll_id is not None and coll_depth == 'members':
            coll_x = "gvp:broader " + self.vocab_id + ":" + coll_id


        type_values = "(skos:Concept) (skos:Collection)"
        if type_c == 'concept':
            type_values = "(skos:Concept)"
        elif type_c == 'collection':
            type_values = "(skos:Collection)"
        query = """
            SELECT ?Subject ?Term ?Type ?Id ?Lang {
            VALUES (?Type) {%s}
            ?Subject rdf:type ?Type; dc:identifier ?Id; luc:term %s; skos:inScheme %s:; %s;.
                            OPTIONAL {
                            VALUES ?Lang {gvp_lang:en gvp_lang:nl}
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term; dcterms:language ?Lang]}
                          }
            }""" % (type_values, _build_keywords(label), self.vocab_id, coll_x)
        print(query)
        try:
            return self._get_answer(query)
        except:
            return False

    def get_all(self):
        warnings.warn(
            'This provider does not support this. The amount of results is too large',
            UserWarning
        )
        return False

    def _get_answer(self, query):
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
        res = requests.get(self.base_url + "sparql.json", params={"query": query})
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
            'label': label
            }
            if uri not in d or self._get_language() == uri_to_id(result["Lang"]["value"]):
                d[uri] = item
        return list(d.values())

    def _get_top(self, type='All'):
        """ Returns all top-level facets. The returned values depend on the given type:
            Concept or All (Concepts and Collections). Default All is used.

        :param (str) type: Concepts or All (Concepts and Collections) top facets to return
        :return: A :class:`lst` of concepts (and collections).
        """

        if type == "concepts" :
            type_values = "(skos:Concept)"
        else:
            type_values = "(skos:Concept) (skos:Collection)"

        query = """SELECT ?Subject ?Id ?Type ?Term ?Lang
                {
                 VALUES (?Type) {%s}
                ?Subject a gvp:Facet; rdf:type ?Type;
                 dc:identifier ?Id; skos:inScheme %s:;.
                 OPTIONAL {
                 VALUES ?Lang {gvp_lang:en gvp_lang:nl}
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term; dcterms:language ?Lang]}
                          }}""" % (type_values, self.vocab_id)
        print(query)
        return self._get_answer(query)

    def get_top_concepts(self):
        """  Returns all concepts that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts.
        """
        return self._get_top("concepts")


    def get_top_display(self):
        """  Returns all concepts or collections that form the top-level of a display hierarchy.

        :return: A :class:`lst` of concepts and collections.
        """
        return self._get_top()

    def _get_children(self, id, extended=False):

        broader = 'broaderExtended' if extended else 'broader'

        query = """SELECT ?Subject ?Id ?Type ?Term ?Lang
                {
                VALUES (?Type) {(skos:Concept) (skos:Collection)}
                ?Subject rdf:type ?Type;
                dc:identifier ?Id; skos:inScheme %s:; gvp:%s %s:%s;.
                OPTIONAL {
                VALUES ?Lang {gvp_lang:en gvp_lang:nl}
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term; dcterms:language ?Lang]}
                          }
                }""" % (self.vocab_id, broader, self.vocab_id, id)

        return self._get_answer(query)

    def get_children_display(self, id):
        """ Return a list of concepts or collections that should be displayed under this concept or collection.

        :param str id: A concept or collection id.
        :returns: A :class:`lst` of concepts and collections.
        """
        return self._get_children(id)

    def expand(self, id):
        """ Expand a concept or collection to all it's narrower concepts.
            If the id passed belongs to a :class:`skosprovider.skos.Concept`,
            the id of the concept itself should be include in the return value.

        :param str id: A concept or collection id.
        :returns: A :class:`lst` of concepts and collections. Returns false if the input id does not exists
        """
        query = """SELECT ?Subject ?Id ?Type ?Term ?Lang
                {VALUES (?Subject) {(%s)}
                VALUES (?Type) {(skos:Concept) (skos:Collection)}
                ?Subject rdf:type ?Type; dc:identifier ?Id; skos:inScheme %s:;
                OPTIONAL {
                VALUES ?Lang {gvp_lang:en gvp_lang:nl}
                  {?Subject xl:prefLabel [skosxl:literalForm ?Term; dcterms:language ?Lang]}
                          }
                }""" % (self.vocab_id + ":" + id, self.vocab_id)
        print(query)
        concept = self._get_answer(query)
        answer = []
        if len(concept) == 0:
            return False
        if concept[0]['type'] == 'Concept':
            answer += concept
        return answer + self._get_children(id, extended=True)


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
    A provider that can work with the GETTY GNT rdf files of
    http://vocab.getty.edu/tgn
    """

    def __init__(self, metadata):
        """ Inherit functions of the getty provider using url http://vocab.getty.edu/tgn
        """
        GettyProvider.__init__(self, metadata, base_url='http://vocab.getty.edu/', vocab_id='tgn')
