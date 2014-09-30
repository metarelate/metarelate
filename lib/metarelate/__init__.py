# (C) British Crown Copyright 2013, Met Office
#
# This file is part of metarelate.
#
# metarelate is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# metarelate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with metarelate. If not, see <http://www.gnu.org/licenses/>.

from collections import Iterable, MutableMapping, namedtuple
from datetime import datetime
import hashlib
import os
import requests
import urlparse
import time

import pydot
from requests.exceptions import ConnectionError

from metarelate.config import update
import metarelate.prefixes as prefixes

site_config = {
    'root_dir': os.path.abspath(os.path.dirname(__file__)),
    'test_dir': os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             'tests'),
    'graph': 'metarelate.net',
}

update(site_config)

def careful_update(adict, bdict):
    if not set(adict.keys()).isdisjoint(set(bdict.keys())):
        raise ValueError('adict shares keys with bdict')
    else:
        adict.update(bdict)
        return adict

def get_notation(uri):
    """Returns the skos:notation for a uri if it exists, or None.
    If uri is not a http uri, the input is returned as the notation.
    """
    result = None
    if uri.startswith('<') and uri.endswith('>'):
        uri = uri.lstrip('<').rstrip('>')
    if uri.startswith('http://'):
        try:
            r = requests.get(uri, headers={'Accept':'application/ld+json'})
        except requests.exceptions.ConnectionError, e:
            time.sleep(0.5)
            r = requests.get(uri, headers={'Accept':'application/ld+json'})
        if r.status_code == 200:
            try:
                result = r.json().get('skos:notation')
                if isinstance(result, dict):
                    result = result.get('@value')
            except ValueError, e:
                if e.message == 'No JSON object could be decoded':
                    result = uri.split('/')[-1]
        else:
            ## hack to use the last part of the uri for now
            result = uri.split('/')[-1]
    else:
        result = uri
    if isinstance(result, unicode):
        result = str(result)
    return result 


class _DotMixin(object):
    """
    Mixin class for common Dot functionality.

    """
    def dot_escape(self, label):
        """
        Pre-process the string suitable for Dot notation.

        Args:
        * label:
            The string label to be escaped.

        Returns:
            String.

        """
        def escape(label, symbol):
            result = []
            for text in label.split(symbol):
                if len(text) == 0:
                    text = '\%s' % symbol
                result.append(text)
            return ''.join(result)
        for symbol in ['<', '>', ':']:
            label = escape(label, symbol)
        return label


class Mapping(_DotMixin):
    """
    Represents an mapping relationship between a source
    :class:`Component` and a target :class:`Component`.

    """
    def __init__(self, uri=None, source=None, target=None,
                 invertible='"False"', creator=None, note=None,
                 replaces=None, valuemaps=None, rightsHolders=None, 
                 contributors=None, dateAccepted=None):
        uri = Item(uri)
        if source is not None and not isinstance(source, Component):
            msg = 'Expected source {!r} object, got {!r}.'
            raise TypeError(msg.format(Component.__name__,
                                       type(source).__name__))
        if target is not None and not isinstance(target, Component):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(Component.__name__,
                                       type(target).__name__))
        if rightsHolders and not isinstance(rightsHolders, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(rightsHolders).__name__))
        if contributors and not isinstance(contributors, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(contributors).__name__))
        if valuemaps and not isinstance(valuemaps, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(valuemaps).__name__))
        if dateAccepted is not None and not isinstance(dateAccepted, datetime):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(dateAccepted).__name__))
        self.uri = uri
        self.source = source
        self.target = target
        self.invertible = invertible
        self.creator = creator
        self.note = note
        self.replaces = replaces
        self.valuemaps = valuemaps
        self.rightsHolders = rightsHolders
        self.contributors = contributors
        self.dateAccepted = dateAccepted


    def __repr__(self):
        pstr = '{}\nSource:\n{!r}Target:\n{!r}'.format(self.uri, self.source, self.target)
        return pstr

    def __eq__(self, other):
        result = NotImplemented
        if isinstance(other, Mapping):
            result = self.source == other.source and \
                self.target == other.target
        return result

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            result = not result
        return result

    def dot(self):
        """
        Generate a Dot digraph representation of this mapping.

        Returns:
            The :class:`pydot.Dot` instance.

        """
        graph = pydot.Dot(graph_type='digraph',
                          label='Metarelate',
                          labelloc='t', labeljust='l',
                          fontsize=15)
        label = self.dot_escape(self.uri.data)
        node = pydot.Node(label, label='Mapping',
                          shape='box', peripheries='2',
                          style='filled',
                          colorscheme='dark28', fillcolor='1',
                          fontsize=8)
        node.uri = self.uri.data
        graph.add_node(node)
        sgraph = pydot.Cluster('Source', label='Source Concept',
                               labelloc='b',
                               style='filled', color='lightgrey')
        snode = self.source.dot(sgraph, node)
        edge = pydot.Edge(node, snode,
                          label='Concept', fontsize=7,
                          tailport='s', headport='n')
        graph.add_edge(edge)
        graph.add_subgraph(sgraph)
        tgraph = pydot.Cluster('Target', label='Target Concept',
                               labelloc='b',
                               style='filled', color='lightgrey')
        tnode = self.target.dot(tgraph, node)
        edge = pydot.Edge(node, tnode,
                          label='Concept', fontsize=7,
                          tailport='s', headport='n')
        graph.add_edge(edge)
        graph.add_subgraph(tgraph)
        return graph

    def _podict(self):
        """
        Return a dictionary of predicates and objects for a rdf representation

        """
        podict = {}
        if self.source is not None:
            podict['mr:source'] = self.source.uri.data
        if self.target is not None:
            podict['mr:target']  = self.target.uri.data
        podict['mr:invertible'] = self.invertible
        podict['dc:date'] = ['"{}"^^xsd:dateTime'.format(datetime.now().isoformat())]
        podict['dc:creator'] = self.creator
        if self.contributors:
            podict['dc:contributor'] = [cont.data for cont in self.contributors]
        if self.replaces:
            podict['dc:replaces'] = self.replaces
        if self.valuemaps:
            podict['mr:hasValueMap'] = [vmap.uri.data for vmap in self.valuemaps]
        if self.note:
            podict['skos:note'] = self.note
        if self.dateAccepted:
            podict['dc:dateAccepted'] = self.dateAccepted.isoformat()
        return podict


    def create_rdf(self, fuseki_process):
        """
        create the rdf representation using the provided fuseki process

        """
        qstr, instr = self.sparql_creator(self._podict())
        result = fuseki_process.create(qstr, instr)
        self.uri = Item(result['mapping'])


    def json_referrer(self):
        """
        return the data contents of the mapping instance ready for encoding
        as a json string

        """
        referrer = {'mapping': self.uri.data, 'mr:hasValueMap': []}
        referrer['mr:source'] = self.source.json_referrer()
        referrer['mr:target'] = self.target.json_referrer()
        ## what about other attributes?? not implemented yet
        return referrer

    @staticmethod
    def sparql_retriever(uri, rep=True):
        vstr = ''
        if rep:
            vstr += '\n\tMINUS {?mapping ^dc:replaces+ ?anothermap}'
        qstr = '''SELECT ?mapping ?source ?target ?invertible ?replaces 
                         ?note ?date ?creator ?invertible
        (GROUP_CONCAT(DISTINCT(?rightsHolder); SEPARATOR = '&') AS ?rightsHolders)
        (GROUP_CONCAT(DISTINCT(?contibutor); SEPARATOR = '&') AS ?contributors)
        (GROUP_CONCAT(DISTINCT(?valueMap); SEPARATOR = '&') AS ?valueMaps)
        WHERE {
        GRAPH <http://metarelate.net/mappings.ttl> {
        ?mapping mr:source ?source ;
             mr:target ?target ;
             mr:invertible ?invertible ;
             dc:date ?date ;
             dc:creator ?creator .
        BIND("False" AS ?inverted)
        OPTIONAL {?mapping dc:replaces ?replaces .}
        OPTIONAL {?mapping skos:note ?note .}
        OPTIONAL {?mapping mr:hasValueMap ?valueMap .}
        OPTIONAL {?mapping dc:rightsHolder ?rightsHolder .}
        OPTIONAL {?mapping dc:contributor ?contributor .}
        FILTER(?mapping = %s)
        %s
        }
        }
        GROUP BY ?mapping ?source ?target ?invertible ?replaces
                 ?note ?date ?creator ?invertible
        ''' % (uri, vstr)
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        subj_pref = 'http://www.metarelate.net/{}/mapping'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        allowed_preds = set(('mr:source', 'mr:target', 'mr:invertible',
                             'dc:replaces', 'mr:hasValueMap',
                             'skos:note', 'dc:date', 'dc:creator',
                             'dc:rightsHolder', 'dc:contributor', 'dc:rights',
                             'dc:dateSubmitted', 'dc:dateAccepted'))
        preds = set(po_dict)
        if not preds.issubset(allowed_preds):
            ec = '''{}
            is not a subset of the allowed predicates set for a mapping record
            {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        mandated_preds = set(('mr:source', 'mr:target', 'mr:invertible', 
                                'dc:date', 'dc:creator'))
        if not preds.issuperset(mandated_preds):
            ec = '''{}
            is not a superset of the mandated predicates set for a mapping record
            {}'''
            ec = ec.format(preds, mandated_preds)
            raise ValueError(ec)
        singular_preds = set(('mr:source', 'mr:target', 'mr:invertible',
                                 'dc:replaces', 'skos:note',
                                 'dc:date', 'dc:creator'))
        search_string = ''
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if pred in singular_preds and len(po_dict[pred]) != 1:
                    ec = 'create_mapping limits {} to one statement per record '
                    ec = ec.format(pred)
                    raise ValueError(ec)
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
        sha1 = make_hash(po_dict, ['''dc:date'''])
        mapping = '%s/%s' % (subj_pref, sha1)
        qstr = '''SELECT ?mapping
        WHERE {
        GRAPH <http://metarelate.net/mappings.ttl> {
        ?mapping rdf:type mr:Mapping .
        FILTER(?mapping = <%s>)
        } }''' % mapping
        instr = '''INSERT DATA {
        GRAPH <http://metarelate.net/mappings.ttl> {
        <%s> a mr:Mapping ;
                    %s
                    mr:saveCache "True" .
        }
        }
        ''' % (mapping, search_string)
        return qstr, instr


class Component(_DotMixin):
    """
    A Component is a typed identifiable collection of metadata.
    
    One may be an identified as a source or target for a mapping.

    A component is deemed as either *simple* or *compound*:

    * A component is *simple* if it contains properties but no
    component members

    """
    def __init__(self, uri, com_type=None, properties=None):
        self.uri = Item(uri)
        self.com_type = Item(com_type)
        if properties is None:
            properties = []
        for prop in properties:
            if not isinstance(prop, Property):
                raise TypeError('one of the properties is a {}, not '
                                'a metarelate Property'.format(type(prop)))
        self.properties = properties

    def __eq__(self, other):
        result = NotImplemented
        if isinstance(other, type(self)):
            result = False
            if self.uri == other.uri and len(self) == len(other):
                result=True
                if not self.properties.sort() == other.properties.sort():
                    res = False
                if not self.com_type == other.com_type:
                    result = False
        return result

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            result = not result
        return result

    def __len__(self):
        res = len(self.properties)
        return res

    def _props(self):
        props = {}
        if self.__dict__.has_key('properties'):
            for prop in self.properties:
                if props.has_key(prop.predicate.notation):
                    props[prop.predicate.notation].append(prop)
                else:
                    props[prop.predicate.notation] = [prop]
                if props.has_key(prop.predicate.data):
                    props[prop.predicate.data].append(prop)
                else:
                    props[prop.predicate.data] = [prop]
                
        return props

    @property
    def data(self):
        if self.uri:
            res = self.uri.data
        else:
            raise ValueError('Component has no URI')
        return res

    def _okeys(self):
        return ['uri', 'data', 'com_type', 'properties']
        
    def __getattr__(self, key):
        if key in self._okeys():
            result = self.__dict__[key]
        elif key in self._props().keys():
            result = self._props()[key]
            if len(result) == 1:
                result = result[0]
        else:
            msg = '{} object has no attribute "{}"'
            msg = msg.format(type(self).__name__, key)
            raise AttributeError(msg)
        return result

    def __contains__(self, key):
        if key in self._okeys():
            res = True
        elif key in self._props().keys():
            res = True
        else:
            res = False
        return res

    def __setattr__(self, key, value):
        if key in self._props().keys():
            # query make this a list instead
            raise ValueError('A property named {} already exists'.format(key))
        elif key in self._okeys():
            self.__dict__[key] = value
        else:
            if isinstance(value, Property):
                self.properties.append(value)
            else:
                msg = '{} is not a metarelate Property'
                msg = msg.format(type(value).__name__)
                raise TypeError(msg)
        
    def __repr__(self):
        fmt = '{cls}({self.uri!r}, {self.com_type!r}\n'
        fmt += '{properties!r}\n'
        return fmt.format(self=self, cls=type(self).__name__,
                          properties=self.properties)

    @property
    def simple(self):
        return len(self.components) == 0 and \
            len(self.properties) != 0

    @property
    def compound(self):
        return not self.simple

    def dot(self, graph, parent, name=None):
        """
        Generate a Dot digraph representation of this mapping component.

        Args:
         * graph:
            The containing Dot graph.
         * parent:
            The parent Dot node of this property.

        Kwargs:
         * name:
            Name of the relationship between the nodes.

        """
        label = self.dot_escape('{}_{}'.format(parent.uri, self.uri.data))
        # if self.com_type:
        #     nlabel = self.com_type.dot()
        # else:
        #     nlabel = 'Component'
        nlabel = self.com_type
        node = pydot.Node(label, label=nlabel,
                          style='filled', peripheries='2',
                          colorscheme='dark28', fillcolor='3',
                          fontsize=8)
        node.uri = self.uri.data
        graph.add_node(node)
        edge = pydot.Edge(parent, node,
                          tailport='s', headport='n')
        if name is not None:
            edge.set_label(self.dot_escape(name))
            edge.set_fontsize(7)
        graph.add_edge(edge)
        for property in self.properties:
            property.dot(graph, node)#, 'Component')
        return node

    def populate_from_uri(self, fuseki_process):
        statements = fuseki_process.run_query(self.sparql_retriever())
        for statement in statements:
            if statement.get('p') == '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>':
                self.com_type = statement.get('o')
            else:
                data = statement.get('p')
                notation = get_notation(statement.get('p'))
                predicate = Item(data, notation)
                data = statement.get('o')
                notation = get_notation(statement.get('o'))
                rdfobject = Item(data, notation)

                subc = '<http://www.metarelate.net/metOcean/component/'
                if rdfobject.data.startswith(subc):
                    comp = Component(rdfobject.data)
                    comp.populate_from_uri(fuseki_process)
                    self.properties.append(ComponentProperty(predicate,
                                                             comp))
                else:
                    self.properties.append(StatementProperty(predicate, 
                                                             rdfobject))

    # @staticmethod
    def sparql_retriever(self):
        qstr = ('SELECT ?component ?p ?o '
                'WHERE {GRAPH <http://metarelate.net/concepts.ttl> {'
                '?component ?p ?o ; '
                'rdf:type mr:Component .'
                'FILTER(?component = %s) '
                'FILTER(?o != mr:Component) '
                'FILTER(?p != mr:saveCache) '
                '}}' % self.uri.data)
        return qstr

    # @staticmethod
    def sparql_creator(self, po_dict):
        subj_pref = 'http://www.metarelate.net/{}/component'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        search_string = ''
        n_statements = 2
        ## type and savecache
        for pred, objs in po_dict.iteritems():
            for obj in objs:
                search_string += '\t\t{p} {o} \n;'.format(p=pred, o=obj)
                n_statements +=1
        qstr = ('SELECT ?component WHERE {{\n'
                '{SELECT ?component (COUNT(?p) as ?statements)\n'
                'WHERE {\n'
                'GRAPH <http://metarelate.net/concepts.ttl> {\n'
                '?component ?p ?o ;\n'
                '\t%s'
                '\tmr:saveCache "True" ;\n'
                '\t. }}\n'
                '\tGROUP by ?component\n'
                '}\n'
                '\t FILTER(?statements = %i)\n'
                '}UNION{'
                '{SELECT ?component (COUNT(?p) as ?statements)\n'
                'WHERE {\n'
                'GRAPH <http://metarelate.net/concepts.ttl> {\n'
                '?component ?p ?o ;\n'
                '\t%s '
                '\t.}}\n'
                '\tGROUP by ?component\n'
                '}\n'
                '\t FILTER(?statements = %i)\n'
                '}}\n' % (search_string, n_statements, search_string, n_statements-1))
        sha1 = make_hash(po_dict)
        instr = ('INSERT DATA {\n'
                 '\tGRAPH <http://metarelate.net/concepts.ttl> {\n'
                 '\t<%s/%s> rdf:type mr:Component ;\n'
                 '\t%s\n'
                 '\tmr:saveCache "True" .\n'
                 '}}' % (subj_pref, sha1, search_string))
        return qstr, instr

    # def json_referrer(self):
    #     """
    #     return the data contents of the component instance ready for encoding
    #     as a json string

    #     """
    #     ## not updated yet
    #     if len(self) == 1 and self.uri.data == self.components[0].uri.data:
    #         prop_ref = self.components[0].json_referrer()
    #         prop_ref['rdf:type'] = self.com_type.data
    #         referrer = prop_ref
    #     else:
    #         referrer = {'component': self.uri.data,
    #                     prop_ref['rdf:type'] : self.com_type.data,
    #                     'mr:hasComponent': []}
    #         for comp in self.components:
    #             prop_ref = comp.json_referrer()
    #             referrer['mr:hasComponent'].append(prop_ref)
    #     return referrer

    def _podict(self):
        """
        Return a dictionary of predicates and objects for a rdf representation

        """
        podict = {}
        if self.com_type:
            podict['rdf:type'] = [self.com_type.data]
        else:
            raise TypeError('this concept has no type')
        for aprop in self.properties:
            if isinstance(aprop, StatementProperty):
                if aprop.predicate.data in podict:
                    podict[aprop.predicate.data].append(aprop.rdfobject.data)
                else:
                    podict[aprop.predicate.data] = [aprop.rdfobject.data]
            elif isinstance(aprop, ComponentProperty):
                if aprop.predicate.data in podict:
                    podict[aprop.predicate.data].append(aprop.component.uri.data)
                else:
                    podict[aprop.predicate.data] = [aprop.component.uri.data]
            else:
                raise TypeError('property not a recognised type:\n{}'.format(type(prop)))
        return podict

    def creation_sparql(self):
        """
        return SPARQL string for creation of a Concept

        """
        return self.sparql_creator(self._podict())

    def create_rdf(self, fuseki_process):
        """
        create rdf representation using the provided fuseki process

        """
        qstr, instr = self.creation_sparql()
        result = fuseki_process.create(qstr, instr)
        self.uri = Item(result['component'])


class Property(_DotMixin):
    """
    Represents a named tuple property participating in a :class:`Mapping`
    relationship.

    A property is immutable and must have a *name*, but it may also have
    additional meta-data representing its associated *value* and *operator*
    i.e. *standard_name = air_temperature*, where *name* is "standard_name",
    *operator* is "=". and *value* is "air_temperature".

    A :class:`Property` member that participated in a :class:`Mapping`
    relationship must be contained within a :class:`PropertyComponent`.

    A property is deemed as either *simple* or *compound*:

     * A property is *simple* iff its *value* references a :class:`Item`.
     * A property is *compound* iff its *value* references a
       :class:`PropertyComponent`.

    """

    ## ToDo reconsider this class in light of StatementProperty and ComponentProperty
    def __init__(self, uri=None, predicate=None, ptype=None, closematch=None, defby=None,
                 value=None, name=None, operator=None):#, component=None):
        self.uri = Item(uri)
        if predicate is None:
            self.predicate = Item('mr:hasProperty', 'hasProperty')
        elif isinstance(predicate, Item):
            self.predicate = predicate
        else:
            raise TypeError('{!r} is not an Item'.format(predicate))
        self.ptype = Item(ptype)
        self.closematch = Item(closematch)
        self.definedby = Item(defby)
        if name is not None and ptype is not None:
            raise ValueError('A name a ptype may not both be defined for'
                                 'a Property')
        self.name = Item(name)
        # if isinstance(value, (Item, basestring)):
        #     new_value = Item(value)
        # el
        if value is None:
            new_value = value
        elif isinstance(value, int) or isinstance(value, float):
            new_value = value
        elif isinstance(value, str):
            new_value = '"{}"'.format(value)
        else:
            msg = 'Invalid value, got {!r}.'
            raise TypeError(msg.format(type(value).__name__))
        self.value = new_value
        self.operator = Item(operator)
        #self.component = Item(component)

    ## careful here
    # @property
    # def notation(self):
    #     return self.ptype.notation

    def __eq__(self, other):
        result = NotImplemented
        if isinstance(other, Property):
            result = self.uri == other.uri and \
                self.name == other.name and \
                self.value == other.value and \
                self.operator == other.operator and \
                self.ptype == other.ptype and \
                self.closematch == other.closematch and \
                self.definedby == other.definedby and \
                self.component == other.component
        elif self.simple and isinstance(other, (Item, basestring)):
            result = self.value == other
        return result

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            result = not result
        return result

    def __repr__(self):
        fmt = '{cls}(uri={self.uri!r}, {ptype}{cm}{db}{name}{value}{operator})'
        value = operator = component = name = ptype = cm = db = ''
        if self.ptype is not None:
            ptype = ', type={!r}'.format(self.ptype)
        if self.closematch is not None:
            cm = ', closeMatch={!r}'.format(self.closematch)
        if self.definedby is not None:
            db = ', definedBy={!r}'.format(self.definedby)
        if self.name is not None:
            name = ', name={!r}'.format(self.name)
        if self.value is not None:
            value = ', value={!r}'.format(self.value)
        if self.operator is not None:
            operator = ', operator={!r}'.format(self.operator)
        return fmt.format(self=self, cls=type(self).__name__,
                          ptype=ptype, name=name,
                          cm=cm, db=db,
                          value=value, operator=operator)

    @property
    def simple(self):
        return isinstance(self.value, Item) or self.value is None

    @property
    def compound(self):
        return not self.simple

    @property
    def complete(self):
        return self.simple and self.value is not None and self.value.complete

    def _podict(self):
        """
        Return a dictionary of predicates and objects for a rdf representation

        """
        podict = {}
        if self.name:
            podict['mr:name'] = self.name.data
        if self.value:
            podict['rdf:value'] = self.value
        # if self.component:
        #     podict['mr:hasComponent'] = self.component.data
        if self.operator:
            podict['mr:operator'] = self.operator.data
        if self.ptype:
            podict['rdf:type'] = self.ptype.data
        if self.closematch:
            podict['skos:closeMatch'] = self.closematch.data
        if self.definedby:
            podict['rdfs:isDefinedBy'] = self.definedby.data
        return podict

    def creation_sparql(self):
        """
        return SPARQL string for creation of a Property

        """
        return self.sparql_creator(self._podict())

    def as_rdf(self, fuseki_process):
        return(self.predicate, self._create_rdf(fuseki_process))

    def _create_rdf(self, fuseki_process):
        """
        create the rdf representation using the provided fuseki process

        """
        qstr, instr = self.creation_sparql()
        result = fuseki_process.create(qstr, instr)
        self.uri = Item(result['property'])

    def dot(self, graph, parent, name=None):
        """
        Generate a Dot digraph representation of this mapping property.

        Args:
         * graph:
            The containing Dot graph.
         * parent:
            The parent Dot node of this property.

        Kwargs:
         * name:
            Name of the relationship between the nodes.

        """
        items = []
        if self.ptype is not None:
            items.append(self.ptype.dot())
        if self.closematch is not None:
            items.append(self.closematch.dot())
        if self.definedby is not None:
            items.append(self.definedby.dot())
        if self.name is not None:
            items.append(self.name.dot())
        if self.operator is not None:
            items.append(self.operator.dot())
        if self.value is not None and isinstance(self.value, Item):
            items.append(self.value.dot())
        items = ' '.join(items)
        label = self.dot_escape('{}_{}'.format(parent.uri, self.uri.data))
        node = pydot.Node(label, label=items,
                          style='filled',
                          colorscheme='dark28', fillcolor='4',
                          fontsize=8)
        node.uri = self.uri.data
        graph.add_node(node)
        edge = pydot.Edge(parent, node,
                          tailport='s', headport='n')
        if name is not None:
            edge.set_label(self.dot_escape(name))
            edge.set_fontsize(7)
        graph.add_edge(edge)

        if self.value is not None and not isinstance(self.value, Item):
            # This property references a component.
            self.value.dot(graph, node, 'Component')

    @staticmethod
    def sparql_retriever(uri):
        qstr = '''SELECT ?property ?name ?operator ?component
                         ?closematch ?ptype ?defby
        (GROUP_CONCAT(?avalue; SEPARATOR='&') AS ?value)
        WHERE {
        GRAPH <http://metarelate.net/concepts.ttl> {
            OPTIONAL {?property mr:name ?name .}
            OPTIONAL {?property rdf:value ?avalue .}
            OPTIONAL {?property mr:operator ?operator . }
            OPTIONAL {?property mr:hasComponent ?component . }
            OPTIONAL {?property skos:closeMatch ?closematch .}
            OPTIONAL {?property rdf:type ?ptype .}
            OPTIONAL {?property rdfs:isDefinedBy ?defby .}
            FILTER(?property = %s)
            FILTER(?ptype != mr:Property)
            }
            {SELECT ?property WHERE {
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?property rdf:type mr:Property .
            }}}
        }
        GROUP BY ?property ?name ?operator ?component
        ''' % uri
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        qstr = ''
        instr = ''
        allowed_predicates = set(('rdf:type', 'mr:name', 'rdf:value',
                                'mr:operator', 'mr:hasComponent',
                                'skos:closeMatch', 'rdfs:isDefinedBy'))
        single_predicates = set(('mr:name', 'mr:operator', 'mr:hasComponent'))
        preds = set(po_dict)
        if not preds.issubset(allowed_predicates):
            ec = '{} is not a subset of the allowed predicates set '\
                 'for a value record {}'
            ec = ec.format(preds, allowed_predicates)
            raise ValueError(ec)
        subj_pref = 'http://www.metarelate.net/{}/property'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        count_string = ''
        search_string = ''
        filter_string = ''
        assign_string = ''
        block_string = ''
        for pred in allowed_predicates.intersection(preds):
            if isinstance(po_dict[pred], list):
                if len(po_dict[pred]) != 1 and pred in single_predicates:
                    ec = 'get_property only accepts 1 statement per predicate {}'
                    ec = ec.format(str(po_dict))
                    raise ValueError(ec)
                else:
                    counter = 0
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
                        counter +=1
                    assign_string += '''
                    %s ?%s ;''' % (pred, pred.split(':')[-1])
                    count_string += '''COUNT(DISTINCT(?%(p)s)) AS ?%(p)ss
                    ''' % {'p':pred.split(':')[-1]}
                    filter_string += '''
                    FILTER(?%ss = %i)''' % (pred.split(':')[-1], counter)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
                assign_string += '''
                %s ?%s ;''' % (pred, pred.split(':')[-1])
                count_string += '''(COUNT(DISTINCT(?%(p)s)) AS ?%(p)ss)
                ''' % {'p':pred.split(':')[-1]}
                filter_string += '''
                FILTER(?%ss = %i)''' % (pred.split(':')[-1], 1)
        for pred in allowed_predicates.difference(preds):
            block_string += '\n\t OPTIONAL{?property %s ?%s .}' % (pred, pred.split(':')[-1])
            block_string += '\n\t FILTER(!BOUND(?%s))' % pred.split(':')[-1]
        if search_string != '':
            qstr = '''SELECT ?property
            WHERE { {
            SELECT ?property        
            %(count)s
            WHERE{
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?property %(assign)s %(search)s
            .
            %(block)s
            FILTER(?type != mr:Property)
            }
            {SELECT ?property WHERE {
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?property rdf:type mr:Property .
            }}}
            }
            GROUP BY ?property
            }
            %(filter)s
            }
            ''' % {'count':count_string,'assign':assign_string,
                   'search':search_string, 'filter':filter_string,
                   'block':block_string}
            sha1 = make_hash(po_dict)
            instr = '''INSERT DATA {
            GRAPH <http://metarelate.net/concepts.ttl> {
            <%s/%s> rdf:type mr:Property ;
                    %s
            mr:saveCache "True" .
            }
            }
            ''' % (subj_pref, sha1, search_string)
        return qstr, instr


class ComponentProperty(Property):
    """
    A property which is only a predicate(Item) and an
    object(Component)

    """
    def __init__(self, predicate, component):
        if not isinstance(predicate, Item):
            raise TypeError('predicate: {!r} is not a metarelate '
                            'Item'.format(predicateitem))
        if not isinstance(component, Component):
            raise TypeError('rdfobject: {!r} is not a metarelate '
                            'Item or Component'.format(rdfobject))
        self.predicate = predicate
        self.component = component

    def __repr__(self):
        return '{!r}:{!r}'.format(self.predicate, self.component)

    def get_identifiers(self, fuseki_process):
        comp_ids = {}
        for prop in self.component.properties:
            careful_update(comp_ids, prop.get_identifiers(fuseki_process))
        identifiers = {self.predicate.notation: comp_ids}
        return identifiers

    def dot(self, graph, parent, name=None):
        """
        Generate a Dot digraph representation of this mapping property.

        Args:
         * graph:
            The containing Dot graph.
         * parent:
            The parent Dot node of this property.

        Kwargs:
         * name:
            Name of the relationship between the nodes.

        """
        items = self.predicate.dot()
        label = self.dot_escape('{}'.format(self.predicate.notation))
        node = pydot.Node(label, label=items,
                          style='filled',
                          colorscheme='dark28', fillcolor='4',
                          fontsize=8)
        node.uri = self.predicate.data
        graph.add_node(node)
        cgraph = pydot.Cluster(self.predicate.notation, label=self.predicate.notation,
                               labelloc='b',
                               style='filled', color='grey')
        anode = self.component.dot(cgraph, node)
        graph.add_subgraph(cgraph)

        edge = pydot.Edge(parent, node,
                          tailport='s', headport='n')
        if name is not None:
            edge.set_label(self.dot_escape(name))
            edge.set_fontsize(7)
        graph.add_edge(edge)


class StatementProperty(Property):
    """
    A property which is only a predicate(Item) and an
    object(Item)

    """
    def __init__(self, predicate, rdfobject):
        if not isinstance(predicate, Item):
            raise TypeError('predicate: {!r} is not a metarelate '
                            'Item'.format(predicateitem))
        if not isinstance(rdfobject, Item):
            raise TypeError('rdfobject: {!r} is not a metarelate '
                            'Item'.format(rdfobject))
        self.predicate = predicate
        self.rdfobject = rdfobject

    def __eq__(self, other):
        result = False
        if isinstance(other, StatementProperty):
            predres = self.predicate == other.predicate
            objres = self.rdfobject == other.rdfobject
            result = predres and objres
        return result

    def __ne__(self, other):
        result = not self.__eq__(other)
        return result

    def __repr__(self):
        return '{!r}:{!r}'.format(self.predicate, self.rdfobject)
    # def as_rdf(self, fuseki_process=None):
    #     return (self.predicate, self.rdfobject)

    def get_identifiers(self, fuseki_process):
        """Returns a dictionary of key value pairs, providing a pattern
        of skos:notations which match the component explicitly"""
        qstr = ('SELECT ?key ?value'
                ' WHERE {'
                '  {SELECT ?key ?value'
                '   WHERE {'
                '    {SERVICE %(ps)s '
                '     {SELECT ?key ?value WHERE {'
                '      %(p)s skos:notation ?key .'
                '    }}}'
                '    {SERVICE %(os)s '
                '     {SELECT ?value WHERE {'
                '      %(o)s skos:notation ?value'
                '    }}}'
                '       }}'
                ' UNION '
                '  {SELECT ?key ?value'
                '   WHERE {'
                '    {SERVICE %(ps)s '
                '     {SELECT ?key ?value WHERE {'
                '      %(p)s skos:notation ?key .'
                '      FILTER(isLiteral(%(o)s))'
                '      BIND(%(o)s as ?value)'
                '    }}}'
                '       }}'
                ' UNION '
                '  {SELECT ?key ?value'
                '   WHERE {'
                '    {SERVICE %(os)s '
                '     {SELECT ?key ?value ?idr ?rdfobj ?rdfobjnot WHERE {'
                '      %(o)s <http://metarelate.net/vocabulary/index.html#identifier> ?idr ;'
                '       ?idr ?rdfobj .'
                '      OPTIONAL {?idr skos:notation ?key . }'
                '      OPTIONAL {?rdfobj skos:notation ?rdfobjnot}'
                '      {SERVICE %(ps)s'
                '       {SELECT ?idr ?key ?rdfobj ?rdfobjnot WHERE {'
                '        OPTIONAL {?idr skos:notation ?key . }'
                '        OPTIONAL {?rdfobj skos:notation ?rdfobjnot}'
                '       }}}'
                '      BIND((IF(isURI(?rdfobj), ?rdfobjnot, ?rdfobj)) AS ?value)'
                '     }}'
                '    }'
                '  }}'
                '}')
        predicate = self.predicate.data
        psplit = urlparse.urlsplit(predicate.strip('<>'))
        if psplit.netloc == 'vocab.nerc.ac.uk':
            pdomain = 'def.scitools.org.uk'
        else:
            pdomain = psplit.netloc 
        pspq = '<{}://{}/system/query?>'.format(psplit.scheme, pdomain)
        rdfobject = self.rdfobject.data
        msplit = urlparse.urlsplit(rdfobject.strip('<>'))
        if msplit.netloc:
            if msplit.netloc == 'vocab.nerc.ac.uk':
                mdomain = 'def.scitools.org.uk'
            else:
                mdomain = msplit.netloc 
            rospq = '<{}://{}/system/query?>'.format(msplit.scheme, mdomain)
        else:
            rospq = pspq

        aqstr = qstr % {'p':predicate, 'o':rdfobject, 'ps':pspq, 'os':rospq}
        results = fuseki_process.run_query(aqstr)
        identifiers = {}
        for item in results:
            key = item.get('key').strip('"')
            value = item.get('value').strip('"')
            if isinstance(value, unicode):
                value=str(value)
            if not (key is not None and value is not None):
                raise ValueError('key and value required, but not present\n'
                                 '{}'.format(item))
            else:
                if identifiers.has_key(key):
                    raise ValueError('duplicate key: {}'.format(key))
            identifiers[key] = value
        # until nerc vocab server is understood
        if self.rdfobject.data.startswith('<http://vocab.nerc.ac.uk'):
            sn = self.rdfobject.data.rstrip('>').split('/')[-1]
            identifiers['standard_name'] = sn
        return identifiers

    @property
    def notation(self):
        return self.rdfobject.notation

    def dot(self, graph, parent, name=None):
        """
        Generate a Dot digraph representation of this mapping property.

        Args:
         * graph:
            The containing Dot graph.
         * parent:
            The parent Dot node of this property.

        Kwargs:
         * name:
            Name of the relationship between the nodes.

        """
        items = []
        items.append(self.predicate.dot())
        items.append(self.rdfobject.dot())
        items = ': '.join(items)
        label = self.dot_escape('{}_{}'.format(self.predicate.data, 
                                               self.rdfobject.data))
        node = pydot.Node(label, label=items,
                          style='filled',
                          colorscheme='dark28', fillcolor='4',
                          fontsize=8)
        node.uri = label
        graph.add_node(node)
        edge = pydot.Edge(parent, node,
                          tailport='s', headport='n')
        if name is not None:
            edge.set_label(self.dot_escape(name))
            edge.set_fontsize(7)
        graph.add_edge(edge)


class Item(_DotMixin, namedtuple('Item', 'data notation')):
    """
    Represents an rdf data item, as an rdf:literal, or as a subject URI and,
    optionally, an associated skos notation in the form of an immutable
    named tuple.

    """
    def __new__(cls, data, notation=None):
        if data is None and notation is None:
            res = None
        else:
            if isinstance(data, str):
                if data.startswith('http'):
                    new_data = '<{}>'.format(data)
                elif data.startswith('<'):
                    new_data = data
                elif data.startswith('"'):
                    new_data = data
                else:
                    new_data = '"{}"'.format(data)
            else:
                new_data = data
            new_notation = None
            if isinstance(data, Item):
                new_data = data.data
                new_notation = data.notation
            if notation is not None:
                if isinstance(notation, basestring) and len(notation) > 1 and \
                        notation.startswith('"') and notation.endswith('"'):
                    notation = notation[1:-1]
                new_notation = notation
            #else:
                #look up notation
                #but it's immutable
                #so write a func in fuseki which takes a notation free Item
                #and returns an Item with its notation
                #pass
            res = super(Item, cls).__new__(cls, new_data, new_notation)
        return res

    def is_uri(self):
        """
        Determine whether the mapping data item is a valid URI.

        Returns:
            Boolean.

        """
        result = False
        if isinstance(self.data, basestring):
            uri = self.data
            if uri.startswith('<') and uri.endswith('>'):
                uri = uri[1:-1]
            uri = urlparse.urlparse(uri)
            result = len(uri.scheme) > 0 and len(uri.netloc) > 0
        return result

    def __eq__(self, other):
        result = NotImplemented
        if isinstance(other, Item):
            result = self.data == other.data and \
                self.notation == other.notation
        elif isinstance(other, basestring):
            notation = self.notation
            if isinstance(notation, basestring):
                notation = notation.lower()
            result = self.data == other or notation == other.lower()
        return result

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            result = not result
        return result

    def __setattr__(self, name, value):
        msg = '{!r} instance is immutable.'
        raise TypeError(msg.format(type(self).__name__))

    def __repr__(self):
        fmt = '{self.data!r}'
        if self.notation is not None:
            fmt = '{cls}(data={self.data!r}, notation={self.notation!r})'
        return fmt.format(self=self, cls=type(self).__name__)

    @property
    def complete(self):
        return self.data is not None and self.notation is not None

    def dot(self):
        """
        Return a Dot escaped string representation of the mapping item.

        If the skos notation is available, this has priority.

        Returns:
            String.

        """
        label = self.dot_escape(self.data)
        if self.notation is not None:
            label = self.dot_escape(str(self.notation))
        return label


# class ValueMap(object):
#     @staticmethod
#     def sparql_retriever(uri):
#         qstr = '''SELECT ?valueMap ?source ?target
#         WHERE {
#         GRAPH <http://metarelate.net/concepts.ttl> {
#             ?valueMap mr:source ?source ;
#                       mr:target ?target .
#             FILTER(?valueMap = %s)
#             }
#         }
#         ''' % uri
#         return qstr

#     @staticmethod
#     def sparql_creator(po_dict):
#         qstr = ''
#         instr = ''
#         allowed_preds = set(('mr:source','mr:target'))
#         preds = set(po_dict)
#         if not preds == allowed_preds:
#             ec = '''{} is not a subset of the allowed predicates set
#                     for a valueMap record
#                     {}'''
#             ec = ec.format(preds, allowed_preds)
#             raise ValueError(ec)
#         subj_pref = 'http://www.metarelate.net/{}/valueMap'
#         subj_pref = subj_pref.format(site_config['fuseki_dataset'])
#         search_string = ''
#         for pred in po_dict:
#             if isinstance(po_dict[pred], list):
#                 if len(po_dict[pred]) != 1:
#                     ec = 'get_format_concept only accepts 1 mr:format statement }'
#                     ec = ec.format(po_dict)
#                     raise ValueError(ec)
#                 else:
#                     for obj in po_dict[pred]:
#                         search_string += '''
#                         %s %s ;''' % (pred, obj)
#             else:
#                 search_string += '''
#                 %s %s ;''' % (pred, po_dict[pred])
#         if search_string != '':
#             qstr = '''SELECT ?valueMap 
#             WHERE{
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             ?valueMap
#                    %s .
#             }
#             }
#             ''' % (search_string)
#             sha1 = make_hash(po_dict)
#             instr = '''INSERT DATA {
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             <%s/%s> a mr:ValueMap ;
#                     %s
#                     mr:saveCache "True" .
#             }
#             }
#             ''' % (subj_pref, sha1, search_string)
#         return qstr, instr


# class Value(object):
#     @staticmethod
#     def sparql_retriever(uri):
#         qstr = '''SELECT ?value ?operator ?subject ?object
#         WHERE {
#         GRAPH <http://metarelate.net/concepts.ttl> {
#             ?value mr:subject ?subject .
#             OPTIONAL {?value mr:operator ?operator .}
#             OPTIONAL {?value mr:object ?object . }
#             FILTER(?value = %s)
#             }
#         }
#         ''' % uri
#         return qstr

#     @staticmethod
#     def sparql_creator(po_dict):
#         qstr = ''
#         instr = ''
#         allowed_preds = set(('mr:operator','mr:subject', 'mr:object'))
#         preds = set(po_dict)
#         if not preds.issubset(allowed_preds):
#             ec = '''{} is not a subset of the allowed predicates set
#                     for a value record
#                     {}'''
#             ec = ec.format(preds, allowed_preds)
#             raise ValueError(ec)
#         subj_pref = 'http://www.metarelate.net/{}/value'
#         subj_pref = subj_pref.format(site_config['fuseki_dataset'])
#         search_string = ''
#         for pred in po_dict:
#             if isinstance(po_dict[pred], list):
#                 if len(po_dict[pred]) != 1:
#                     ec = 'get_value only accepts 1 mr:format statement }'
#                     ec = ec.format(po_dict)
#                     raise ValueError(ec)
#                 else:
#                     for obj in po_dict[pred]:
#                         search_string += '''
#                         %s %s ;''' % (pred, obj)
#             else:
#                 search_string += '''
#                 %s %s ;''' % (pred, po_dict[pred])
#         if search_string != '':
#             qstr = '''SELECT ?value
#             WHERE{
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             ?value
#                    %s .
#             }
#             }
#             ''' % (search_string)
#             sha1 = make_hash(po_dict)
#             instr = '''INSERT DATA {
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             <%s/%s> a mr:Value ;
#                     %s
#                     mr:saveCache "True" .
#             }
#             }
#             ''' % (subj_pref, sha1, search_string)
#         return qstr, instr


# class ScopedProperty(object):
#     @staticmethod
#     def sparql_retriever(uri):
#         qstr = '''SELECT ?scopedProperty ?scope ?hasProperty
#         WHERE {
#         GRAPH <http://metarelate.net/concepts.ttl> {
#             ?scopedProperty mr:scope ?scope ;
#                       mr:hasProperty ?hasProperty .
#             FILTER(?scopedProperty = %s)
#             }
#         }
#         ''' % uri
#         return qstr

#     @staticmethod
#     def sparql_creator(po_dict):
#         qstr = ''
#         instr = ''
#         allowed_preds = set(('mr:scope','mr:hasProperty'))
#         preds = set(po_dict)
#         if not preds == allowed_preds:
#             ec = '''{} is not a subset of the allowed predicates set
#                     for a scopedProperty record
#                     {}'''
#             ec = ec.format(preds, allowed_preds)
#             raise ValueError(ec)
#         subj_pref = 'http://www.metarelate.net/{}/scopedProperty'
#         subj_pref = subj_pref.format(site_config['fuseki_dataset'])
#         search_string = ''
#         for pred in po_dict:
#             if isinstance(po_dict[pred], list):
#                 if len(po_dict[pred]) != 1:
#                     ec = 'get_scopedProperty only accepts 1 mr:format statement {}'
#                     ec = ec.format(po_dict)
#                     raise ValueError(ec)
#                 else:
#                     for obj in po_dict[pred]:
#                         search_string += '''
#                         %s %s ;''' % (pred, obj)
#             else:
#                 search_string += '''
#                 %s %s ;''' % (pred, po_dict[pred])
#         if search_string != '':
#             qstr = '''SELECT ?scopedProperty
#             WHERE{
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             ?scopedProperty
#                    %s .
#             }
#             }
#             ''' % (search_string)
#             sha1 = make_hash(po_dict)
#             instr = '''INSERT DATA {
#             GRAPH <http://metarelate.net/concepts.ttl> {
#             <%s/%s> a mr:Property ;
#                     %s
#                     mr:saveCache "True" .
#             }
#             }
#             ''' % (subj_pref, sha1, search_string)
#         return qstr, instr


# class Mediator(object):
#     @staticmethod
#     def sparql_retriever(uri=None, fformat=''):
#         if fformat:
#             ffilter = 'FILTER(?format = <http://www.metarelate.net/{ds}/format/{f}>)'
#             ffilter = ffilter.format(ds=site_config['fuseki_dataset'], f=fformat)
#         else:
#             ffilter = ''
#         urifilter = ''
#         if uri is not None:
#             urifilter = 'FILTER(?mediator = <{}>)'.format(uri)
#         qstr = '''
#         SELECT ?mediator ?label
#         WHERE
#         { GRAPH <http://metarelate.net/concepts.ttl> {
#                       rdf:label ?label .
#         %s
#         %s
#         } }
#         ''' % (urifilter, ffilter)
#         return qstr

#     @staticmethod
#     def sparql_creator(po_dict):
#         allowed_preds = set(('rdf:type','rdf:label'))
#         preds = set(po_dict)
#         if not preds == allowed_preds:
#             ec = '''{} is not a subset of the allowed predicates set
#                     for a scopedProperty record
#                     {}'''
#             ec = ec.format(preds, allowed_preds)
#             raise ValueError(ec)
#         atype = po_dict['rdf:type']
#         label = po_dict['rdf:label']
#         ff = fformat.rstrip('>').split('/')[-1]
#         med = '<http://www.metarelate.net/{ds}/mediates/{f}/{l}>'
#         med = med.format(ds=site_config['fuseki_dataset'], f=ff, l=label)
#         qstr = '''
#         SELECT ?mediator
#         WHERE
#         { GRAPH <http://metarelate.net/concepts.ttl> {
#         %s a mr:Mediator, {} ;
#              rdf:label "%s" ;
#              .
#              } }
#         ''' % (med, atype, label)
#         instr = '''
#         INSERT DATA
#         { GRAPH <http://metarelate.net/concepts.ttl> {
#         %s a mr:Mediator, {} ;
#              rdf:label "%s" ;
#              mr:saveCache "True" .
#              } }
#         ''' % (med, atype, label)
#         return qstr, instr


def make_hash(pred_obj, omitted=None):
    """ creates and returns an sha-1 hash of the elements in the pred_obj
    (object list) dictionary
    skipping any 'ommited' (list) predicates and objects

    Args:
    
    * pred_obj:
        A dictionary of predicates and lists of objects, or single objects
        which will be used, in order, to construct the hash
    * omitted:
        A list of predicate strings to be ignored when building the hash
        
    """
    if omitted is None:
        omitted = []
    pre = prefixes.Prefixes()
    sha1 = hashlib.sha1()
    #sort keys
    po_keys = pred_obj.keys()
    po_keys.sort()
    for pred in po_keys:
        if pred not in omitted:
            if not pred.startswith('<'):
                pred_elems = pred.split(':')
                if len(pred_elems) == 2:
                    if pre.has_key(pred_elems[0]):
                        predicate = '%s%s' % (pre[pred_elems[0]], pred_elems[1])
                    else:
                        raise ValueError('predicate {} not in prefixes.py'
                                         ''.format(pred_elems[0]))
                else:
                    raise ValueError('make hash passed a predicate '
                                     'which is not of the form <prefix>:<item>')
            else:
                predicate = pred
            if isinstance(pred_obj[pred], list):
                for obj in pred_obj[pred]:
                    sha1.update(predicate)
                    sha1.update(obj)
            else:
                sha1.update(predicate)
                sha1.update(pred_obj[pred])
    sha1_hex = str(sha1.hexdigest())
    return sha1_hex
    

class Contact(object):
    """a named contact in the knowledgebase"""
    @staticmethod
    def sparql_retriever(uri=None, contact_type=None):
        tfilter = ''
        urifilter = ''
        if contact_type is not None:
            tfilter = 'FILTER(?contact skos:inScheme metoc:{})'
            tfilter = tfilter.format(contact_type)
        if uri is not None:
            urifilter = 'FILTER(?contact = <{}>)'.format(uri)
        qstr ='''SELECT ?contact ?prefLabel ?def
        WHERE
        { GRAPH <http://metarelate.net/contacts.ttl> {
            ?s skos:inScheme <http://www.metarelate.net/%s/%s> ;
               skos:prefLabel ?prefLabel ;
               skos:definition ?def ;
               dc:valid ?valid .
        %s
        %s
        } }''' % (urifilter, ffilter)
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        allowed_preds = set(('skos:inScheme', 'skos:prefLabel',
                             'skos:definition', 'dc:valid'))
        preds = set(po_dict)
        if not preds == allowed_preds:
            ec = '''{} is not the same as the allowed predicates set
                    for a scopedProperty record
                    {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        scheme = po_dict['skos:inScheme'].split('/')[-1].rstrip('>')
        #print scheme
        search_string = ''
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if len(po_dict[pred]) != 1:
                    ec = 'contacts only accepts 1 statement per predicate {}'
                    ec = ec.format(po_dict)
                    raise ValueError(ec)
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '%s %s ;\n' % (pred, po_dict[pred])
        po_hash = make_hash(po_dict)
        qstr = '''
        SELECT ?contact
        WHERE
        { GRAPH <http://metarelate.net/contacts.ttl> {
        ?contact a skos:Concept ;
           %s
           .
             } }
        ''' % search_string
        instr = '''
        INSERT DATA
        { GRAPH <http://metarelate.net/contacts.ttl> {
        <http://www.metarelate.net/metOcean/%s/%s> a skos:Concept ;
           %s
             mr:saveCache "True" .
             } }
        ''' % (scheme, po_hash, search_string)
        #print scheme, po_hash, search_string
        return qstr, instr
