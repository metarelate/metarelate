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


import glob
import json
import os
import socket
import subprocess
import sys
import time
import urllib
import urllib2

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
        graphs = os.path.join(self._static_dir, '*')
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
        mm_string = 'The following mappings are ambiguous, providing multiple '\
                    'targets in the same format for a particular source'
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
        # use null ProxyHandler to ignore proxy for localhost access
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
        pre = prefixes.Prefixes()
        if debug == True:
            k=0
            for j, line in enumerate(pre.sparql.split('\n')):
                print j,line
                k+=1
            for i, line in enumerate(query_string.split('\n')):
                print i+k, line
        if update:
            action = 'update'
            qstr = urllib.urlencode([
                (action, "%s %s" % (pre.sparql, query_string))])
        else:
            action = 'query'
            qstr = urllib.urlencode([
                (action, "%s %s" % (pre.sparql, query_string)),
                ("output", output),
                ("stylesheet","/static/xml-to-html-links.xsl")])
        BASEURL = "http://%s:%i%s/%s?" % (self.host, self.port,
                                          '/{}'.format(self._fuseki_dataset)
                                          , action)
        data = ''
        try:
            data = opener.open(urllib2.Request(BASEURL), qstr).read()
        except urllib2.URLError as err:
            ec = 'Error connection to Fuseki server on {}.\n server returned {}'
            ec = ec.format(BASEURL, err)
            raise RuntimeError(ec)
        if output == "json":
            return process_data(data)
        elif output == "text":
            return data
        else:
            return data

    def get_label(self, subject, debug=False):
        """
        return the skos:notation for a subject, if it exists

        """
        subject = str(subject)
        if not subject.startswith('<') and not subject.startswith('"'):
            subj_str = '"{}"'.format(subject)
        else:
            subj_str = subject
        qstr = ''' SELECT ?notation 
        WHERE { {'''
        for graph in _vocab_graphs():
            qstr += '\n\tGRAPH %s {' % graph
            qstr += '\n\t?s skos:notation ?notation . }}\n\tUNION {'
        qstr = qstr.rstrip('\n\tUNION {')
        qstr += '\n\tFILTER(?s = %(sub)s) }' % {'sub':subj_str}
        results = self.run_query(qstr, debug=debug)
        if len(results) == 0:
            hash_split = subject.split('#')
            if len(hash_split) == 2 and hash_split[1].endswith('>'):
                label = hash_split[1].rstrip('>')
            else:
                # raise ValueError('{} returns no notation'.format(subject))
                label = subject
        elif len(results) >1:
            raise ValueError('{} returns multiple notation'.format(subject))
        else:
            label = results[0]['notation']
        return label

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

    def retrieve_mappings(self, source, target):
        """
        return the format specific mappings for a particular source
        and target format

        """
        if isinstance(source, basestring) and \
                not metarelate.Item(source).is_uri():
            s_str = '<http://www.metarelate.net/{ds}/format/{s}>'
            source = s_str.format(ds=self._fuseki_dataset, s=source.lower())
        if isinstance(target, basestring) and \
                not metarelate.Item(target).is_uri():
            t_str = '<http://www.metarelate.net/{ds}/format/{t}>'
            target = t_str.format(ds=self._fuseki_dataset, t=target.lower())
        qstr = '''
        SELECT ?mapping ?source ?sourceFormat ?target ?targetFormat ?inverted
        (GROUP_CONCAT(DISTINCT(?valueMap); SEPARATOR = '&') AS ?valueMaps)
        WHERE { 
        GRAPH <http://metarelate.net/mappings.ttl> { {
        ?mapping mr:source ?source ;
                 mr:target ?target ;
                 mr:status ?status .
        BIND("False" AS ?inverted)
        OPTIONAL {?mapping mr:hasValueMap ?valueMap . }
        FILTER (?status NOT IN ("Deprecated", "Broken"))
        MINUS {?mapping ^dc:replaces+ ?anothermap}
        }
        UNION {
        ?mapping mr:source ?target ;
                 mr:target ?source ;
                 mr:status ?status ;
                 mr:invertible "True" .
        BIND("True" AS ?inverted)
        OPTIONAL {?mapping mr:hasValueMap ?valueMap . }
        FILTER (?status NOT IN ("Deprecated", "Broken"))
        MINUS {?mapping ^dc:replaces+ ?anothermap}
        } }
        GRAPH <http://metarelate.net/concepts.ttl> { 
        ?source mr:hasFormat %s .
        ?target mr:hasFormat %s .
        }
        }
        GROUP BY ?mapping ?source ?sourceFormat ?target ?targetFormat ?inverted
        ORDER BY ?mapping

        ''' % (source, target)
        mappings = self.run_query(qstr)
        mapping_list = []
        for mapping in mappings:
            mapping_list.append(self.structured_mapping(mapping))
        return mapping_list

    def _retrieve_component(self, uri, base=True):
        qstr = metarelate.Component.sparql_retriever(uri)
        qcomp = self.retrieve(qstr)
        if qcomp is None:
            msg = 'Cannot retrieve URI {!r} from triple-store.'
            raise ValueError(msg.format(uri))
        for key in ['property', 'subComponent']:
            if qcomp.get(key) is None:
                qcomp[key] = []
            if isinstance(qcomp[key], basestring):
                qcomp[key] = [qcomp[key]]
        if qcomp['property']:
            properties = []
            for puri in qcomp['property']:
                qstr = metarelate.Property.sparql_retriever(puri)
                qprop = self.retrieve(qstr)
                name = qprop['name']
                name = metarelate.Item(name, self.get_label(name))
                curi = qprop.get('component')
                if curi is not None:
                    value = self._retrieve_component(curi, base=False)
                else:
                    value = qprop.get('value')
                    if value is not None:
                        value = metarelate.Item(value, self.get_label(value))
                    op = qprop.get('operator')
                    if op is not None:
                        op = metarelate.Item(op, self.get_label(op))
                properties.append(metarelate.Property(puri, name, value, op))
            result = metarelate.PropertyComponent(uri, properties)
        ## this bit needs fixing
        if qcomp['subComponent']:
            components = []
            for curi in qcomp['subComponent']:
                components.append(self._retrieve_component(curi, base=False))
            if base:
                result = components
            else:
                result = metarelate.Component(uri, components)
        if base:
            scheme = qcomp['format']
            scheme = metarelate.Item(scheme, self.get_label(scheme))
            result = metarelate.Component(uri, scheme=scheme, components=result)
        return result

    def _retrieve_value_map(self, valmap_id, inv):
        """
        returns a dictionary of valueMap information
        
        """
        if inv == '"False"':
            inv = False
        elif inv == '"True"':
            inv = True
        else:
            raise ValueError('inv = {}, not "True" or "False"'.format(inv))
        value_map = {'valueMap':valmap_id, 'mr:source':{}, 'mr:target':{}}
        qstr = metarelate.ValueMap.sparql_retriever(valmap_id)
        vm_record = self.retrieve(qstr)
        if inv:
            value_map['mr:source']['value'] = vm_record['target']
            value_map['mr:target']['value'] = vm_record['source']
        else:
            value_map['mr:source']['value'] = vm_record['source']
            value_map['mr:target']['value'] = vm_record['target']
        for role in ['mr:source', 'mr:target']:
            value_map[role] = self._retrieve_value(value_map[role]['value'])

        return value_map

    def _retrieve_value(self, val_id):
        """
        returns a dictionary from a val_id
        
        """
        value_dict = {'value':val_id}
        qstr = metarelate.Value.sparql_retriever(val_id)
        val = self.retrieve(qstr)
        for key in val.keys():
            value_dict['mr:{}'.format(key)] = val[key]
        for sc_prop in ['mr:subject', 'mr:object']:
            pid = value_dict.get(sc_prop)
            if pid:
                qstr = metarelate.ScopedProperty.sparql_retriever(pid)
                prop = self.retrieve(qstr)
                if prop:
                    value_dict[sc_prop] = {}
                    for pkey in prop:
                        pv = prop[pkey]
                        value_dict[sc_prop]['mr:{}'.format(pkey)] = pv
                        if pkey == 'hasProperty':
                            pr = value_dict[sc_prop]['mr:{}'.format(pkey)]
                            qstr = metarelate.Property.sparql_retriever(pr)
                            aprop = self.retrieve(qstr)
                            value_dict[sc_prop]['mr:{}'.format(pkey)] = {'property':pv}
                            for p in aprop:
                                value_dict[sc_prop]['mr:{}'.format(pkey)]['mr:{}'.format(p)] = aprop[p]
                elif pid.startswith('<http://www.metarelate.net/{}/value/'.format(self._fuseki_dataset)):
                    newval = self._retrieve_value(pid)
                    value_dict[sc_prop] = newval
                else:
                    value_dict[sc_prop] = pid
        return value_dict

    def structured_mapping(self, template):
        uri = template['mapping']
        source = self._retrieve_component(template['source'])
        target = self._retrieve_component(template['target'])
        return metarelate.Mapping(uri, source, target)
    
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

    def mapping_by_properties(self, prop_list):
        results = self.run_query(mapping_by_properties(prop_list))
        mapping = None
        maps = set([r['mapping'] for r in results])
        if not mapping:
            mappings = maps
        else:
            mappings.intersection_update(maps)
        return mappings


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
                    # val = ['<{}>'.format(v) for v in val.split('&')]
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
    ?amap mr:status ?astatus ;
         mr:source ?asource ;
         mr:target ?atarget . } 
    UNION 
        { 
    ?amap mr:invertible "True" ;
         mr:status ?astatus ;
         mr:target ?asource ;
         mr:source ?atarget . } 
    FILTER (?astatus NOT IN ("Deprecated", "Broken"))
    MINUS {?amap ^dc:replaces+ ?anothermap} %s
    } 
    GRAPH <http://metarelate.net/mappings.ttl> { {
    ?bmap mr:status ?bstatus ;
         mr:source ?bsource ;
         mr:target ?btarget . } 
    UNION  
        { 
    ?bmap mr:invertible "True" ;
         mr:status ?bstatus ;
         mr:target ?bsource ;
         mr:source ?btarget . } 
    FILTER (?bstatus NOT IN ("Deprecated", "Broken"))
    MINUS {?bmap ^dc:replaces+ ?bnothermap}
    filter (?bmap != ?amap)
    filter (?bsource = ?asource)
    filter (?btarget != ?atarget)
    } 
    GRAPH <http://metarelate.net/concepts.ttl> {
    ?asource mr:hasFormat ?asourceformat .
    ?bsource mr:hasFormat ?bsourceformat .
    ?atarget mr:hasFormat ?atargetformat .
    ?btarget mr:hasFormat ?btargetformat .
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


def valid_vocab():
    """
    find all valid mapping and every property they reference

    """
    qstr = '''
    SELECT DISTINCT  ?amap 
    (GROUP_CONCAT(DISTINCT(?vocab); SEPARATOR = '&') AS ?signature)
    WHERE {      
    GRAPH <http://metarelate.net/mappings.ttl> { {  
    ?amap mr:status ?astatus ; 
    FILTER (?astatus NOT IN ("Deprecated", "Broken")) 
    MINUS {?amap ^dc:replaces+ ?anothermap}      }
    { 
    ?amap mr:source ?fc .      }
    UNION {
    ?amap mr:target ?fc .      } } 
    GRAPH <http://metarelate.net/concepts.ttl> { {
    ?fc mr:hasProperty ?prop . }
    UNION {
    ?fc mr:hasComponent|mr:hasProperty ?prop . }
    UNION { 
    ?fc mr:hasProperty|mr:hasComponent|mr:hasProperty ?prop .
    }
    { ?prop mr:name ?vocab . }
    UNION {
    ?prop mr:operator ?vocab . }
    UNION {
    ?prop rdf:value ?vocab . }
    FILTER(ISURI(?vocab))
    FILTER(!regex(str(?vocab), "computed_value#"))}
    OPTIONAL {GRAPH ?g{?vocab ?p ?o .} }
    FILTER(!BOUND(?g))      }
    GROUP BY ?amap
    '''
    return qstr


def mapping_by_properties(prop_list):
    """
    Return the mapping id's which contain all of the proerties
    in the list of property dictionaries
    
    """
    fstr = ''
    for prop_dict in prop_list:
        name = prop_dict.get('mr:name')
        op = prop_dict.get('mr:operator')
        value = prop_dict.get('rdf:value')
        if name:
            fstr += '\tFILTER(?name = {})\n'.format(name)
        if op:
            fstr += '\tFILTER(?operator = {})\n'.format(op)
        if value:
            fstr += '\tFILTER(?value = {})\n'.format(value)
            
    qstr = '''SELECT DISTINCT ?mapping 
    WHERE {
    GRAPH <http://metarelate.net/mappings.ttl> {    
    ?mapping rdf:type mr:Mapping ;
             mr:source ?source ;
             mr:target ?target ;
             mr:status ?status ;

    FILTER (?status NOT IN ("Deprecated", "Broken"))
    MINUS {?mapping ^dc:replaces+ ?anothermap}
    }
    GRAPH <http://metarelate.net/concepts.ttl> { {
    ?source mr:hasProperty ?property
    }
    UNION {
    ?target mr:hasProperty ?property
    }
    UNION {
    ?source mr:hasComponent/mr:hasProperty ?property
    }
    UNION {
    ?target mr:hasComponent/mr:hasProperty ?property
    }
    UNION {
    ?source mr:hasProperty/mr:hasComponent/mr:hasProperty ?property
    }
    UNION {
    ?target mr:hasProperty/mr:hasComponent/mr:hasProperty ?property
    }
    ?property mr:name ?name .
    OPTIONAL{?property rdf:value ?value . }
    OPTIONAL{?property mr:operator ?operator . }
    %s
    }
    }
    ''' % fstr
    return qstr


# def get_all_notation_note(fuseki_process, graph, debug=False):
#     """
#     return all names, skos:notes and skos:notations from the stated graph
#     """
#     qstr = '''SELECT ?name ?notation ?units
#     WHERE
#     {GRAPH <%s>{
#     ?name skos:note ?units ;
#           skos:notation ?notation .
#     }
#     }
#     order by ?name
#     ''' % graph
#     results = fuseki_process.run_query(qstr, debug=debug)
#     return results


def _vocab_graphs():
    """returns a list of the graphs which contain thirds party vocabularies """
    vocab_graphs = []
    vocab_graphs.append('<http://metarelate.net/formats.ttl>')
    vocab_graphs.append('<http://um/umdpF3.ttl>')
    vocab_graphs.append('<http://um/stashconcepts.ttl>')
    vocab_graphs.append('<http://um/fieldcode.ttl>')
    vocab_graphs.append('<http://cf/cf-model.ttl>')
    vocab_graphs.append('<http://cf/cf-standard-name-table.ttl>')
    vocab_graphs.append('<http://grib/apikeys.ttl>')
    vocab_graphs.append('<http://openmath/ops.ttl>')
    return vocab_graphs
