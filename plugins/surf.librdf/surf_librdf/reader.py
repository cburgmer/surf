# -*- coding: utf-8 -*-
__author__ = 'Christoph Burgmer'

from surf.plugin.query_reader import RDFQueryReader
from surf_librdf.util import librdf_to_rdflib
from RDF import Model, MemoryStorage, SPARQLQuery


class ReaderPlugin(RDFQueryReader):
    def __init__(self, *args, **kwargs):
        RDFQueryReader.__init__(self, *args, **kwargs)

        self.__librdf_model = Model(MemoryStorage(options_string="contexts='yes'"))

    librdf_model = property(lambda self: self.__librdf_model)

    def _to_table(self, result):
        def convert((key, value)):
            return (key, librdf_to_rdflib(value))
        
        # Convert librdf types to rdflib
        return [dict(map(convert, row.items())) for row in result]

    def _ask(self, result):
        assert result.is_boolean()
        return result.get_boolean()

    # execute
    def _execute(self, query):
        q_string = unicode(query)
        self.log.debug(q_string)
        q = SPARQLQuery(q_string.encode('utf8'))
        return q.execute(self.__librdf_model)

    #def execute_sparql(self, q_string, format = None):
        #self.log.debug(q_string)

        #q = SPARQLQuery(q_string)
        #result = q.execute(self.__librdf_model)
        #return loads(result.serialize('json'))

    def close(self):
        self.__librdf_model.sync()

