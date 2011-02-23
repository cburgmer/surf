# Copyright (c) 2009, Digital Enterprise Research Institute (DERI),
# NUI Galway
# All rights reserved.

# author: Cosmin Basca
# email: cosmin.basca@gmail.com

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer
#      in the documentation and/or other materials provided with
#      the distribution.
#    * Neither the name of DERI nor the
#      names of its contributors may be used to endorse or promote
#      products derived from this software without specific prior
#      written permission.

# THIS SOFTWARE IS PROVIDED BY DERI ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DERI BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

# -*- coding: utf-8 -*-
__author__ = 'Cosmin Basca'

from surf.plugin.reader import RDFReader
from surf.query import Query, Union, Group
from surf.query import a, ask, select, optional_group, named_group
from surf.resource.util import Q
from surf.rdf import URIRef

def query_SP(s, p, direct, contexts):
    """ Construct :class:`surf.query.Query` with `?v` and `?g`, `?c` as
    unknowns. """

    s, v = direct and (s, '?v') or ('?v', s)
    query = select('?v', '?c', '?g').distinct()
    query.where((s, p, v)).optional_group(('?v', a, '?c'))\
                          .optional_group(named_group('?g', ('?v', a, '?c')))
    if contexts:
        query.from_(*contexts)
        query.from_named(*contexts)

    return query

def query_S(s, direct, contexts):
    """ Construct :class:`surf.query.Query` with `?p`, `?v` and `?g`, `?c` as
    unknowns. """
    s, v = direct and (s, '?v') or ('?v', s)
    query = select('?p', '?v', '?c', '?g').distinct()
    # Get predicate, objects and optionally rdf:type & named graph of
    # subject rdf:type and object rdf:type
    # TODO fails under Virtuoso as V. doesn't allow ?g to be bound to two
    # optional matches
    query.where((s, '?p', v)).optional_group(('?v', a, '?c'))\
                             .optional_group(named_group('?g', (s, a, v)))\
                             .optional_group(named_group('?g', ('?v', a, '?c')))
    if contexts:
        query.from_(*contexts)
        query.from_named(*contexts)

    return query

def query_Ask(subject, contexts):
    """ Construct :class:`surf.query.Query` of type **ASK**. """

    query = ask().where((subject, '?p', '?o'))

    if contexts:
        query.from_(*contexts)
        query.from_named(*contexts)

    return query

#Resource class level
def query_P_S(c, p, direct, context):
    """ Construct :class:`surf.query.Query` with `?s` and `?g`, `?c` as
    unknowns. """

    query = select('?s', '?c', '?g').distinct()
    if context:
        query.from_(context)
        query.from_named(context)

    for i in range(len(p)):
        s, v = direct and  ('?s', '?v%d' % i) or ('?v%d' % i, '?s')
        if type(p[i]) is URIRef:
            query.where((s, p[i], v))

    query.optional_group(('?s', a, '?c'))
    query.optional_group(named_group('?g', ('?s', a, '?c')))

    return query

def query_Concept(subject):
    """ Construct :class:`surf.query.Query` with `?c` as the unknown. """

    return select('?c').distinct().where((subject, a, '?c'))

class RDFQueryReader(RDFReader):
    """ Super class for SuRF Reader plugins that wrap queryable `stores`. """

    def __init__(self, *args, **kwargs):
        RDFReader.__init__(self, *args, **kwargs)
        self.use_subqueries = kwargs.get('use_subqueries', False)
        if type(self.use_subqueries) in [str, tuple]:
            self.use_subqueries = (self.use_subqueries.lower() == 'true')
        elif type(self.use_subqueries) is not bool:
            raise ValueError('The use_subqueries parameter must be a bool or a string set to "true" or "false"')

    #protected interface
    def _get(self, subject, attribute, direct, query_contexts):
        query = query_SP(subject, attribute, direct, query_contexts)
        result = self._execute(query)
        return self.convert(result, 'v', 'g', 'c')

    def _load(self, subject, direct, query_contexts):
        query = query_S(subject, direct, query_contexts)
        result = self._execute(query)
        return self.convert(result, 'p', 'v', 'g', 'c')

    def _is_present(self, subject, query_contexts):
        query = query_Ask(subject, query_contexts)
        result = self._execute(query)
        return self._ask(result)

    def _concept(self, subject):
        query = query_Concept(subject)
        result = self._execute(query)
        return self.convert(result, 'c')

    def _instances_by_attribute(self, concept, attributes, direct, context):
        query = query_P_S(concept, attributes, direct, context)
        result = self._execute(query)
        return self.convert(result, 's', 'g', 'c')

    @classmethod
    def __edge_iterator(cls, edge='e'):
        edge_idx = 0
        while True:
            yield '?' + edge + str(edge_idx)
            edge_idx += 1

    @classmethod
    def __build_attribute_clause(cls, (edges, values), edge_iterator):
        def order_terms(a, b, c, direct):
            if direct:
                return (a, b, c)
            else:
                return (c, b, a)

        last_edge = "?s"
        clauses = []

        # Build path to attribute, value pair
        for attribute, direct in edges[:-1]:
            edge_variable = edge_iterator.next()

            clauses.append(order_terms(last_edge,
                                       attribute,
                                       edge_variable,
                                       direct))
            last_edge = edge_variable

        # Attach value query to path
        attribute, direct = edges[-1]
        if hasattr(values, "__iter__"):
            union_clause = Union()
            for value in values:
                union_clause.append(order_terms(last_edge,
                                                attribute,
                                                value,
                                                direct))
            clauses.append(union_clause)
        else:
            clauses.append(order_terms(last_edge,
                                       attribute,
                                       values,
                                       direct))
        return clauses

    @classmethod
    def __build_where_clause(cls, q_obj, edge_iterator):
        clauses = []
        for child in q_obj.children:
            if isinstance(child, Q):
                subclauses = cls.__build_where_clause(child, edge_iterator)
                connection = child.connection
            else:
                subclauses = cls.__build_attribute_clause(child, edge_iterator)
                connection = Q.AND

            if len(subclauses) > 1:
                if connection == Q.AND:
                    clause = Group(subclauses)
                elif connection == Q.OR:
                    clause = Union(subclauses)
            else:
                clause = subclauses[0]

            clauses.append(clause)

        return clauses

    def __apply_limit_offset_order_get_by_filter(self, params, query):
        """ Apply limit, offset, order parameters to query. """
        def order_terms(a, b, c, direct):
            if direct:
                return (a, b, c)
            else:
                return (c, b, a)


        if "limit" in params:
            query.limit(params["limit"])

        if "offset" in params:
            query.offset(params["offset"])

        if "get_by" in params:
            edges = self.__edge_iterator()
            clauses = self.__build_where_clause(params["get_by"], edges)

            if params["get_by"].connection == Q.OR:
                query.where(Union(clauses))
            else:
                query.where(*clauses)

        if "filter" in params:
            filter_idx = 0
            for attribute, value, direct  in params["filter"]:
                filter_idx += 1
                filter_variable = "?f%d" % filter_idx
                query.where(("?s", attribute, filter_variable))
                query.filter(value % filter_variable)

        if "order" in params:
            if params["order"] == True:
                # Order by subject URI
                if "desc" in params and params["desc"]:
                    query.order_by("DESC(?s)")
                else:
                    query.order_by("?s")
            elif params["order"] != False:
                # Match another variable, order by it
                edges = params["order"]
                edge_idx = 0
                last_edge = "?s"
                where_clauses = []

                # Build path to attribute, value pair for which we sort
                for attribute, direct in edges:
                    edge_idx += 1
                    edge_variable = "?o%d" % edge_idx

                    where_clauses.append(order_terms(last_edge,
                                                     attribute,
                                                     edge_variable,
                                                     direct))
                    last_edge = edge_variable

                query.optional_group(*where_clauses)
                if "desc" in params and params["desc"]:
                    query.order_by("DESC(%s)" % last_edge)
                else:
                    query.order_by(last_edge)

        return query

    def _get_by(self, params):
        # Decide which loading strategy to use
        if "full" in params:
            if self.use_subqueries:
                return self.__get_by_subquery(params)
            else:
                return self.__get_by_n_queries(params)

        # No details, just subjects and classes
        query = select("?s", "?c", "?g")
        self.__apply_limit_offset_order_get_by_filter(params, query)
        query.optional_group(("?s", a, "?c"))
        # Query for the same tuple to get the named graph if obtainable
        query.optional_group(named_group("?g", ("?s", a, "?c")))

        contexts = params.get("contexts", None)
        if contexts:
            query.from_(*contexts)
            query.from_named(*contexts)

        # Load just subjects and their types
        table = self._to_table(self._execute(query))

        # Create response structure, preserve order, don't include
        # duplicate subjects if some subject has multiple types
        subjects = {}
        results = []
        for match in table:
            subject = match["s"]
            if not subject in subjects:
                instance_data = {"direct" : {a : {}}}
                subjects[subject] = instance_data
                results.append((subject, instance_data))

            # "context" comes from an optional group and is missing if the
            # triple is stored in the unamed graph
            context = match.get("g")

            if "c" in match:
                concept = match["c"]
                subjects[subject]["direct"][a][concept] = {context: []}

        return results

    def __get_by_n_queries(self, params):
        contexts = params.get("contexts", None)

        query = select("?s")
        if contexts:
            query.from_(*contexts)
            query.from_named(*contexts)

        self.__apply_limit_offset_order_get_by_filter(params, query)

        # Load details, for now the simplest approach with N queries.
        # Use _to_table instead of convert to preserve order.
        results = []
        for match in self._to_table(self._execute(query)):
            subject = match["s"]
            instance_data = {}

            result = self._execute(query_S(subject, True, contexts))
            result = self.convert(result, 'p', 'v', 'g', 'c')
            instance_data["direct"] = result

            if not params.get("only_direct"):
                result = self._execute(query_S(subject, False, contexts))
                result = self.convert(result, 'p', 'v', 'g', 'c')
                instance_data["inverse"] = result

            results.append((subject, instance_data))

        return results

    def __get_by_subquery(self, params):
        contexts = params.get("contexts", None)

        inner_query = select("?s")
        inner_params = params.copy()
        if "order" in params:
            # "order" needs to stay in subquery,
            # but doesn't do anything useful in main query
            del params["order"]
        self.__apply_limit_offset_order_get_by_filter(inner_params, inner_query)


        query = select("?s", "?p", "?v", "?c", "?g").distinct()
        # Get values with object type & context
        # TODO we need to query both contexts, from ?s -> rdf_type & ?v -> rdf_type but Virtuoso does not bind ?g twice. Bug or feature?
        query.group(('?s', '?p', '?v'),
                    optional_group(('?v', a, '?c')),
                    optional_group(named_group("?g", ("?s", a, "?v"))))
                    #optional_group(named_group("?g", ("?v", a, "?c"))))
        query.where(inner_query)
        if contexts:
            query.from_(*contexts)
            query.from_named(*contexts)

        # Need ordering in outer query
        if "order" in params:
            if params["order"] == True:
                # Order by subject URI
                query.order_by("?s")
            else:
                # Match another variable, order by it
                query.optional_group(("?s", params["order"], "?order"))
                query.order_by("?order")

        table = self._to_table(self._execute(query))
        subjects = {}
        results = []
        for match in table:
            # Make sure subject and predicate are URIs (they have to be!),
            # this works around bug in Virtuoso -- it sometimes returns
            # URIs as Literals.
            subject = URIRef(match["s"])
            predicate = URIRef(match["p"])
            value = match["v"]

            # Add subject to result list if it's not there
            if not subject in subjects:
                instance_data = {"direct" : {}}
                subjects[subject] = instance_data
                results.append((subject, instance_data))

            # Add predicate to subject's direct predicates if it's not there
            direct_attributes = subjects[subject]["direct"]
            if not predicate in direct_attributes:
                direct_attributes[predicate] = {}

            # "context" comes from an optional group and is missing if the
            # triple is stored in the unamed graph
            context = match.get("g")

            # Add value to subject->predicate if ...
            predicate_values = direct_attributes[predicate]
            if not value in predicate_values:
                predicate_values[value] = {context: []}

            # Add RDF type of the value to subject->predicate->value list
            if "c" in match:
                predicate_values[value][context].append(match["c"])

        return results

    # to implement
    def _ask(self, result):
        """ Return boolean value of an **ASK** query. """

        return False

    # execute
    def _execute(self, query):
        """ To be implemented by classes the inherit from `RDFQueryReader`.

        This method is called internally by :meth:`execute`.

        """

        return None

    def _to_table(self, result):
        return []

    def __convert(self, query_result, *keys):
        results_table = self._to_table(query_result)

        if len(keys) == 1:
            return [row[keys[0]] for row in results_table]

        last = len(keys) - 2
        results = {}
        for row in results_table:
            data = results
            for i in range(len(keys) - 1):
                k = keys[i]
                v = row.get(k)
                if i < last:
                    if v not in data:
                        data[v] = {}
                    data = data[v]
                elif i == last:
                    if v not in data:
                        data[v] = []

                    value = row.get(keys[i + 1])
                    if value:
                        data[v].append(value)

        return results

    # public interface
    def execute(self, query):
        """ Execute a `query` of type :class:`surf.query.Query`. """

        if isinstance(query, Query):
            return self._execute(query)

        return None

    def convert(self, query_result, * keys):
        """ Convert the results from the query to a multilevel dictionary.

        This method is used by the :class:`surf.resource.Resource` class.

        """

        try:
            return self.__convert(query_result, *keys)
        except Exception, e:
            self.log.exception("Error on convert")
        return []
