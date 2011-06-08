# -*- coding: utf-8 -*-
__author__ = 'Christoph Burgmer'

import warnings

from surf.plugin.writer import RDFWriter
from reader import ReaderPlugin
from surf_librdf.util import rdflib_to_librdf
from RDF import Model, MemoryStorage, Statement

class WriterPlugin(RDFWriter):
    def __init__(self, reader, *args, **kwargs):
        RDFWriter.__init__(self, reader, *args, **kwargs)
        if isinstance(self.reader, ReaderPlugin):
            self.__librdf_model = self.reader.librdf_model
        else:
            self.__librdf_model = Model(MemoryStorage(options_string="contexts='yes'"))

            warnings.warn("Graph is not readable through the reader plugin", 
                          UserWarning)

    librdf_model = property(lambda self: self.__librdf_model)

    def _save(self, *resources):
        for resource in resources:
            s = resource.subject
            self.__remove(s)
            for p, objs in resource.rdf_direct.items():
                for o in objs:
                    self.__add(s, p, o, resource.context)

    def _update(self, *resources):
        for resource in resources:
            s = resource.subject
            for p in resource.rdf_direct:
                self.__remove(s, p)
            for p, objs in resource.rdf_direct.items():
                for o in objs:
                    self.__add(s, p, o, resource.context)

    def _remove(self, *resources, **kwargs):
        inverse = kwargs.get("inverse")
        for resource in resources:
            self.__remove(s=resource.subject, context=resource.context)
            if inverse:
                self.__remove(o=resource.subject, context=resource.context)

    def _size(self):
        return self.__librdf_model.size()

    def _add_triple(self, s = None, p = None, o = None, context = None):
        self.__add(s, p, o, context)

    def _set_triple(self, s = None, p = None, o = None, context = None):
        self.__remove(s, p, context = context)
        self.__add(s, p, o, context)

    def _remove_triple(self, s = None, p = None, o = None, context = None):
        self.__remove(s, p, o, context)

    def __add(self, s = None, p = None, o = None, context = None):
        self.log.info('ADD: %s, %s, %s, %s' % (s, p, o, context))
        statement = Statement(*map(rdflib_to_librdf, [s, p, o]))
        self.__librdf_model.append(statement, rdflib_to_librdf(context))

    def __remove(self, s = None, p = None, o = None, context = None):
        self.log.info('REM: %s, %s, %s, %s' % (s, p, o, context))
        statement = Statement(*map(rdflib_to_librdf, [s, p, o]))
        context = rdflib_to_librdf(context)
        if s is None or p is None or o is None:
            statements = list(self.__librdf_model.find_statements(statement, context))
        else:
            statements = [statement]
        
        for statement in statements:
            if context:
                del self.__librdf_model[statement, context]
            else:
                del self.__librdf_model[statement]

    def index_triples(self, **kwargs):
        """ Index triples if this functionality is present.  
        
        Return `True` if successful.
        
        """
        return False

    def load_triples(self, source=None, **args):
        """ Load files (or resources on the web) into the triple-store. """
        
        if source:
            # TODO more formats
            self.__librdf_model.load(source)
            return True
        
        return False

    def _clear(self, context=None):
        """ Clear the triple-store. """

        # TODO Does this only remove context less triples?
        self.__remove((None, None, None), context)

    def close(self):
        self.__librdf_model.sync()
