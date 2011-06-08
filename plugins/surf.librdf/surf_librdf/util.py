import RDF
import rdflib

def librdf_to_rdflib(obj):
    if obj is None:
        return
    elif obj.is_resource():
        return rdflib.URIRef(unicode(obj.uri))
    elif obj.is_literal():
        return rdflib.Literal(obj.literal_value['string'],
                              datatype=obj.literal_value['datatype'],
                              lang=obj.literal_value['language'])
    elif obj.is_blank():
        return rdflib.BNode(obj.blank_identifier)

def rdflib_to_librdf(obj):
    if obj is None:
        return
    elif type(obj) == rdflib.URIRef:
        return RDF.Node(uri_string=unicode(obj).encode('utf8'))
    elif type(obj) == rdflib.Literal:
        if obj.datatype:
            datatype = RDF.Uri(unicode(obj.datatype).encode('utf8'))
            return RDF.Node(literal=unicode(obj),
                            datatype=datatype,
                            language=obj.language)
        else:
            return RDF.Node(literal=unicode(obj),
                            language=obj.language)
    elif type(obj) == rdflib.BNode:
        return rdflib.BNode(blank=unicode(obj))
