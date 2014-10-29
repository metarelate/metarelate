# (C) British Crown Copyright 2011 - 2013, Met Office
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

from collections import deque
import glob
import json
import os
from Queue import Queue
import socket
import subprocess
import sys
from threading import Thread
import time
import urllib
import urllib2

import requests

import metarelate
import metarelate.prefixes as prefixes

HEADER = '''#(C) British Crown Copyright 2012 - 2014 , Met Office 
#
# This file is part of metOcean.
#
# metOcean is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# metOcean distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with metOcean.  If not, see <http://www.gnu.org/licenses/>.
'''

PRE = prefixes.Prefixes()

# maximum number of threads for multi-thrteading code
MAXTHREADS = 4

# Configure the Apache Jena environment.
if metarelate.site_config.get('jena_dir') is not None:
    os.environ['JENAROOT'] = metarelate.site_config['jena_dir']
else:
    msg = 'The Apache Jena semantic web framework has not been configured ' \
        'for metarelate.'
    raise ValueError(msg)

# Configure the Apache Fuseki environment.
if metarelate.site_config.get('fuseki_dir') is not None:
    os.environ['FUSEKI_HOME'] = metarelate.site_config['fuseki_dir']
else:
    msg = 'The Apache Fuseki SPARQL server has not been configured ' \
        'for metarelate.'
    raise ValueError(msg)


class WorkerThread(Thread):
    """
    A :class:threading.Thread which moves objects from an input queue to an
    output deque using a 'dowork' method, as defined by a subclass.

    """
    def __init__(self, aqueue, adeque, fu_p):
        self.queue = aqueue
        self.deque = adeque
        self.fuseki_process = fu_p
        Thread.__init__(self)
        self.daemon = True
    def run(self):
        while not self.queue.empty():
            resource = self.queue.get()
            try:
                self.dowork(resource)
                self.deque.append(resource)
            except Exception, e:
                print e
            self.queue.task_done()

class MappingPopulateWorker(WorkerThread):
    """
    WorkerThread for populating a Mapping instance from its URI.
    """
    def dowork(self, resource):
        resource.populate_from_uri(self.fuseki_process)


class FusekiServer(object):
    """
    A class to represent an instance of a process managing
    an Apache Jena triple store database and Fuseki SPARQL server.
    
    """
    def __init__(self, host='localhost', test=False):

        self._jena_dir = metarelate.site_config['jena_dir']
        self._fuseki_dir = metarelate.site_config['fuseki_dir']

        static_key = 'static_dir'
        tdb_key = 'tdb_dir'
        if test:
            static_key = 'test_{}'.format(static_key)
            tdb_key = 'test_{}'.format(tdb_key)
        
        if metarelate.site_config.get(static_key) is None:
            msg = 'The {}static data directory for the Apache Jena database' \
                'has not been configured for metarelate.'
            raise ValueError(msg.format('test ' if test else ''))
        else:
            self._static_dir = metarelate.site_config[static_key]

        if metarelate.site_config.get(tdb_key) is None:
            msg = 'The Apache Jena {}triple store database directory has not ' \
                'been configured for metarelate.'
            raise ValueError(msg.format('test ' if test else ''))
        else:
            self._tdb_dir = metarelate.site_config[tdb_key]
        
        self._fuseki_dataset = metarelate.site_config['fuseki_dataset']
        if test:
            self._fuseki_dataset = 'test'

        port_key = 'port'
        if test:
            port_key = 'test_{}'.format(port_key)
        self.port = metarelate.site_config[port_key]

        self.host = host
        self.test = test
        self._process = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
        
    def start(self):
        """
        Initialise the Apache Fuseki SPARQL server process on the configured
        port, using the configured Apache Jena triple store database.
        
        """
        if not self.alive():
            nohup_dir = metarelate.site_config['log_dir']
            if self.test and \
                os.access(metarelate.site_config['test_dir'], os.W_OK):
                    nohup_dir = metarelate.site_config['test_dir']
            nohup_file = os.path.join(nohup_dir, 'nohup.out')
            if os.path.exists(nohup_file):
                os.remove(nohup_file)
            cwd = os.getcwd()
            os.chdir(nohup_dir)
            args = ['nohup',
                    os.path.join(self._fuseki_dir, 'fuseki-server'),
                    '--loc={}'.format(self._tdb_dir),
                    '--update',
                    '--port={}'.format(self.port),
                    '/{}'.format(self._fuseki_dataset)]
            self._process = subprocess.Popen(args)
            os.chdir(cwd)
            for attempt in xrange(metarelate.site_config['timeout_attempts']):
                if self.alive():
                    break
                time.sleep(metarelate.site_config['timeout_sleep'])
            else:
                msg = 'The metarelate Apache Fuseki SPARQL server failed ' \
                    'to start.'
                raise RuntimeError(msg)

    def stop(self, save=False):
        """
        Shutdown the metarelate Apache Fuseki SPARQL server.

        Kwargs:
         * save:
            Save any cache results to the configured Apache Jena triple
            store database.
            
        """
        if save:
            self.save()
        if self.alive():
            pid = self._process.pid
            self._process.terminate()
            for attempt in xrange(metarelate.site_config['timeout_attempts']):
                if not self.alive():
                    break
                time.sleep(metarelate.site_config['timeout_sleep'])
            else:
                msg = 'The metarelate Apache Fuseki SPARQL server failed ' \
                    'to shutdown, PID={}.'
                raise RuntimeError(msg.format(pid))
                             
            self._process = None

    def restart(self):
        """
        Restart the metarelate Apache Fuseki SPARQL server.

        """
        self.stop()
        self.start()

    def alive(self):
        """
        Determine whether the Apache Fuseki SPARQL server is available
        on the configured port.

        Returns:
            Boolean.

        """
        result = False
        s = socket.socket() 
        try: 
            s.connect((self.host, self.port))
            s.close()
            result = True
        except socket.error:
            pass
        if result and self._process is None:
            msg = 'There is currently another service on port {!r}.'
            raise RuntimeError(msg.format(self.port))
        return result

    def clean(self):
        """
        Delete all of the files in the configured Apache Jena triple
        store database.

        """
        if self.alive():
            self.stop()
        files = os.path.join(self._tdb_dir, '*')
        for tdb_file in glob.glob(files):
            os.remove(tdb_file)
        return glob.glob(files)

    def save(self):
        """
        write out all saveCache flagged changes in the metarelate graph,
        appending to the relevant ttl files
        remove saveCache flags after saving
        
        """
        
        main_graph = metarelate.site_config['graph']
        files = os.path.join(self._static_dir, main_graph, '*.ttl')
        for subgraph in glob.glob(files):
            graph = 'http://%s/%s' % (main_graph, subgraph.split('/')[-1])
            save_string = self.save_cache(graph)
            if save_string:
                with open(subgraph, 'w') as sg:
                    sg.write(HEADER)
                    for line in save_string.splitlines():
                        sg.write(line + '\n')

    def save_cache(self, graph, debug=False):
        """
        export new records from a graph in the triple store to an external location,
        as flagged by the manager application
        clear the 'not saved' flags on records, updating a graph in the triple store
        with the fact that changes have been persisted to ttl

        """
        nstr = '''
        SELECT ?s ?p ?o
        WHERE {
        GRAPH <%s>
        {
        ?s ?p ?o ;
            mr:saveCache "True" .
        }
        } 
        ''' % graph
        n_res = self.run_query(nstr)
        delstr = '''
        DELETE
        {  GRAPH <%s>
            {
            ?s mr:saveCache "True" .
            }
        }
        WHERE
        {  GRAPH <%s>
            {
        ?s ?p ?o ;
            mr:saveCache "True" .
            }
        } 
        ''' % (graph,graph)
        delete_results = self.run_query(delstr, update=True, debug=debug)
        qstr = '''
        SELECT
            ?s ?p ?o
        WHERE
        {
        GRAPH <%s>
        {
        ?s ?p ?o .
        }
        }
        order by ?s ?p ?o
        ''' % graph
        results = self.run_query(qstr, debug=debug)
        save_string = ''
        save_out = []
        if n_res:
            subj = ''
            for res in results:
                if res['s'] == subj:
                    save_out.append('\t{} {} ;'.format(res['p'], res['o']))
                elif subj == '':
                    subj = res['s']
                    save_out.append('\n{}\n\t{} {} ;'.format(res['s'],
                                                               res['p'],
                                                               res['o']))
                else:
                    subj = res['s']
                    save_out.append('\t.\n\n{}\n\t{} {} ;'.format(res['s'],
                                                               res['p'],
                                                               res['o']))
            save_string = '\n'.join(save_out)
        return save_string


    def revert(self):
        """
        identify all cached changes in the metarelate graph
        and remove them, reverting the TDB to the same state
        as the saved ttl files
        
        """
        qstr = '''
        DELETE
        {  GRAPH <%s>
            {
            ?s ?p ?o .
            }
        }
        WHERE
        {  GRAPH <%s>
            {
            ?s ?p ?o ;
            mr:saveCache "True" .
            }
        } 
        '''
        main_graph = metarelate.site_config['graph']
        files = os.path.join(self._static_dir, main_graph, '*.ttl')
        for infile in glob.glob(files):
            ingraph = infile.split('/')[-1]
            graph = 'http://%s/%s' % (main_graph, ingraph)
            qstring = qstr % (graph, graph)
            revert_string = self.run_query(qstring, update=True)

    def query_cache(self):
        """
        identify all cached changes in the metarelate graph

        """
        qstr = '''
        SELECT ?s ?p ?o
        WHERE
        {  GRAPH <%s>
            {
        ?s ?p ?o ;
            mr:saveCache "True" .
            }
        } 
        '''
        results = []
        main_graph = metarelate.site_config['graph']
        files = os.path.join(self._static_dir, main_graph, '*.ttl')
        for infile in glob.glob(files):
            ingraph = infile.split('/')[-1]
            graph = 'http://%s/%s' % (main_graph, ingraph)
            query_string = qstr % (graph)
            result = self.run_query(query_string)
            results = results + result
        return results


    def load(self):
        """
        Load all the static data turtle files into the new Apache Jena
        triple store database.

        """
        self.clean()
        graphs = os.path.join(self._static_dir, 'metarelate.net')
        for ingraph in glob.glob(graphs):
            graph = ingraph.split('/')[-1]
            if os.path.exists(os.path.join(ingraph, 'getCodes.py')):
                subprocess.check_call(['python', os.path.join(ingraph, 'getCodes.py')])
            subgraphs = os.path.join(ingraph, '*.ttl')
            for insubgraph in glob.glob(subgraphs):
                subgraph = insubgraph.split('/')[-1]
                tdb_load = [os.path.join(self._jena_dir, 'bin/tdbloader'),
                            '--graph=http://{}/{}'.format(graph, subgraph),
                            '--loc={}'.format(self._tdb_dir),
                            insubgraph]
                print ' '.join(tdb_load)
                subprocess.check_call(tdb_load)

    def validate(self):
        """
        run the validation queries

        """
        failures = {}
        mm_string = ('The following mappings are ambiguous, providing multiple'
                    ' targets in the same format for a particular source')
        failures[mm_string] = self.run_query(multiple_mappings())
        invalid_vocab = 'The following mappings contain an undeclared URI'
        failures[invalid_vocab] = self.run_query(valid_vocab())
        return failures

    def run_query(self, query_string, output='json', update=False, debug=False):
        """
        run a query_string on the FusekiServer instance
        return the results
        
        """
        if not self.alive():
            self.restart()
        pref = prefixes.Prefixes().sparql
        baseurl = "http://{}:{}/{}/".format(self.host, self.port,
                                           self._fuseki_dataset)
        if update:
            action='update'
            qparams={'update': pref+query_string}
            url = baseurl + action
            results = requests.post(url, proxies={'http':''},
                                    data=qparams)
        else:
            action = 'query'
            qparams={'query': pref+query_string, 'output': 'json'}
            url = baseurl + action
            results = requests.get(url, proxies={'http':''},
                                   params=qparams)
        if results.status_code != 200:
            msg = ('Error connection to Fuseki server on {}.\n'
                  ' server returned {}\n'
                  '{}\n{}')
            msg = msg.format(url, results.status_code,
                             pref, query_string)
            raise RuntimeError(msg)
        if output == 'json':
            return process_data(results.text)
        else:
            return results.text

    def get_contacts(self, register, debug=False):
        """
        return a list of contacts from the tdb which are part of the named register

        """
        qstr = '''
        SELECT ?s ?prefLabel ?def
        WHERE
        { GRAPH <http://metarelate.net/contacts.ttl> {
            ?s skos:inScheme <http://www.metarelate.net/%s/%s> ;
               skos:prefLabel ?prefLabel ;
               skos:definition ?def ;
               dc:valid ?valid .
        } }
        ''' % (self._fuseki_dataset, register)
        results = self.run_query(qstr, debug=debug)
        return results

    def subject_and_plabel(self, graph, debug=False):
        """
        selects subject and prefLabel from a particular graph

        """
        qstr = '''
            SELECT ?subject ?prefLabel ?notation
            WHERE {
                GRAPH <%s> {
                ?subject skos:notation ?notation .
                OPTIONAL {?subject skos:prefLabel ?prefLabel . }}
            }
            ORDER BY ?subject
        ''' % graph
        results = self.run_query(qstr, debug=debug)
        return results

    def retrieve_mappings(self, sourcetype, targettype):
        """
        return the format specific mappings for a particular source
        and target component type

        """
        if not isinstance(sourcetype, metarelate.Item):
            sourcetype = metarelate.Item(sourcetype)
        if not isinstance(targettype, metarelate.Item):
            targettype = metarelate.Item(targettype)
        if not (sourcetype.is_uri() and targettype.is_uri()):
            raise ValueError('sourcetype and targettype must both be URIs')

        qstr = ('SELECT ?mapping ?source ?target ?invertible ?inverted '
                '''(GROUP_CONCAT(DISTINCT(?valueMap); SEPARATOR = '&') AS ?valueMaps) '''
                'WHERE {  '
                'GRAPH <http://metarelate.net/mappings.ttl> { { '
                '?mapping mr:source ?source ; '
                'mr:target ?target ; '
                'mr:invertible ?invertible .'
                'BIND("False" AS ?inverted) '
                'OPTIONAL {?mapping mr:hasValueMap ?valueMap . } '
                'MINUS {?mapping ^dc:replaces+ ?anothermap} '
                '} UNION { '
                '?mapping mr:source ?target ; '
                '         mr:target ?source ; '
                '         mr:invertible "True" . '
                'BIND("True" AS ?inverted) '
                'BIND("True" AS ?invertible) '
                'OPTIONAL {?mapping mr:hasValueMap ?valueMap . } '
                'MINUS {?mapping ^dc:replaces+ ?anothermap} '
                '} } '
                'GRAPH <http://metarelate.net/concepts.ttl> { '
                '?source rdf:type %s . '
                '?target rdf:type %s . '
                '}} '
                'GROUP BY ?mapping ?source ?target ?inverted ?invertible '
                'ORDER BY ?mapping') % (sourcetype.data, targettype.data)
        map_templates = self.run_query(qstr)
        mapping_list = deque()
        mapping_queue = Queue()
        mq = 0
        for mt in map_templates:
            mapping_queue.put(metarelate.Mapping(mt.get('mapping'),
                                                 invertible=mt.get('invertible'),
                                                 inverted=mt.get('inverted')))
            mq += 1
        for i in range(MAXTHREADS):
            MappingPopulateWorker(mapping_queue, mapping_list, self).start()
        mapping_queue.join()
        if len(mapping_list) != mq:
            msg = '{} entries in mapping_list, expected {}'
            raise ValueError(msg.format(len(mapping_list), mq))
        return mapping_list

    def retrieve(self, qstr, debug=False):
        """
        Return a record from the provided id
        or None if one does not exist.

        """
        results = self.run_query(qstr, debug=debug)
        if len(results) == 0:
            fCon = None
        elif len(results) >1:
            raise ValueError('{} is a malformed component'.format(results))
        else:
            fCon = results[0]
        return fCon

    def create(self, qstr, instr, debug=False):
        """obtain a json representation of a defined type
        either by retrieving or creating it
        qstr is a SPARQL query string 
        instr is a SPARQL insert string
        """
        results = self.run_query(qstr, debug=debug)
        if len(results) == 0:
            insert_results = self.run_query(instr, update=True, debug=debug)
            results = self.run_query(qstr, debug=debug)
        if len(results) == 1:
            results = results[0]
        else:
            ec = '{} results returned, one expected'.format(len(results))
            raise ValueError(ec)
        return results

    def find_valid_mapping(self, source, target):
        """
        Returns a mapping instance which links the source to the target,
        or None, or an error if multiple mappings exist

        Args:
        source : a metarelate component, or None
        target : a metarelate component, or None

        """
        if source is None:
            source_uri = '?s'
        elif not isinstance(source, metarelate.Component):
            raise ValueError('source must be ametarelate Component or None')
        if target is None:
            target_uri = '?t'
        elif not isinstance(target, metarelate.Component):
            raise ValueError('target must be ametarelate Component or None')
        result = None
        if source is not None:
            source_qstr, sinstr = source.creation_sparql()
            source_uri = self.run_query(source_qstr)
            if len(source_uri) > 1:
                raise ValueError('Source Component exists in duplicate in store')
            elif source_uri:
                source_uri = source_uri[0]['component']
                if source.uri.data != source_uri:
                    raise ValueError('Source Component URI is different from '
                                     'a duplicate Component in the store')
        if target is not None:
            target_qstr, instr = target.creation_sparql()
            target_uri = self.run_query(target_qstr)
            if len(target_uri) > 1:
                raise ValueError('Target Component exists in duplicate in store')
            elif target_uri:
                target_uri = target_uri[0]['component']
                if target.uri.data != target_uri:
                    raise ValueError('Target Component URI is different from '
                                     'a duplicate Component in the store')
        if source_uri and target_uri:
            map_qstr = ('SELECT ?mapping \n'
                        'WHERE { \n'
                        'GRAPH <http://metarelate.net/mappings.ttl> { \n'
                        '?mapping mr:source %s ;\n'
                        '\tmr:target %s .\n'
                        'OPTIONAL {?mapping dc:replaces ?replaces .}\n'
                        'MINUS {?mapping ^dc:replaces+ ?anothermap} \n'
                        '}}' % (source_uri, target_uri)) 
            map_ids = self.run_query(map_qstr)
            if len(map_ids) > 1:
                raise ValueError('multiple valid mapping for the same source'
                                 ' and target')
            elif map_ids:
                result = map_ids[0]
        return result
                



def process_data(jsondata):
    """ helper method to take JSON output from a query and return the results"""
    resultslist = []
    try:
        jdata = json.loads(jsondata)
    except (ValueError, TypeError):
        return resultslist
    vars = jdata['head']['vars']
    data = jdata['results']['bindings']
    for item in data:
        tmpdict = {}
        for var in vars:
            tmpvar = item.get(var)
            if tmpvar:
                val = tmpvar.get('value')
                if str(val).startswith('http://') or \
                   str(val).startswith('https://') :
                    if len(val.split('&')) == 1:
                        val = '<{}>'.format(val)
                    else:
                        val = ['<{}>'.format(v) for v in val.split('&')]
                else:
                    try:
                        int(val)
                    except ValueError:
                        try:
                            float(val)
                        except ValueError:
                            if not val.startswith('<'):
                                val = '"{}"'.format(val)
                tmpdict[var] = val
        if tmpdict != {}:
            resultslist.append(tmpdict)
    return resultslist

def multiple_mappings(test_source=None):
    """
    returns all the mappings which map the same source to a different target
    where the targets are the same format
    filter to a single test mapping with test_map
    
    """
    tm_filter = ''
    if test_source:
        pattern = '<http.*>'
        pattern = re.compile(pattern)
        if pattern.match(test_source):
            tm_filter = '\n\tFILTER(?asource = {})'.format(test_source)
    qstr = '''SELECT ?amap ?asource ?atarget ?bmap ?bsource ?btarget
    (GROUP_CONCAT(DISTINCT(?value); SEPARATOR='&') AS ?signature)
    WHERE {
    GRAPH <http://metarelate.net/mappings.ttl> { {
    ?amap mr:source ?asource ;
         mr:target ?atarget . } 
    UNION 
        { 
    ?amap mr:invertible "True" ;
         mr:target ?asource ;
         mr:source ?atarget . } 
    MINUS {?amap ^dc:replaces+ ?anothermap} %s
    } 
    GRAPH <http://metarelate.net/mappings.ttl> { {
    ?bmap mr:source ?bsource ;
         mr:target ?btarget . } 
    UNION  
        { 
    ?bmap mr:invertible "True" ;
         mr:target ?bsource ;
         mr:source ?btarget . } 
    MINUS {?bmap ^dc:replaces+ ?bnothermap}
    filter (?bmap != ?amap)
    filter (?bsource = ?asource)
    filter (?btarget != ?atarget)
    } 
    GRAPH <http://metarelate.net/concepts.ttl> {
    ?asource rdf:type ?asourceformat .
    ?bsource rdf:type ?bsourceformat .
    ?atarget rdf:type ?atargetformat .
    ?btarget rdf:type ?btargetformat .
    }
    filter (?btargetformat = ?atargetformat)

    OPTIONAL { GRAPH <http://metarelate.net/formats.ttl> {
    ?atargetformat <http://www.metarelate.net/vocabulary/index.html#subFormat> ?asubtargetpref .
    ?btargetformat <http://www.metarelate.net/vocabulary/index.html#subFormat> ?bsubtargetpref .
    } 
    GRAPH <http://metarelate.net/concepts.ttl> {
    ?atarget mr:hasProperty ?asubprop .
    ?asubprop mr:name ?asubtargetpref ;
          rdf:value ?asubswitch .
    ?btarget mr:hasProperty ?bsubprop .
    ?bsubprop mr:name ?bsubtargetpref ;
          rdf:value ?bsubswitch .
    } }
    filter (?asubswitch = ?bsubswitch)

    GRAPH <http://metarelate.net/concepts.ttl> { {
    ?asource mr:hasProperty ?prop . }
    UNION {
    ?atarget mr:hasProperty ?prop . }
    UNION {
    ?asource mr:hasComponent|mr:hasProperty ?prop . }
    UNION {
    ?atarget mr:hasComponent|mr:hasProperty ?prop . }
    UNION { 
    ?asource mr:hasProperty|mr:hasComponent|mr:hasProperty ?prop . }
    UNION { 
    ?atarget mr:hasProperty|mr:hasComponent|mr:hasProperty ?prop . }
    OPTIONAL { ?prop rdf:value ?value . }
    } }
    GROUP BY ?amap ?asource ?atarget ?bmap ?bsource ?btarget
    ORDER BY ?asource
    ''' % tm_filter
    return qstr

