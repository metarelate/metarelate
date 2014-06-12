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
from urlparse import urlparse

import pydot

from metarelate.config import update
import metarelate.prefixes as prefixes

site_config = {
    'root_dir': os.path.abspath(os.path.dirname(__file__)),
    'test_dir': os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             'tests'),
    'graph': 'metarelate.net',
}

update(site_config)


# class _ComponentMixin(object):
#     """
#     Mixin class for common mapping component behaviour.

#     """
#     # def __setitem__(self, key, value):
#     #     self._immutable_exception()

#     # def __delitem__(self, key):
#     #     self._immutable_exception()

#     # def __getattr__(self, name):
#     #     return self.__getitem__(name)

#     # def __iter__(self):
#     #     return iter(self._data)

#     # def __len__(self):
#     #     return len(self._data)

#     def _immutable_exception(self):
#         msg = '{!r} object is immutable.'
#         raise TypeError(msg.format(type(self).__name__))


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
    def __init__(self, uri, source, target, invertible='"False"',
                 editor=None, note=None, reason=None, replaces=None, 
                 valuemaps=None, owners=None, watchers=None, status=None):
        uri = Item(uri)
        if not isinstance(source, Component):
            msg = 'Expected source {!r} object, got {!r}.'
            raise TypeError(msg.format(Component.__name__,
                                       type(source).__name__))
        if not isinstance(target, Component):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(Component.__name__,
                                       type(target).__name__))
        if owners and not isinstance(owners, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(owners).__name__))
        if valuemaps and not isinstance(valuemaps, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(valuemaps).__name__))
        if watchers and not isinstance(watchers, list):
            msg = 'Expected target {!r} object, got {!r}.'
            raise TypeError(msg.format(list.__name__,
                                       type(watchers).__name__))
        self.uri = uri
        self.source = source
        self.target = target
        self.invertible = invertible
        self.editor = editor
        self.note = note
        self.reason = reason
        self.replaces = replaces
        self.valuemaps = valuemaps
        self.owners = owners
        self.watchers = watchers
        self.status = status

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

    def _check_status(self):
        status = False
        allowed = ['"Draft"', '"Proposed"', '"Approved"',
                   '"Broken"', '"Deprecated"']
        if self.status:
            if self.status not in allowed:
                msg = ('{} is not an allowed value'.format(self.status),
                       ' for status please use one of {}'.format(allowed))
                raise ValueError(msg)
            status = True
        return status

    def _podict(self):
        """
        Return a dictionary of predicates and objects for a rdf representation

        """
        podict = {}
        podict['mr:source'] = self.source.uri.data
        podict['mr:target']  = self.target.uri.data
        podict['mr:invertible'] = self.invertible
        podict['dc:date'] = ['"{}"^^xsd:dateTime'.format(datetime.now().isoformat())]
        podict['dc:creator'] = self.editor
        if self.replaces:
            podict['dc:replaces'] = self.replaces
        if self.valuemaps:
            podict['mr:hasValueMap'] = [vmap.uri.data for vmap in self.valuemaps]
        if self._check_status():
            podict['mr:status'] = self.status
        if self.note:
            podict['skos:note'] = self.note
        if self.reason:
            podict['mr:reason'] = self.reason
        # if self.owners:
        #     podict['mr:owner'] = [owner for owner in self.owners]
        # if self.watchers:
        #     podict['mr:watcher'] = self.watchers
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
    def sparql_retriever(uri, valid=True, rep=True):
        vstr = ''
        if valid:
            vstr += '\tFILTER (?status NOT IN ("Deprecated", "Broken"))'
        if rep:
            vstr += '\n\tMINUS {?mapping ^dc:replaces+ ?anothermap}'
        qstr = '''SELECT ?mapping ?source ?target ?invertible ?replaces ?status
                         ?note ?reason ?date ?creator ?inverted
        (GROUP_CONCAT(DISTINCT(?owner); SEPARATOR = '&') AS ?owners)
        (GROUP_CONCAT(DISTINCT(?watcher); SEPARATOR = '&') AS ?watchers)
        (GROUP_CONCAT(DISTINCT(?valueMap); SEPARATOR = '&') AS ?valueMaps)
        WHERE {
        GRAPH <http://metarelate.net/mappings.ttl> {
        ?mapping mr:source ?source ;
             mr:target ?target ;
             mr:invertible ?invertible ;
             mr:status ?status ;
             mr:reason ?reason ;
             dc:date ?date ;
             dc:creator ?creator .
        BIND("False" AS ?inverted)
        OPTIONAL {?mapping dc:replaces ?replaces .}
        OPTIONAL {?mapping skos:note ?note .}
        OPTIONAL {?mapping mr:hasValueMap ?valueMap .}
        OPTIONAL {?mapping mr:owner ?owner .}
        OPTIONAL {?mapping mr:watcher ?watcher .}
        FILTER(?mapping = %s)
        %s
        }
        }
        GROUP BY ?mapping ?source ?target ?invertible ?replaces
                 ?status ?note ?reason ?date ?creator ?inverted
        ''' % (uri, vstr)
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        subj_pref = 'http://www.metarelate.net/{}/mapping'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        allowed_preds = set(('mr:source', 'mr:target', 'mr:invertible',
                                'dc:replaces', 'mr:hasValueMap', 'mr:status',
                                'skos:note', 'mr:reason', 'dc:date', 'dc:creator',
                                'mr:owner', 'mr:watcher'))
        preds = set(po_dict)
        if not preds.issubset(allowed_preds):
            ec = '''{}
            is not a subset of the allowed predicates set for a mapping record
            {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        mandated_preds = set(('mr:source', 'mr:target', 'mr:invertible', 
                                'mr:status',  'mr:reason',
                                'dc:date', 'dc:creator'))
        if not preds.issuperset(mandated_preds):
            ec = '''{}
            is not a superset of the mandated predicates set for a mapping record
            {}'''
            ec = ec.format(preds, mandated_preds)
            raise ValueError(ec)
        singular_preds = set(('mr:source', 'mr:target', 'mr:invertible',
                                 'dc:replaces', 'mr:status', 'skos:note',
                                 'mr:reason', 'dc:date', 'dc:creator'))
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


# class Component(_ComponentMixin, _DotMixin, MutableMapping):
class Component(_DotMixin):
    """
    A component is an identified source or target for a mapping

    A component is deemed as either *simple* or *compound*:

    * A component is *simple* if it contains properties but no
    component members

    """
    def __init__(self, uri, com_type=None, components=[], properties=[],
                 requires=[], mediator=None):
        # self.__dict__['uri'] = Item(uri)
        self.uri = Item(uri)
        if com_type is not None:
            self.com_type = Item(com_type)
        # self.requires = [Item(req) for req in requires]
        # self.mediator = Item(mediator)
        for comp in components:
            if not isinstance(comp, Component):
                raise TypeError('one of the components is a {}, not '
                                'a metarelate Component'.format(type(comp)))
        self.components = components
        for prop in properties:
            if not isinstance(prop, Property):
                raise TypeError('one of the properties is a {}, not '
                                'a metarelate Property'.format(type(prop)))
        self.properties = properties

    def _retrieve(self, fuseki_process):
        if self.uri:
            qstr = self.sparql_retriever(uri)
            response = fuseki_process.run_query(qstr)
            # populate attrs
            # not yet done

    def __eq__(self, other):
        result = NotImplemented
        if isinstance(other, type(self)):
            result = False
            if self.uri == other.uri and len(self) == len(other):
                result=True
                if not self.components.sort() == other.components.sort():
                    res = False
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
        if self.simple:
            res = len(self.properties)
        else:
            res = len(self.properties) + len(self.components)
        return res

    def _props(self):
        if self.__dict__.has_key('properties'):
            uniquekeys = len(set([p.notation for p in self.__dict__['properties']]))
            if len(self.__dict__['properties']) != uniquekeys:
                raise ValueError('this component has non-unique property types')
            props = dict([(prop.notation, prop) for prop in self.properties])
        else:
            props = {}
        return props

    def _okeys(self):
        return ['uri', 'com_type', 'requires',
                'mediator', 'components', 'properties']
        
    def __getattr__(self, key):
        if key in self._props().keys():
            result = self._props()[key]
        elif key in self._okeys():
            result = self.__dict__[key]
        else:
            msg = '{} object has no attribute "{}"'
            msg = msg.format(type(self).__name__, key)
            raise AttributeError(msg)
        return result

    def __contains__(self, key):
        if key in self._props().keys():
            res = True
        elif key in self._okeys():
            res = True
        else:
            res = False
        return res

    def __setattr__(self, key, value):
        if key in self._props().keys():
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
        fmt += '{components!r})'
        return fmt.format(self=self, cls=type(self).__name__,
                          properties=self.properties,
                          components=self.components)

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
        if self.com_type:
            nlabel = self.com_type.dot()
        else:
            nlabel = 'Component'
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
        for comp in self.components:
            comp.dot(graph, node, 'Component')
        return node

    @staticmethod
    def sparql_retriever(uri):
        qstr = '''SELECT ?component ?mediates ?requires ?com_type
                         ?subComponent ?property
        (GROUP_CONCAT(?acomponent; SEPARATOR='&') AS ?subComponent)
        (GROUP_CONCAT(?aproperty; SEPARATOR='&') AS ?property)
        (GROUP_CONCAT(?arequires; SEPARATOR='&') AS ?requires)
        WHERE {
        GRAPH <http://metarelate.net/concepts.ttl> {
            ?component rdf:type ?com_type .
            FILTER(?com_type != skos:Concept)
            OPTIONAL{?component mr:hasComponent ?acomponent .}
            OPTIONAL{?component mr:hasProperty ?aproperty .}
            OPTIONAL{?component dc:requires ?arequires .}
            OPTIONAL{?component dc:mediator ?mediates .}
            FILTER(?component = %s)
            FILTER(?type != mr:Component)
        }
            {SELECT ?component WHERE {
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?component rdf:type mr:Component .
            }}}
        }
        GROUP BY ?component ?mediates ?com_type
        ''' % uri
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        allowed_prefixes = set(('rdf:type', 'mr:hasComponent',
                                'mr:hasProperty', 'dc:requires',
                                'dc:mediator'))
        preds = set(po_dict)
        if not preds.issubset(allowed_prefixes):
            ec = '{} is not a subset of the allowed predicates set for '\
                 'a component record {}'
            ec = ec.format(preds, allowed_prefixes)
            raise ValueError(ec)
        subj_pref = 'http://www.metarelate.net/{}/component'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        search_string = ''
        n_propertys = 0
        n_components = 0
        n_reqs = 0
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if pred == 'dc:mediator' and len(po_dict[pred]) != 1:
                    ec = 'get_format_concept only accepts 1 dc:mediator statement'\
                         ' The po_dict in this case is not valid {} '
                    ec = ec.format(str(po_dict))
                    raise ValueError(ec)
                elif pred == 'dc:requires':
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
                        n_reqs +=1
                elif pred == 'mr:hasProperty':
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
                        n_propertys +=1
                elif pred == 'mr:hasComponent':
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
                        n_components +=1
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
                if pred == 'skos:member':
                    n_members =1
        if search_string != '':
            qstr = '''SELECT ?component ?type
            WHERE { {
            SELECT ?component ?type
            (COUNT(DISTINCT(?property)) AS ?propertys)
            (COUNT(DISTINCT(?subComponent)) AS ?subComponents)
            (COUNT(DISTINCT(?requires)) AS ?requireses)        
            WHERE{
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?component rdf:type ?type ;
                   %s .
            OPTIONAL { ?component  mr:hasProperty ?property . }
            OPTIONAL { ?component  mr:hasComponent ?subComponent . }
            OPTIONAL{?component dc:requires ?requires .}
            OPTIONAL{?component dc:mediator ?mediates .}
            FILTER(?type != mr:Component)
            }
            {SELECT ?component WHERE {
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?component rdf:type mr:Component .
            }}}
            }
            GROUP BY ?component ?type
            }
            FILTER(?subComponents = %i)
            FILTER(?propertys = %i)
            FILTER(?requireses = %i)
            }
            ''' % (search_string, n_components, n_propertys, n_reqs)
            sha1 = make_hash(po_dict)
            instr = '''INSERT DATA {
            GRAPH <http://metarelate.net/concepts.ttl> {
            <%s/%s> rdf:type mr:Component ;
                    %s
                    mr:saveCache "True" .
            }
            }
            ''' % (subj_pref, sha1, search_string)
        return qstr, instr

    def json_referrer(self):
        """
        return the data contents of the component instance ready for encoding
        as a json string

        """
        ## not updated yet
        if len(self) == 1 and self.uri.data == self.components[0].uri.data:
            prop_ref = self.components[0].json_referrer()
            prop_ref['rdf:type'] = self.com_type.data
            referrer = prop_ref
        else:
            referrer = {'component': self.uri.data,
                        prop_ref['rdf:type'] : self.com_type.data,
                        'mr:hasComponent': []}
            for comp in self.components:
                prop_ref = comp.json_referrer()
                referrer['mr:hasComponent'].append(prop_ref)
        return referrer

    def _podict(self):
        """
        Return a dictionary of predicates and objects for a rdf representation

        """
        podict = {}
        if self.com_type:
            podict['rdf:type'] = self.com_type.data
        if self.requires:
            podict['dc:requires'] = self.requires.data ## list
        if self.mediator:
            podict['dc:mediator'] = self.mediator.data
        podict = self._podict_elems(podict)
        return podict

    def _podict_elems(self, podict):
        podict['mr:hasComponent'] = []
        for comp in self.components:
            podict['mr:hasComponent'].append(comp.uri.data)
        podict['mr:hasProperty'] = []
        for aprop in self.properties:
            podict['mr:hasProperty'].append(aprop.uri.data)
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



# class PropertyComponent(Component):
#     """
#     A property component contains one or more uniquely named/typed
#     :class:`Property` members.

#     The property component provides dictionary style access to its
#     :class:`Property` members, keyed on the :data:`Property.name`.
#     Alternatively, attribute access via the member *name* is supported
#     as a convenience.

#     Note that, each :class:`Property` member must have a unique *name*/*type*.

#     A property component is deemed as either *simple* or *compound*:

#      * A property component is *simple* iff all its :class:`Property`
#        members are *simple*.
#      * A property component is *compound* iff it contains at least
#        one :class:`Property` member that is *compound*.

#     """
#     def __init__(self, uri, com_type, properties, requires=None, mediator=None):
#         self.uri = Item(uri)
#         self.com_type = Item(com_type)
#         self._data = {}
#         if isinstance(properties, Property) or \
#                 not isinstance(properties, Iterable):
#             properties = [properties]
#         if not len(properties):
#             msg = '{!r} object must contain at least one {!r}.'
#             raise ValueError(msg.format(type(self).__name__,
#                                         Property.__name__))
#         for prop in properties:
#             if not isinstance(prop, Property):
#                 msg = 'Expected a {!r} object, got {!r}.'
#                 raise TypeError(msg.format(Property.__name__,
#                                            type(prop).__name__))
#             if prop.ptype:
#                 self._data[prop.ptype] = prop
#             elif prop.name:
#                 self._data[prop.name] = prop

#     def __eq__(self, other):
#         result = NotImplemented
#         if isinstance(other, PropertyComponent):
#             result = False
#             if self.uri == other.uri and set(self.keys()) == set(other.keys()):
#                 for key in self.keys():
#                     if self[key] != other[key]:
#                         break
#                 else:
#                     result = True
#         return result

#     def __ne__(self, other):
#         result = self.__eq__(other)
#         if result is not NotImplemented:
#             result = not result
#         return result

#     def __getitem__(self, key):
#         result = None
#         for item in self._data.iterkeys():
#             if item == key:
#                 result = self._data[item]
#                 break
#         return result

#     def __contains__(self, key):
#         result = False
#         if isinstance(key, (Item, basestring)):
#             result = self[key] is not None
#         elif isinstance(key, Property):
#             result = key == self[key.name]
#         return result

#     def __repr__(self):
#         fmt = '{cls}({self.uri!r}, {self.com_type!r}, {properties!r})'
#         properties = sorted(self._data.values())
#         if len(properties) == 1:
#             properties, = properties
#         return fmt.format(self=self, cls=type(self).__name__,
#                           properties=properties)

#     @property
#     def simple(self):
#         return all([prop.simple for prop in self.itervalues()])

#     @property
#     def compound(self):
#         return not self.simple

#     def dot(self, graph, parent, name=None):
#         """
#         Generate a Dot digraph representation of this mapping component.

#         Args:
#          * graph:
#             The containing Dot graph.
#          * parent:
#             The parent Dot node of this componet.

#         Kwargs:
#          * name:
#             Name of the relationship between the nodes.

#         """
#         if parent.uri == self.uri.data:
#             # This component references one or more properties.
#             for prop in self.values():
#                 prop.dot(graph, parent, 'Property')
#         else:
#             # This component references another component.
#             label = self.dot_escape('{}_{}'.format(parent.uri, self.uri.data))
#             node = pydot.Node(label, label='Component',
#                               style='filled', peripheries='2',
#                               colorscheme='dark28', fillcolor='3',
#                               fontsize=8)
#             node.uri = self.uri.data
#             graph.add_node(node)
#             edge = pydot.Edge(parent, node,
#                               tailport='s', headport='n')
#             if name is not None:
#                 edge.set_label(self.dot_escape(name))
#                 edge.set_fontsize(7)
#             graph.add_edge(edge)
#             for prop in self.values():
#                 prop.dot(graph, node, 'Property')

#     def json_referrer(self):
#         """
#         return the data contents of the propertyComponent instance
#         ready for encoding as a json string

#         """
#         referrer = {'component': self.uri.data,
#                     'mr:hasProperty': []}
#         for item in self.itervalues():
#             referrer['mr:hasProperty'].append(item.json_referrer())
#         return referrer

#     def _podict_elems(self, podict):
#         if len(self) > 0:
#             podict['mr:hasProperty'] = []
#             for aproperty in self.values():
#                 podict['mr:hasProperty'].append(aproperty.uri.data)
#         return podict


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
    def __init__(self, uri=None, ptype=None, closematch=None, defby=None,
                 value=None, name=None, operator=None, component=None):
        self.uri = Item(uri)
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
        elif isinstance(value, str):
            new_value = '""'.format(value)
        elif isinstance(value, int) or isinstance(value, float):
            new_value = value
        else:
            msg = 'Invalid value, got {!r}.'
            raise TypeError(msg.format(type(value).__name__))
        self.value = new_value
        self.operator = Item(operator)
        self.component = Item(component)

    @property
    def notation(self):
        return self.ptype.notation

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
            podict['rdf:value'] = self.value.data
        if self.component:
            podict['mr:hasComponent'] = self.component.data
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

    def create_rdf(self, fuseki_process):
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

    def json_referrer(self):
        """
        return the data contents of the property instance ready for encoding
        as a json string

        """

        # to be updated!!
        referrer = {}
        referrer['property'] = self.uri.data
        referrer['mr:name'] = self.name.data
        if self.operator:
            referrer['mr:operator'] = self.operator.data
        if self.value:
            if self.simple:
                referrer['rdf:value'] = self.value.data
            else:
                referrer['mr:hasComponent'] = self.value.json_referrer()
        return referrer

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


class Item(_DotMixin, namedtuple('Item', 'data notation')):
    """
    Represents a mapping data item and associated skos notation in
    the form of an immutable named tuple.

    """
    def __new__(cls, data, notation=None):
        if data is None and notation is None:
            res = None
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
            uri = urlparse(uri)
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


class ValueMap(object):
    @staticmethod
    def sparql_retriever(uri):
        qstr = '''SELECT ?valueMap ?source ?target
        WHERE {
        GRAPH <http://metarelate.net/concepts.ttl> {
            ?valueMap mr:source ?source ;
                      mr:target ?target .
            FILTER(?valueMap = %s)
            }
        }
        ''' % uri
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        qstr = ''
        instr = ''
        allowed_preds = set(('mr:source','mr:target'))
        preds = set(po_dict)
        if not preds == allowed_preds:
            ec = '''{} is not a subset of the allowed predicates set
                    for a valueMap record
                    {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        subj_pref = 'http://www.metarelate.net/{}/valueMap'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        search_string = ''
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if len(po_dict[pred]) != 1:
                    ec = 'get_format_concept only accepts 1 mr:format statement }'
                    ec = ec.format(po_dict)
                    raise ValueError(ec)
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
        if search_string != '':
            qstr = '''SELECT ?valueMap 
            WHERE{
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?valueMap
                   %s .
            }
            }
            ''' % (search_string)
            sha1 = make_hash(po_dict)
            instr = '''INSERT DATA {
            GRAPH <http://metarelate.net/concepts.ttl> {
            <%s/%s> a mr:ValueMap ;
                    %s
                    mr:saveCache "True" .
            }
            }
            ''' % (subj_pref, sha1, search_string)
        return qstr, instr


class Value(object):
    @staticmethod
    def sparql_retriever(uri):
        qstr = '''SELECT ?value ?operator ?subject ?object
        WHERE {
        GRAPH <http://metarelate.net/concepts.ttl> {
            ?value mr:subject ?subject .
            OPTIONAL {?value mr:operator ?operator .}
            OPTIONAL {?value mr:object ?object . }
            FILTER(?value = %s)
            }
        }
        ''' % uri
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        qstr = ''
        instr = ''
        allowed_preds = set(('mr:operator','mr:subject', 'mr:object'))
        preds = set(po_dict)
        if not preds.issubset(allowed_preds):
            ec = '''{} is not a subset of the allowed predicates set
                    for a value record
                    {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        subj_pref = 'http://www.metarelate.net/{}/value'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        search_string = ''
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if len(po_dict[pred]) != 1:
                    ec = 'get_value only accepts 1 mr:format statement }'
                    ec = ec.format(po_dict)
                    raise ValueError(ec)
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
        if search_string != '':
            qstr = '''SELECT ?value
            WHERE{
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?value
                   %s .
            }
            }
            ''' % (search_string)
            sha1 = make_hash(po_dict)
            instr = '''INSERT DATA {
            GRAPH <http://metarelate.net/concepts.ttl> {
            <%s/%s> a mr:Value ;
                    %s
                    mr:saveCache "True" .
            }
            }
            ''' % (subj_pref, sha1, search_string)
        return qstr, instr


class ScopedProperty(object):
    @staticmethod
    def sparql_retriever(uri):
        qstr = '''SELECT ?scopedProperty ?scope ?hasProperty
        WHERE {
        GRAPH <http://metarelate.net/concepts.ttl> {
            ?scopedProperty mr:scope ?scope ;
                      mr:hasProperty ?hasProperty .
            FILTER(?scopedProperty = %s)
            }
        }
        ''' % uri
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        qstr = ''
        instr = ''
        allowed_preds = set(('mr:scope','mr:hasProperty'))
        preds = set(po_dict)
        if not preds == allowed_preds:
            ec = '''{} is not a subset of the allowed predicates set
                    for a scopedProperty record
                    {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        subj_pref = 'http://www.metarelate.net/{}/scopedProperty'
        subj_pref = subj_pref.format(site_config['fuseki_dataset'])
        search_string = ''
        for pred in po_dict:
            if isinstance(po_dict[pred], list):
                if len(po_dict[pred]) != 1:
                    ec = 'get_scopedProperty only accepts 1 mr:format statement {}'
                    ec = ec.format(po_dict)
                    raise ValueError(ec)
                else:
                    for obj in po_dict[pred]:
                        search_string += '''
                        %s %s ;''' % (pred, obj)
            else:
                search_string += '''
                %s %s ;''' % (pred, po_dict[pred])
        if search_string != '':
            qstr = '''SELECT ?scopedProperty
            WHERE{
            GRAPH <http://metarelate.net/concepts.ttl> {
            ?scopedProperty
                   %s .
            }
            }
            ''' % (search_string)
            sha1 = make_hash(po_dict)
            instr = '''INSERT DATA {
            GRAPH <http://metarelate.net/concepts.ttl> {
            <%s/%s> a mr:Property ;
                    %s
                    mr:saveCache "True" .
            }
            }
            ''' % (subj_pref, sha1, search_string)
        return qstr, instr


class Mediator(object):
    @staticmethod
    def sparql_retriever(uri=None, fformat=''):
        if fformat:
            ffilter = 'FILTER(?format = <http://www.metarelate.net/{ds}/format/{f}>)'
            ffilter = ffilter.format(ds=site_config['fuseki_dataset'], f=fformat)
        else:
            ffilter = ''
        urifilter = ''
        if uri is not None:
            urifilter = 'FILTER(?mediator = <{}>)'.format(uri)
        qstr = '''
        SELECT ?mediator ?label
        WHERE
        { GRAPH <http://metarelate.net/concepts.ttl> {
                      rdf:label ?label .
        %s
        %s
        } }
        ''' % (urifilter, ffilter)
        return qstr

    @staticmethod
    def sparql_creator(po_dict):
        allowed_preds = set(('rdf:type','rdf:label'))
        preds = set(po_dict)
        if not preds == allowed_preds:
            ec = '''{} is not a subset of the allowed predicates set
                    for a scopedProperty record
                    {}'''
            ec = ec.format(preds, allowed_preds)
            raise ValueError(ec)
        atype = po_dict['rdf:type']
        label = po_dict['rdf:label']
        ff = fformat.rstrip('>').split('/')[-1]
        med = '<http://www.metarelate.net/{ds}/mediates/{f}/{l}>'
        med = med.format(ds=site_config['fuseki_dataset'], f=ff, l=label)
        qstr = '''
        SELECT ?mediator
        WHERE
        { GRAPH <http://metarelate.net/concepts.ttl> {
        %s a mr:Mediator, {} ;
             rdf:label "%s" ;
             .
             } }
        ''' % (med, atype, label)
        instr = '''
        INSERT DATA
        { GRAPH <http://metarelate.net/concepts.ttl> {
        %s a mr:Mediator, {} ;
             rdf:label "%s" ;
             mr:saveCache "True" .
             } }
        ''' % (med, atype, label)
        return qstr, instr


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
            pred_elems = pred.split(':')
            if len(pred_elems) == 2:
                if pre.has_key(pred_elems[0]):
                    predicate = '%s%s' % (pre[pred_elems[0]], pred_elems[1])
                else:
                    raise ValueError('predicate not in prefixes.py')
            else:
                raise ValueError('make hash passed a predicate '
                                 'which is not of the form <prefix>:<item>')
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
