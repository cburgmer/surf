from surf.util import attr2rdf, value_to_rdf

def split_attribute_edges(name):
    """ Allow specifying indirect attributes by giving a path of properties
    from the object up to the requested attribute """
    edges = []
    for edge in name.split('__'):
        attr, direct = attr2rdf(edge)
        if attr is None:
            raise ValueError("Not an attribute %r" % edge)
        edges.append((attr, direct))

    return edges

def map_property_value(value):
    if hasattr(value, "subject"):
        # If value has subject attribute, this must be Resource, 
        # take its subject.
        return value.subject

    if not hasattr(value, "__iter__"):
        return value_to_rdf(value)
    else:
        values = []
        for v in value:
            if hasattr(v, "subject"):
                values.append(v.subject)
            else:
                values.append(value_to_rdf(v))
        return values

class Q(object):
    """ A tree with boolean linkage of nodes. """
    OR = 'OR'
    AND = 'AND'

    def __init__(self, **children):
        self.children = map(self.__map, children.items())
        if self.children:
            # AND together given children by default
            self.connection = self.AND
        else:
            self.connection = None

    def copy(self):
        new = Q()
        new.children = list(self.children)
        new.connection = self.connection
        return new

    def __combine(self, other, connection):
        if not isinstance(other, Q):
            raise TypeError(other)
        new = self.copy()
        new.add(other, connection)
        return new

    def add(self, child, connection=AND):
        if type(child) != Q:
            child = self.__map(child)

        if self.connection is None or self.connection == connection:
            # New child with same connection, add to list
            self.children.append(child)
        else:
            # Push down existing children and create new top node
            old = self.copy()
            self.children = [old, child]

        self.connection = connection

    def extend(self, children):
        for child in children:
            self.add(child)

    def __or__(self, other):
        return self.__combine(other, self.OR)

    def __and__(self, other):
        return self.__combine(other, self.AND)

    def __unicode__(self):
        if not self.children:
            return ''
        elif len(self.children) == 1:
            return unicode(self.children[0])
        else:
            con = ') %s (' % self.connection
            return '(' + con.join(map(unicode, self.children)) + ')'

    # resource specific methods

    @classmethod
    def __map(cls, (kw, value)):
        kw = split_attribute_edges(kw)
        value = map_property_value(value)
        return kw, value
