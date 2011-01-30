# Parts Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.

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

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ''AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

""" Module for ResultProxy. """

from surf.exc import NoResultFound, MultipleResultsFound
from surf.rdf import Literal, URIRef
from surf.util import attr2rdf, value_to_rdf

class ResultProxy(object):
    """ Interface to :meth:`surf.store.Store.get_by`.

    ResultProxy collects filtering parameters. When iterated, it executes
    :meth:`surf.store.Store.get_by` with collected parameters and yields results.

    ResultProxy doesn't know how to convert data returned by
    :meth:`surf.store.Store.get_by` into :class:`surf.resource.Resource`, `URIRef`
    and `Literal` objects. It delegates this task to `instancemaker`
    function.

    """

    def __init__(self, params={}, store=None, instancemaker=None):
        self.__params = params
        self.__get_by_response = None

        if store:
            self.__params["store"] = store

        if instancemaker:
            self.__params["instancemaker"] = instancemaker

    def instancemaker(self, instancemaker_function):
        """ Specify the function for converting triples into instances.

        ``instancemaker_function`` function can also be specified
        as argument to constructor when instantiating :class:`ResultProxy`.

        ``instancemaker_function`` will be executed whenever
        :class:`ResultProxy` needs to return a resource. It has to accept two
        arguments: ``params`` and ``instance_data``.

        ``params`` will be a dictionary containing query parameters gathered
        by :class:`ResultProxy`. Information from ``params`` can be used
        by ``instancemaker_function``, for example, to decide what
        context should be set for created instances.

        ``instance_data`` will be a dictionary containing keys `direct` and
        `inverse`. These keys map to dictionaries describing direct and
        inverse attributes respectively.

        """

        params = self.__params.copy()
        params["instancemaker"] = instancemaker_function
        return ResultProxy(params)

    def limit(self, value):
        """ Set the limit for returned result count. """
        if "high" in self.__params or "low" in self.__params:
            raise ValueError(
                    "Cannot combine slicing with limit & offset")

        params = self.__params.copy()
        params["limit"] = value
        return ResultProxy(params)

    def offset(self, value):
        """ Set the limit for returned results. """
        if "high" in self.__params or "low" in self.__params:
            raise ValueError(
                    "Cannot combine slicing with limit & offset")

        params = self.__params.copy()
        params["offset"] = value
        return ResultProxy(params)

    def full(self, only_direct=False):
        """ Enable eager-loading of resource attributes.

        If ``full`` is set to `True`, returned resources will have attributes
        already loaded.

        Whether setting this will bring performance
        improvements depends on reader plugin implementation.
        For example, sparql_protocol plugin is capable of using SPARQL
        subqueries to fully load multiple resources in one request.

         """

        params = self.__params.copy()
        params["full"] = True
        params["only_direct"] = only_direct
        return ResultProxy(params)

    def order(self, value=True):
        """ Request results to be ordered.

        If no arguments are specified, resources will be ordered by their
        subject URIs.

        If ``value`` is set to an URIRef, corresponding attribute will be
        used for sorting. For example, sorting persons by surname::

            FoafPerson = session.get_class(surf.ns.FOAF.Person)
            for person in FoafPerson.all().order(surf.ns.FOAF.surname):
                print person.foaf_name.first, person.foaf_surname.first

        Currently only one sorting key is supported.

        """

        params = self.__params.copy()
        if type(value) in [str, unicode]:
            value = self.__split_attribute_edges(value)
        elif isinstance(value, URIRef):
            value = [(value, True)]
        elif type(value) != bool:
            raise TypeError("Invalid type specified %r" % type(value))

        params["order"] = value
        return ResultProxy(params)

    def desc(self):
        """ Set sorting order to descending. """

        params = self.__params.copy()
        params["desc"] = True
        return ResultProxy(params)

    def __split_attribute_edges(self, name):
        """ Allow specifying indirect attributes by giving a path of properties
        from the object up to the requested attribute """
        edges = []
        for edge in name.split('__'):
            attr, direct = attr2rdf(edge)
            if attr is None:
                raise ValueError("Not an attribute %r" % edge)
            edges.append((attr, direct))

        return edges

    def get_by(self, **kwargs):
        """ Add filter conditions.

        Arguments are expected in form::

            foaf_name = "John"

        Multiple arguments are supported.
        An example that retrieves all persons named "John Smith"::

            FoafPerson = session.get_class(surf.ns.FOAF.Person)
            for person in FoafPerson.get_by(foaf_name = "John", foaf_surname = "Smith"):
                print person.subject

        """

        params = self.__params.copy()
        # Don't overwrite existing get_by parameters, just append new ones.
        # Overwriting get_by params would cause resource.some_attr.get_by()
        # to work incorrectly.
        params.setdefault("get_by", [])
        for name, value in kwargs.items():
            edges = self.__split_attribute_edges(name)

            if hasattr(value, "subject"):
                # If value has subject attribute, this must be Resource, 
                # take its subject.
                value = value.subject
            elif hasattr(value, "__iter__"):
                value = map(value_to_rdf, value)
            else:
                value = value_to_rdf(value)

            params["get_by"].append((edges, value))
        return ResultProxy(params)

    def filter(self, **kwargs):
        """ Add filter conditions.

        Expects arguments in form::

            ns_predicate = "(%s > 15)"

        ``ns_predicate`` specifies which predicate will be used for
        filtering, a query variable will be bound to it. `%s` is a placeholder
        for this variable.

        Filter expression (in example: "(%s > 15)") must follow SPARQL
        specification, on execution "%s" will be substituted with variable
        and the resulting string will be placed in query as-is. Because of
        string substitution percent signs need to be escaped. For example::

            Person.all().filter(foaf_name = "(%s LIKE 'J%%')")

        This Virtuoso-specific filter is intended to select persons with names starting with
        "J". In generated query it will look like this::

            ...
            ?s <http://xmlns.com/foaf/0.1/name> ?f1 .
            FILTER (?f1 LIKE 'J%')
            ...

        """

        params = self.__params.copy()
        params.setdefault("filter", [])
        for name, value in kwargs.items():
            attr, direct = attr2rdf(name)
            assert direct, "Only direct attributes can be used for filters"
            # Assume by plain strings user means literals
            if type(value) in [str, unicode]:
                value = Literal(value)
            params["filter"].append((attr, value, direct))
        return ResultProxy(params)

    def context(self, context):
        """ Specify context/graph that resources should be loaded from. """

        params = self.__params.copy()
        params["context"] = context
        return ResultProxy(params)

    def __execute_get_by(self):
        if self.__get_by_response is None:
            self.__get_by_args = {}

            if "high" in self.__params:
                self.__get_by_args["limit"] = (self.__params["high"]
                                               - self.__params.get("low", 0))
            if "low" in self.__params:
                self.__get_by_args["offset"] = self.__params["low"]

            for key in ["limit", "offset", "full", "order", "desc", "get_by",
                        "only_direct", "context", "filter"]:
                if key in self.__params:
                    self.__get_by_args[key] = self.__params[key]

            store = self.__params["store"]
            self.__get_by_response = store.get_by(self.__get_by_args)

        return self.__get_by_args, self.__get_by_response

    def __iterator(self):
        get_by_args, get_by_response = self.__execute_get_by()

        instancemaker = self.__params["instancemaker"]
        for instance_data in get_by_response:
            yield instancemaker(get_by_args, instance_data)


    def __iter__(self):
        """ Return iterator over resources in this collection. """

        return self.__iterator()

    def __len__(self):
        """ Return count of resources in this collection. """

        _, get_by_response = self.__execute_get_by()
        return len(get_by_response)

    def __getitem__(self, item):
        """ Retrieves an item or slice from resources in this collection. """
        if not isinstance(item, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(item, slice) and (item >= 0))
                or (isinstance(item, slice)
                    and (item.start is None or item.start >= 0)
                    and (item.stop is None or item.stop >= 0))), \
                "Negative indexing is not supported."

        # If the query has already been executed generate from results
        if self.__get_by_response is not None:
            get_by_args, get_by_response = self.__execute_get_by()

            instancemaker = self.__params["instancemaker"]
            if isinstance(item, slice):
                l = []
                for instance_data in get_by_response[item]:
                    l.append(instancemaker(get_by_args, instance_data))

                return l
            else:
                return instancemaker(get_by_args, get_by_response[item])

        # Build new query
        if isinstance(item, slice):
            start = stop = None
            if item.start is not None:
                start = int(item.start)
            if item.stop is not None:
                stop = int(item.stop)

            params = self.__params.copy()
            self.__set_limits(params, start, stop)
            rp = ResultProxy(params)

            if item.step is not None:
                return list(rp)[::item.step]
            else:
                return rp
        else:
            # Raise IndexError if result list empty
            params = self.__params.copy()
            self.__set_limits(params, item, item + 1)
            return list(ResultProxy(params))[0]

    @staticmethod
    def __set_limits(params, low, high):
        """ Adjusts offset and limit. These are applied relative to existing
        values.
        """
        if "offset" in params or "limit" in params:
            raise ValueError(
                    "Cannot combine slicing with limit & offset")

        if high is not None:
            if "high" in params:
                params["high"] = min(params["high"],
                                     params.get("low", 0) + high)
            else:
                params["high"] = params.get("low", 0) + high

        if low is not None:
            if "high" in params:
                params["low"] = min(params["high"],
                                    params.get("low", 0) + low)
            else:
                params["low"] = params.get("low", 0) + low

    def first(self):
        """ Return first resource or None if there aren't any. """

        item = None
        try:
            item = iter(self).next()
        except StopIteration:
            pass

        return item

    def one(self):
        """ Return the only resource or raise if resource count != 1. 
        
        If the query matches no resources, this method will raise
        :class:`surf.exc.NoResultFound` exception. If the query matches 
        more than one resource, this method will raise
        :class:`surf.exc.MultipleResultsFound` exception. 
        
        """

        iterator = iter(self)
        try:
            item = iterator.next()
        except StopIteration:
            raise NoResultFound("List is empty")

        try:
            iterator.next()
        except StopIteration:
            # As expected, return item
            return item

        raise MultipleResultsFound("List has more than one item")
