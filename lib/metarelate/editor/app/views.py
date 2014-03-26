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

import collections
import copy
import datetime
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
import urllib

from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.html import escape 
from django.utils.safestring import mark_safe
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory


import forms
import metarelate
import metarelate.prefixes as prefixes
from metarelate.editor.settings import READ_ONLY
from metarelate.editor.settings import fuseki_process


def home(request):
    """
    returns a view for the editor homepage
    a control panel for interacting with the triple store
    and reporting on status
    
    """
    persist = fuseki_process.query_cache()
    cache_status = '{} statements in the local triple store are' \
                   ' flagged as not existing in the persistent ' \
                   'StaticData store'.format(len(persist))
    print_string = ''
    for r in persist:
        if len(r.keys()) == 3 and r.has_key('s') and \
            r.has_key('p') and r.has_key('o'):
            print_string += '%s\n' % r['s']
            print_string += '\t%s\n' % r['p']
            print_string += '\t\t%s\n' % r['o']
            print_string += '\n'
        else:
            for k,v in r.iteritems():
                print_string += '%s %s\n' (k, v)
            print_string += '\n'
    cache_state = print_string
    #find cached mappings
    edited_mappings = set()
    for r in persist:
        map_str = '<http://www.metarelate.net/metOcean/mapping/'
        if r.has_key('s') and r['s'].startswith(map_str):
            edited_mappings.add(r['s'])
    if request.method == 'POST':
        form = forms.HomeForm(request.POST)
        if form.is_valid():
            invalids = form.cleaned_data.get('validation')
            if invalids:
                url = url_qstr(reverse('invalid_mappings'),
                                           ref=json.dumps(invalids))
                response = HttpResponseRedirect(url)
            else:
                url = url_qstr(reverse('home'))
                reload(forms)
                response = HttpResponseRedirect(url)
    else:
        form = forms.HomeForm(initial={'cache_status':cache_status,
                                       'cache_state':cache_state})
        # con_dict = {}
        con_dict = _process_mapping_list(edited_mappings, 'cached mapping edits')
        searchurl = url_qstr(reverse('fsearch'),ref='')
        con_dict['search'] = {'url':searchurl, 'label':'search for mappings'}
        createurl = reverse('mapping_formats')
        con_dict['create'] = {'url':createurl, 'label':'create a new mapping'}
        con_dict['control'] = {'control':'control'}
        con_dict['form'] = form
        context = RequestContext(request, con_dict)
        response = render_to_response('main.html', context)
    return response

def mapping_formats(request):
    """ returns a view to define the formats for the mapping_concept """
    if request.method == 'POST':
        form = forms.MappingFormats(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            referrer = {'mr:source': {'mr:hasFormat': data['source_format']},
                        'mr:target': {'mr:hasFormat': data['target_format']}}
            url = url_qstr(reverse('mapping_concepts'),
                                       ref=json.dumps(referrer))
            response = HttpResponseRedirect(url)
    else:
        form = forms.MappingFormats()
        context = RequestContext(request, {'form':form})
        response = render_to_response('simpleform.html', context)
    return response

def _prop_id(members, fformat=None):
    """
    helper function
    returns the value_ids from a list of value records
    in the triple store
    
    """
    new_map = copy.deepcopy(members)
    property_list = []
    prop_ids = []
    mrprops = []
    for mem, new_mem in zip(members, new_map):
        comp_mem = mem.get('mr:hasComponent')
        new_comp = new_mem.get('mr:hasComponent')
        if comp_mem and new_comp:
            subprops = []
            props = comp_mem.get('mr:hasProperty')
            new_props = new_comp.get('mr:hasProperty')
            if props and new_props:
                for i, (prop, new_prop) in enumerate(zip(props, new_props)):
                    # remove old property id
                    prop.pop('property', None)
                    mrprop = metarelate.Property(None, prop['mr:name'],
                                                 prop['rdf:value'], 
                                                 prop['mr:operator'])
                    mrprop.create_rdf(fuseki_process)
                    subprops.append(mrprop)
            else:
                #validation error please
                raise ValueError('If a property has a component that component'
                                 'must itself reference properties')
            mrcomp = metarelate.Concept(None, fformat, 
                                        metarelate.PropertyComponent(None, subprops))
            mrcomp.create_rdf(fuseki_process)
            new_mem['mr:hasComponent']['component'] = mrcomp.uri.data
        # remove old property id
        mem.pop('property', None)
        if mem.has_key('rdf:value') and mem.has_key('mr:operator'):
            mrprop = metarelate.Property(None, mem['mr:name'],
                                         mem['rdf:value'], 
                                         mem['mr:operator'])
        elif mem.has_key('mr:hasComponent'):
            mrprop = metarelate.Property(None, mem['mr:name'],
                                         component=mem['mr:hasComponent'])
        else:
            mrprop = metarelate.Property(None, mem['mr:name'])
        mrprop.create_rdf(fuseki_process)
        new_mem['property'] = mrprop.uri.data
        mrprops.append(mrprop)
    return mrprops


def url_qstr(path, **kwargs):
    """
    helper function
    returns url for path and query string
    
    """
    return path + '?' + urllib.urlencode(kwargs)


def _create_components(key, requestor, new_map):#, components):
    """
    return the mapping json structure and components list having created
    relevant component records in the triple store

    """
    mrcomps = []
    for i, (mem, newm) in enumerate(zip(requestor[key]['mr:hasComponent'],
                                  new_map[key]['mr:hasComponent'])):
        if mem.get('mr:hasProperty'):
            mrprops = _prop_id(mem.get('mr:hasProperty'),
                               requestor[key].get('mr:hasFormat'))
            mrcomp = metarelate.Concept(None, requestor[key]['mr:hasFormat'],
                                        metarelate.PropertyComponent(None, mrprops))
            mrcomp.create_rdf(fuseki_process)
            mrcomps.append(mrcomp)
    mrcomp = metarelate.Concept(None, requestor[key]['mr:hasFormat'],
                                mrcomps)

    mrcomp.create_rdf(fuseki_process)
    new_map[key]['component'] = mrcomp.uri.data
    return new_map

def _create_properties(key, requestor, new_map):
    """
    return the mapping json structure and components list having created
    relevant property records in the triple store
    
    """
    props = requestor[key]['mr:hasProperty']
    mrprops = _prop_id(props)
    mrcomp = metarelate.Concept(None, requestor[key]['mr:hasFormat'],
                                metarelate.PropertyComponent(None, mrprops))
    if requestor[key].get('dc:mediator'):
        mrcomp.mediator = requestor[key]['dc:mediator']
    if requestor[key].get('dc:requires'):
        ## nb many requires required one day
        mrcomp.requires = requestor[key]['dc:requires']
    mrcomp.create_rdf(fuseki_process)
    new_map[key]['component'] = mrcomp.uri.data
    return new_map

def _component_links(key, request, amended):
    """
    helper method
    provides urls in amended (the dictionary used for rendering the view,
    for adding and removing concepts
    
    """
    fformurl = '%s' % request[key]['mr:hasFormat']
    fformat = request[key]['mr:hasFormat'].split('/')[-1]
    fformat = fformat.rstrip('>')
    ## 'add a new component' link
    fterm = copy.deepcopy(request)
    if not fterm[key].get('mr:hasProperty'):
        if not fterm[key].get('mr:hasComponent'):
            fterm[key]['mr:hasComponent'] = []
            amended[key]['mr:hasComponent'] = []
        fterm[key]['mr:hasComponent'].append({"mr:hasComponent":[]})
        refer = {'url': url_qstr(reverse('mapping_concepts'),
                                             ref=json.dumps(fterm)),
                'label': 'add a component'}
        amended[key]['mr:hasComponent'].append(refer)
    ## 'add a new property' link if no sub-component exist
    if not request[key].get('mr:hasComponent'):
        new_term = copy.deepcopy(request)
        if not new_term[key].get('mr:hasProperty'):
            new_term[key]['mr:hasProperty'] = []
            amended[key]['mr:hasProperty'] = []
        new_term[key]['mr:hasProperty'].append('&&&&')
        refer = {'url':url_qstr(reverse('define_property',
                      kwargs={'fformat':fformat}),
                      ref=json.dumps(new_term)),
                'label':'add a property definition'}
        amended[key]['mr:hasProperty'].append(refer)
    ## removers
    rem_keys = ['mr:hasProperty', 'mr:hasComponent']
    for rem_key in rem_keys:
        for i, rs in enumerate(request[key].get(rem_key, [])):
            remover = copy.deepcopy(request)
            del remover[key][rem_key][i]
            url = url_qstr(reverse('mapping_concepts'),
                                               ref=json.dumps(remover))
            ad = amended[key].get(rem_key, [])[i]
            ad['remove'] = {'url':url, 'label':'remove this item'}
    for i, rq in enumerate(request[key].get('mr:hasProperty', [])):
        ad = amended[key].get('mr:hasProperty', [])[i]
        ## link to add a new component to a 'name only' property
        if rq.get('mr:name') and not rq.get('mr:operator') and not \
            rq.get('rdf:value') and not rq.get('mr:hasComponent'):
            refr = copy.deepcopy(request)
            new_comp = {'mr:hasFormat':fformurl}
            refr[key]['mr:hasProperty'][i]['mr:hasComponent'] = new_comp
            compurl = url_qstr(reverse('mapping_concepts'),
                                     ref=json.dumps(refr))
            ref = {'url':compurl, 'label':'add a component'}
            ad['define_component'] = ref
        #adder for a new sub-conponent property to a name and concept property
        elif rq.get('mr:name') and not rq.get('mr:operator') and not \
            rq.get('rdf:value') and rq.get('mr:hasComponent'):
            refr = copy.deepcopy(request)
            rf = refr[key]['mr:hasProperty'][i]
            if not rq['mr:hasComponent'].get('mr:hasProperty'):
                rf['mr:hasComponent']['mr:hasProperty'] = []
                ad['mr:hasComponent']['mr:hasProperty'] = []
            rf['mr:hasComponent']['mr:hasProperty'].append('&&&&')
            prop = {'url':url_qstr(reverse('define_property',
                                           kwargs={'fformat':fformat}),
                                   ref=json.dumps(refr)),
                    'label':'add a property definition'}
            ad['mr:hasComponent']['mr:hasProperty'].append(prop)
            #remover for each sub-component property
            for j, prq in enumerate(rq['mr:hasComponent'].get('mr:hasProperty',
                                                              [])):
                remover = copy.deepcopy(request)
                rm = remover[key]['mr:hasProperty'][i]
                del rm['mr:hasComponent']['mr:hasProperty'][j]
                url = url_qstr(reverse('mapping_concepts'),
                               ref=json.dumps(remover))
                rmer = {'url':url, 'label':'remove this item'}
                ad['mr:hasComponent']['mr:hasProperty'][j]['remove'] = rmer
    ## iterate through sub-components
    for k, scomp in enumerate(request[key].get('mr:hasComponent', [])):
        amd = amended[key].get('mr:hasComponent', [])[k]
        ## add property
        new_term = copy.deepcopy(request)
        if not scomp.get('mr:hasProperty'):
            new_term[key]['mr:hasComponent'][k]['mr:hasProperty'] = []
            amd['mr:hasProperty'] = []
        new_term[key]['mr:hasComponent'][k]['mr:hasProperty'].append('&&&&')
        refer = {'url':url_qstr(reverse('define_property',
                                        kwargs={'fformat':fformat}),
                                ref=json.dumps(new_term)),
                'label':'add a property definition'}
        amd['mr:hasProperty'].append(refer)
        
        for i, elem in enumerate(scomp.get('mr:hasProperty', [])):
            ad = amd.get('mr:hasProperty', [])[i]
        ## remove property
            remover = copy.deepcopy(request)
            del remover[key]['mr:hasComponent'][k]['mr:hasProperty'][i]
            url = url_qstr(reverse('mapping_concepts'), ref=json.dumps(remover))
            ad['remove'] = {'url':url, 'label':'remove this item'}
            ## enable component as property
            if elem.get('mr:name') and not elem.get('mr:operator') and not \
                elem.get('rdf:value') and not elem.get('mr:hasComponent'):
                refr = copy.deepcopy(request)
                refR = refr[key]['mr:hasComponent'][k]['mr:hasProperty'][i]
                refR['mr:hasComponent'] = {'mr:hasFormat':fformurl}
                compurl = url_qstr(reverse('mapping_concepts'),
                                         ref=json.dumps(refr))
                ref = {'url':compurl, 'label':'add a component'}
                ad['define_component'] = ref
            elif elem.get('mr:name') and not elem.get('mr:operator') and not \
                elem.get('rdf:value') and elem.get('mr:hasComponent'):
                #adder for a new property
                refr = copy.deepcopy(request)
                refR = refr[key]['mr:hasComponent'][k]['mr:hasProperty'][i]
                if not elem['mr:hasComponent'].get('mr:hasProperty'):
                    refR['mr:hasComponent']['mr:hasProperty'] = []
                    ad['mr:hasComponent']['mr:hasProperty'] = []
                refR['mr:hasComponent']['mr:hasProperty'].append('&&&&')
                prop = {'url':url_qstr(reverse('define_property',
                                                kwargs={'fformat':fformat}),
                                       ref=json.dumps(refr)),
                        'label':'add a property definition'}
                ad['mr:hasComponent']['mr:hasProperty'].append(prop)
                #remover for each property
                pelems = elem['mr:hasComponent'].get('mr:hasProperty', [])
                pads = ad['mr:hasComponent'].get('mr:hasProperty', [])
                for j, pelem in enumerate(pelems):
                    pad = pads[j]
                    rer = copy.deepcopy(request)
                    rmR = rer[key]['mr:hasComponent'][k]['mr:hasProperty'][i]
                    del rmR['mr:hasComponent']['mr:hasProperty'][j]
                    url = url_qstr(reverse('mapping_concepts'),
                                   ref=json.dumps(remover))
                    pad['remove'] = {'url':url, 'label':'remove this item'}
    ## mediators
    for fckey in ['dc:requires', 'dc:mediator']:
        url = None
        # if True:
        # if fformat == 'cf':
        adder = copy.deepcopy(request)
        if request[key].get(fckey):
            if fckey == 'dc:requires':
                adder[key][fckey].append('&&&&')
                rev = reverse('define_mediator', kwargs={'mediator':fckey,
                                                         'fformat':fformat})
                url = url_qstr(rev, ref=json.dumps(adder))
        else:
            adder[key][fckey] = ['&&&&']
            rev = reverse('define_mediator', kwargs={'mediator':fckey,
                                                     'fformat':fformat})
            url = url_qstr(rev, ref=json.dumps(adder))
            amended[key][fckey] = []
        if url:
            amended[key][fckey].append({'url': url,
                                        'label': 'add a {}'.format(fckey)}) 
    return amended


### for comparison post refactoring (see above): 
def __component_links(key, requestor, amended_dict):
    """
    helper method
    provides urls in amended_dict for adding and removing concepts
    """
    fformurl = '%s' % requestor[key]['mr:hasFormat']
    fformat = requestor[key]['mr:hasFormat'].split('/')[-1]
    fformat = fformat.rstrip('>')
    ## 'add a new component' link
    fterm = copy.deepcopy(requestor)
    if not fterm[key].get('mr:hasProperty'):
        if not fterm[key].get('mr:hasComponent'):
            fterm[key]['mr:hasComponent'] = []
            amended_dict[key]['mr:hasComponent'] = []
        fterm[key]['mr:hasComponent'].append({"mr:hasComponent":[]})
        refer = {'url': url_qstr(reverse('mapping_concepts'),
                                             ref=json.dumps(fterm)),
                'label': 'add a component'}
        amended_dict[key]['mr:hasComponent'].append(refer)
    ## 'add a new property' link if no sub-component exist
    if not requestor[key].get('mr:hasComponent'):
        new_term = copy.deepcopy(requestor)
        if not new_term[key].get('mr:hasProperty'):
            new_term[key]['mr:hasProperty'] = []
            amended_dict[key]['mr:hasProperty'] = []
        new_term[key]['mr:hasProperty'].append('&&&&')
        refer = {'url':url_qstr(reverse('define_property',
                      kwargs={'fformat':fformat}),
                      ref=json.dumps(new_term)),
                'label':'add a property definition'}
        amended_dict[key]['mr:hasProperty'].append(refer)
    ## removers
    rem_keys = ['mr:hasProperty', 'mr:hasComponent']
    for rem_key in rem_keys:
        for i, element in enumerate(requestor[key].get(rem_key, [])):
            remover = copy.deepcopy(requestor)
            del remover[key][rem_key][i]
            url = url_qstr(reverse('mapping_concepts'),
                                               ref=json.dumps(remover))
            amended_dict[key][rem_key][i]['remove'] = {'url':url,
                                    'label':'remove this item'}
    for i, elem in enumerate(requestor[key].get('mr:hasProperty', [])):
        ## link to add a new component to a 'name only' property
        if elem.get('mr:name') and not elem.get('mr:operator') and not \
            elem.get('rdf:value') and not elem.get('mr:hasComponent'):
            refr = copy.deepcopy(requestor)
            refr[key]['mr:hasProperty'][i]['mr:hasComponent'] = {'mr:hasFormat':fformurl}
            compurl = url_qstr(reverse('mapping_concepts'),
                                     ref=json.dumps(refr))
            ref = {'url':compurl, 'label':'add a component'}
            #print ref
            amended_dict[key]['mr:hasProperty'][i]['define_component'] = ref
        #adder for a new sub-conponent property to a name and concept property
        elif elem.get('mr:name') and not elem.get('mr:operator') and not \
            elem.get('rdf:value') and elem.get('mr:hasComponent'):
            refr = copy.deepcopy(requestor)
            if not elem['mr:hasComponent'].get('mr:hasProperty'):
                refr[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'] = []
                amended_dict[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'] = []
            refr[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'].append('&&&&')
            prop = {'url':url_qstr(reverse('define_property',
              kwargs={'fformat':fformat}),
              ref=json.dumps(refr)), 'label':'add a property definition'}
            amended_dict[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'].append(prop)
            #remover for each sub-component property
            for j, pelem in enumerate(elem['mr:hasComponent'].get('mr:hasProperty', [])):
                remover = copy.deepcopy(requestor)
                del remover[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'][j]
                url = url_qstr(reverse('mapping_concepts'),
                                                   ref=json.dumps(remover))
                amended_dict[key]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'][j]['remove'] = {'url':url, 'label':'remove this item'}
    ## iterate through sub-components
    for k, scomp in enumerate(requestor[key].get('mr:hasComponent', [])):
        ## add property
        new_term = copy.deepcopy(requestor)
        if not new_term[key]['mr:hasComponent'][k].get('mr:hasProperty'):
            new_term[key]['mr:hasComponent'][k]['mr:hasProperty'] = []
            amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'] = []
        new_term[key]['mr:hasComponent'][k]['mr:hasProperty'].append('&&&&')
        refer = {'url':url_qstr(reverse('define_property',
                      kwargs={'fformat':fformat}),
                      ref=json.dumps(new_term)),
                'label':'add a property definition'}
        amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'].append(refer)
    ## remove property
        for i, elem in enumerate(requestor[key]['mr:hasComponent'][k].get('mr:hasProperty', [])):
            remover = copy.deepcopy(requestor)
            del remover[key]['mr:hasComponent'][k]['mr:hasProperty'][i]
            url = url_qstr(reverse('mapping_concepts'),
                                               ref=json.dumps(remover))
            amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['remove'] = {'url':url,
                                    'label':'remove this item'}
            ## enable component as property
            if elem.get('mr:name') and not elem.get('mr:operator') and not \
                elem.get('rdf:value') and not elem.get('mr:hasComponent'):
                refr = copy.deepcopy(requestor)
                refr[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent'] = {'mr:hasFormat':fformurl}
                compurl = url_qstr(reverse('mapping_concepts'),
                                         ref=json.dumps(refr))
                ref = {'url':compurl, 'label':'add a component'}
                #print ref
                amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['define_component'] = ref
            elif elem.get('mr:name') and not elem.get('mr:operator') and not \
                elem.get('rdf:value') and elem.get('mr:hasComponent'):
                #adder for a new property
                refr = copy.deepcopy(requestor)
                if not elem['mr:hasComponent'].get('mr:hasProperty'):
                    refr[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'] = []
                    amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'] = []
                refr[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'].append('&&&&')
                prop = {'url':url_qstr(reverse('define_property',
                  kwargs={'fformat':fformat}),
                  ref=json.dumps(refr)), 'label':'add a property definition'}
                amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'].append(prop)
                #remover for each property
                for j, pelem in enumerate(elem['mr:hasComponent'].get('mr:hasProperty', [])):
                    remover = copy.deepcopy(requestor)
                    del remover[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'][j]
                    url = url_qstr(reverse('mapping_concepts'),
                                                       ref=json.dumps(remover))
                    amended_dict[key]['mr:hasComponent'][k]['mr:hasProperty'][i]['mr:hasComponent']['mr:hasProperty'][j]['remove'] = {'url':url, 'label':'remove this item'}
    ## mediators
    for fckey in ['dc:requires', 'dc:mediator']:
        url = None
        if True:
        # if fformat == 'cf':
            adder = copy.deepcopy(requestor)
            if requestor[key].get(fckey):
                if fckey == 'dc:requires':
                    adder[key][fckey].append('&&&&')
                    url = url_qstr(reverse('define_mediator',
                                                       kwargs={'mediator':fckey,
                                                        'fformat':fformat}),
                                                        ref=json.dumps(adder))
            else:
                adder[key][fckey] = ['&&&&']
                url = url_qstr(reverse('define_mediator', kwargs=
                                                   {'mediator':fckey,
                                                    'fformat':fformat}),
                                                    ref=json.dumps(adder))
                amended_dict[key][fckey] = []
            if url:
                amended_dict[key][fckey].append({'url': url, 'label':
                                                 'add a {}'.format(fckey)}) 

    return amended_dict


def mapping_concepts(request):
    """
    returns a view to present the mapping concepts:
    source and target, and the valuemaps
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '{}'
    requestor = json.loads(requestor_path)
    print requestor
    amended_dict = copy.deepcopy(requestor)
    if request.method == 'POST':
        ## get the formatConcepts for source and target
        ## pass to value map definition
        form = forms.MappingConcept(request.POST)
        new_map = copy.deepcopy(requestor)
        for key in ['mr:source','mr:target']:
            if requestor[key].get('mr:hasProperty'):
                new_map = _create_properties(key, requestor, new_map)
            elif requestor[key].get('mr:hasComponent'):
                new_map = _create_components(key, requestor, new_map)
        for key in ['mr:source','mr:target']:
            if not new_map[key].has_key('component'):
                raise ValueError('The source and target are not both defined')
        ref = json.dumps(new_map)
        url = url_qstr(reverse('value_maps'),ref=ref)
        response = HttpResponseRedirect(url)
    else:
        form = forms.MappingConcept()
        for key in ['mr:source','mr:target']:
            amended_dict = _component_links(key, requestor, amended_dict)
        con_dict = {}
        con_dict['mapping'] = amended_dict
        con_dict['form'] = form
        context = RequestContext(request, con_dict)
        response = render_to_response('mapping_concept.html', context)
    return response

def define_mediator(request, mediator, fformat):
    """
    returns a view to define a mediator for a
    formatConcept
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    requestor = json.loads(requestor_path)
    if request.method == 'POST':
        form = forms.Mediator(request.POST, fformat=fformat)
    else:
        form = forms.Mediator(fformat=fformat)
    if request.method == 'POST' and form.is_valid():
        mediator = form.cleaned_data['mediator']
        requestor_path = requestor_path.replace('&&&&',
                                                          mediator)
        url = url_qstr(reverse('mapping_concepts'),
                                   ref=requestor_path)
        response = HttpResponseRedirect(url)
    else:
        con_dict = {'form':form}
        if mediator == 'dc:mediator':
            links = []
            link_url = url_qstr(reverse('create_mediator',
                                        kwargs={'fformat':fformat}),
                                ref=requestor_path)
            links.append({'url':link_url, 'label':'create a new mediator'})
            con_dict['links'] = links
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response


def create_mediator(request, fformat):
    """
    returns a view to define a mediator for a
    formatConcept
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    requestor = json.loads(requestor_path)
    if request.method == 'POST':
        form = forms.NewMediator(request.POST)
    else:
        form = forms.NewMediator()
    if request.method == 'POST' and form.is_valid():
        mediator = form.cleaned_data['mediator']
        po_dict = {'mr:hasFormat': fformat,'rdf:label': mediator}
        qstr, instr = metarelate.Mediator.sparql_creator(po_dict)
        res = fuseki_process.create(qstr, instr)
        kw = {'mediator':'dc:mediator','fformat':fformat}
        url = url_qstr(reverse('define_mediator', kwargs=kw),
                                   ref=requestor_path)
        response = HttpResponseRedirect(url)
    else:
        con_dict = {'form':form}
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response


def _get_value(value):
    """
    helper function
    returns a value id for a given json input
    
    """
    if value.get('mr:subject').get('mr:subject'):
        subj_id = _get_value(value.get('mr:subject'))
    else:
        po_dict = value['mr:subject']['mr:hasProperty']
        qstr, instr = metarelate.Property.sparql_creator(po_dict)
        prop = fuseki_process.create(qstr, instr)
        po_dict = {'mr:hasProperty':prop['property'],
                   'mr:scope':value['mr:subject']['mr:scope']}
        qstr, instr = metarelate.ScopedProperty.sparql_creator(po_dict)
        sc_prop = fuseki_process.create(qstr, instr)
        subj_id = sc_prop['scopedProperty']
    new_val = {'mr:subject':subj_id}
    if value.get('mr:object'):
        if isinstance(value.get('mr:object'), dict) and \
            value.get('mr:object').get('mr:subject'):
            obj_id = _get_value(value.get('mr:object'))
        else:
            if isinstance(value.get('mr:object'), dict):
                po_dict = value['mr:object']['mr:hasProperty']
                qstr, instr = metarelate.Property.sparql_creator(po_dict)
                oprop = fuseki_process.create(qstr, instr)
                po_dict = {'mr:hasProperty':oprop['property'],
                           'mr:scope':value['mr:object']['mr:scope']}
                qstr, instr = metarelate.ScopedProperty.sparql_creator(po_dict)
                o_sc_prop = fuseki_process.create(qstr, instr)
                obj_id = o_sc_prop['scopedProperty']
            else:
                obj_id = value.get('mr:object')
        new_val['mr:object'] = obj_id
    if value.get('mr:operator'):
        new_val['mr:operator'] = value.get('mr:operator')
    qstr, instr = metarelate.Value.sparql_creator(new_val)
    value = fuseki_process.create(qstr, instr)
    v_id = value['value']
    return v_id
        

def value_maps(request):
    """
    returns a view to define value mappings for a defined
    source and target pair
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '{}'
    requestor = json.loads(requestor_path)
    print requestor
    amended_dict = copy.deepcopy(requestor)
    if request.method == 'POST':
        ## create the valuemaps as defined
        ## check if a mapping (including invalid) provides this source to target
        #### or this source to a different target (same format)
        #### perhaps render this on a new screen
        ## then pass the json of {source:{},target:{},valueMaps[{}]
        ## to mapping_edit for creation
        form = forms.MappingConcept(request.POST)
        for valuemap in requestor.get('mr:hasValueMap',[]):
            vmap_dict = {'mr:source':_get_value(valuemap['mr:source']),
                         'mr:target':_get_value(valuemap['mr:target'])}
            qstr, instr = metarelate.ValueMap.sparql_creator(vmap_dict)
            vmap = fuseki_process.create(qstr, instr)
            valuemap['valueMap'] = vmap['valueMap']
            #value['value'] = val_id
        url = url_qstr(reverse('mapping_edit'),
                                   ref = json.dumps(requestor))
        response = HttpResponseRedirect(url)
            
    else:
        form = forms.MappingConcept()
        if not amended_dict.has_key('mr:hasValueMap'):
            addition = copy.deepcopy(requestor)
            addition['mr:hasValueMap'] = []
            url = url_qstr(reverse('define_valuemaps'),
                                       ref=json.dumps(addition))
            amended_dict['addValueMap'] = {'url':url,
                                           'label':'add a value mapping'}
        else:
            url = url_qstr(reverse('define_valuemaps'),
                           ref=json.dumps(requestor))
            amended_dict['addValueMap'] = {'url':url,
                                           'label':'add a value mapping'}
        con_dict = {}
        con_dict['mapping'] = amended_dict
        con_dict['form'] = form
        context = RequestContext(request, con_dict)
        response = render_to_response('mapping_concept.html', context)
    return response

def _define_valuemap_choice(comp, aproperty, choice):
    """
    helper function
    returns a value map choice given the potential inputs
    
    """
    pcomp = aproperty.get('mr:hasComponent')
    if not aproperty.get('rdf:value') and not pcomp:
        prop = {'mr:name':aproperty.get('mr:name')}
        choice[1].append(json.dumps({'mr:scope':comp, 'mr:hasProperty': prop}))
    elif pcomp:
        for prop in pcomp.get('mr:hasProperty', []):
            if not prop.get('rdf:value'):
                val = json.dumps({'mr:scope':pcomp.get('component'), 
                           'mr:hasProperty': {'mr:name': prop.get('mr:name')}})
                choice[1].append(val)
#            elif prop.get('mr:hasComponent'):
    return choice

def define_valuemap(request):
    """ returns a view to input choices for an individual value_map """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    requestor = json.loads(requestor_path)
    # print requestor
    source_list = []
    target_list = []
    choices = [('mr:source', source_list),('mr:target', target_list)]
    for i, ch in enumerate(choices):
        if requestor[ch[0]].get('mr:hasProperty'):
            comp = requestor[ch[0]]['component']
            for elem in requestor[ch[0]]['mr:hasProperty']:
                choices[i] = _define_valuemap_choice(comp, elem, ch)
        elif requestor[ch[0]].get('mr:hasComponent'):
            for elem in requestor[ch[0]]['mr:hasComponent']:
                comp = elem['component']
                for selem in elem['mr:hasProperty']:
                    choices[i] = _define_valuemap_choice(comp, selem, ch)
        if requestor.get('derived_values'):
            for derived in requestor['derived_values'].get(ch[0]):
                ch[1].append(json.dumps(derived))
    # print 'DERIVED VALUES'
    # print requestor.get('derived_values')
    if request.method == 'POST':
        form = forms.ValueMap(request.POST, sc=source_list, tc=target_list)
        if form.is_valid():
            source = json.loads(form.cleaned_data['source_value'])
            if not source.get('mr:subject'):
                source = {'mr:subject': source}
            target = json.loads(form.cleaned_data['target_value'])
            if not target.get('mr:subject'):
                target = {'mr:subject': target}
            new_vmap = {'mr:source':source,
                        'mr:target':target}
            requestor['mr:hasValueMap'].append(new_vmap)
            if requestor.get('derived_values'):
                del requestor['derived_values']
            requestor_path = json.dumps(requestor)
            url = url_qstr(reverse('value_maps'),
                                       ref=requestor_path)
            return HttpResponseRedirect(url)
    else:
        form = forms.ValueMap(sc=source_list, tc=target_list)
    con_dict = {'form':form}
    links = []
    link_url = url_qstr(reverse('derived_value', kwargs={'role':'source'}),
                                        ref=requestor_path)
    links.append({'url':link_url, 'label':'create a derived source value'})
    link_url = url_qstr(reverse('derived_value', kwargs={'role':'target'}),
                                        ref=requestor_path)
    links.append({'url':link_url, 'label':'create a derived target value'})
    con_dict['links'] = links
    context = RequestContext(request, con_dict)
    return render_to_response('simpleform.html', context)


def derived_value(request, role):
    """
    reurns a view to create a derived value
    given the potnetial inputs from the component request
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    requestor = json.loads(requestor_path)
    if not requestor.get('derived_values'):
        requestor['derived_values'] = {'mr:source':[], 'mr:target':[]}
    source_list = []
    target_list = []
    choices = [('mr:source', source_list),('mr:target', target_list)]
    for i, ch in enumerate(choices):
        if requestor[ch[0]].get('mr:hasProperty'):
            comp = requestor[ch[0]]['component']
            for elem in requestor[ch[0]]['mr:hasProperty']:
                choices[i] = _define_valuemap_choice(comp, elem, ch)
        elif requestor[ch[0]].get('mr:hasComponent'):
            for elem in requestor[ch[0]]['mr:hasComponent']:
                comp = elem['component']
                for selem in elem['mr:hasProperty']:
                    choices[i] = _define_valuemap_choice(comp, selem, ch)
        if requestor.get('derived_values'):
            for derived in requestor['derived_values'].get(ch[0]):
                ch[1].append(json.dumps(derived))
    #print 'DERIVED VALUES'
    #print requestor.get('derived_values')
    if role == 'source':
        components = source_list
    elif role == 'target':
        components = target_list
    else:
        raise ValueError('role must be source or target')
    if request.method == 'POST':
        form = forms.DerivedValue(request.POST, components=components)
        if form.is_valid():
            derived = {}
            derived['mr:subject'] = json.loads(form.cleaned_data['_subject'])
            if form.cleaned_data.get('_object'):
                derived['mr:object'] = json.loads(form.cleaned_data['_object'])
            elif form.cleaned_data.get('_object_literal'):
                derived['mr:object'] = form.cleaned_data['_object_literal']
            derived['mr:operator'] = form.cleaned_data['_operator']
            requestor['derived_values']['mr:{}'.format(role)].append(derived)
            requestor_path = json.dumps(requestor)
            url = url_qstr(reverse('define_valuemaps'),
                                       ref=requestor_path)
            response = HttpResponseRedirect(url)
        else:
            con_dict = {'form':form}
            context = RequestContext(request, con_dict)
            response = render_to_response('simpleform.html', context)
    else:
        form = forms.DerivedValue(components=components)
        con_dict = {'form':form}
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response


def define_property(request, fformat):
    """ returns a view to define an individual property  """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if request.method == 'POST':
        form = forms.Value(request.POST, fformat=fformat)
        if form.is_valid():
            new_value = {}
            if form.cleaned_data.get('name'):
                new_value['mr:name'] = form.cleaned_data['name']
            if form.cleaned_data['value'] != '""':
                new_value['rdf:value'] =  form.cleaned_data['value']
            if form.cleaned_data.get('operator'):
                new_value['mr:operator'] = form.cleaned_data['operator']
            newv = json.dumps(new_value)
            requestor_path = requestor_path.replace('"&&&&"', newv)
            url = url_qstr(reverse('mapping_concepts'),
                                       ref=requestor_path)
            response = HttpResponseRedirect(url)
        else:
            con_dict = {'form':form}
            context = RequestContext(request, con_dict)
            response = render_to_response('simpleform.html', context)
    else:
        form = forms.Value(fformat=fformat)
        con_dict = {'form':form}
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response


    
def mapping_edit(request):
    """
    returns a view to provide editing to the mapping record defining a
    source target and any valuemaps from the referrer
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '{}'
    requestor = json.loads(requestor_path)
    # print requestor
    fname = None
    if request.method == 'POST':
        form = forms.MappingMeta(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            source = fuseki_process._retrieve_component(data['source'])
            target = fuseki_process._retrieve_component(data['target'])
            
            amap = metarelate.Mapping(None,  source, target, 
                                      invertible=data['invertible'],
                                      editor=data['editor'],
                                      reason=data['next_reason'],
                                      status=data['next_status'])
            if data['mapping'] != "":
                amap.replaces = data['mapping']
            if data['comment'] != '':
                amap.note = data['comment']
            if data.get('valueMaps'):
                amap.valuemaps = ['%s' % vm for vm in
                                          data['valueMaps'].split('&')]
            # if data.get('owners'):
            #     amap.owners = ['%s' % vm for vm in
            #                               data['owners'].split('&')]
            # if data.get('watchers'):
            #     amap.watchers = ['%s' % vm for vm in
            #                               data['watchers'].split('&')]
            
            amap.create_rdf(fuseki_process)
            requestor['mapping'] = amap.uri.data
            url = url_qstr(reverse('mapping_edit'),
                                       ref=json.dumps(requestor))
            return HttpResponseRedirect(url)
    else:
        ## look for mapping, if it exists, show it, with a warning
        ## if a partially matching mapping exists, handle this (somehow)
        initial = {'invertible':'"True"',
                   'source':requestor.get('mr:source').get('component')
                   ,
                   'target':requestor.get('mr:target').get('component')
                   , 'valueMaps':'&'.join([vm.get('valueMap') for vm
                                         in requestor.get('mr:hasValueMap',
                                                               [])])}
        map_id = requestor.get('mapping')
        if map_id:
            qstr = metarelate.Mapping.sparql_retriever(map_id, valid=False)
            mapping = fuseki_process.retrieve(qstr)
            ## quick example of dot notation, needs refactor
            amap = mapping.copy()
            map_instance = fuseki_process.structured_mapping(amap)
            # print map_instance
            fname = map_id.split('/')[-1].rstrip('>') + '.png'
            outfile = os.path.join(os.path.dirname(__file__), 'static',
                                   'tmp_images', fname)
            graph = map_instance.dot()
            graph.write_png(outfile)
            ts = initial['source'] == mapping['source']
            tt = initial['target'] == mapping['target']
            tvm = initial['valueMaps'].split('&').sort() == \
                  mapping.get('hasValueMaps', '').split('&').sort()
            # if ts and tt and tvm:
            initial = mapping
            initial['editor'] = initial.pop('creator')
            initial['source'] = requestor.get('mr:source').get('component')
            initial['target'] =  requestor.get('mr:target').get('component')
            initial['valueMaps'] = '&'.join([vm.get('valueMap') for vm in
                                         requestor.get('mr:hasValueMap', [])])
            # if mapping.get('valueMaps'):
            #     initial['valueMaps'] = '&'.join(mapping['valueMaps'])
            if mapping.get('note'):
                initial['comment'] = mapping['note'].strip('"')
            if mapping.get('reason'):
                initial['next_reason'] = mapping['reason']
            if mapping.get('status'):
                initial['next_status'] = mapping['status']
            if mapping.get('creator'):
                initial['last_editor'] = mapping['creator']
        form = forms.MappingMeta(initial)
    con_dict = {}
    con_dict['mapping'] = requestor
    if fname:
        con_dict['map_rendering'] = fname
    con_dict['form'] = form
    con_dict['amend'] = {'url': url_qstr(reverse(mapping_concepts),
                                                    ref=requestor_path),
                        'label': 'Re-define this Mapping'}
    context = RequestContext(request, con_dict)
    return render_to_response('mapping_concept.html', context)


def invalid_mappings(request):
    """
    list mappings which reference the concept search criteria
    by concept by source then target
    
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '{}'
    requestor = json.loads(requestor_path)
    invalids = []
    for key, inv_mappings in requestor.iteritems():
        invalid = {'label':key, 'mappings':[]}
        for inv_map in inv_mappings:
            qstr = metarelate.Mapping.sparql_retriever(inv_map['amap'])
            mapping = fuseki_process.retrieve(qstr)
            referrer = fuseki_process.structured_mapping(mapping)
            referrer = referrer.json_referrer()
            map_json = json.dumps(referrer)
            url = url_qstr(reverse('mapping_edit'), ref=map_json)
            sig = inv_map.get('signature', [])
            label = []
            if isinstance(sig, list):
                for elem in sig:
                    label.append(elem.split('/')[-1].strip('<>'))
            else:
                label.append(sig.split('/')[-1].strip('<>'))
            if label:
                '&'.join(label)
            else:
                label = 'mapping'
            invalid['mappings'].append({'url':url, 'label':label})
        invalids.append(invalid)
    context_dict = {'invalid': invalids}
    context = RequestContext(request, context_dict)
    return render_to_response('select_list.html', context)


### searching    

def fsearch(request):
    """ Select a format """
    urls = {}
    formats = ['um', 'cf', 'grib']
    for form in formats:
        searchurl = url_qstr(reverse('search', kwargs={'fformat':form}),ref='')
        search = {'url':searchurl, 'label':'search for %s components' % form}
        urls[form] = search
    context = RequestContext(request, urls)
    return render_to_response('main.html', context)
        
    

def search(request, fformat):
    """Select a set of parameters for a concept search"""
    itemlist = ['Search Parameters:']
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '[]'
    paramlist = json.loads(requestor_path)
    for param in paramlist:
        itemlist.append(param)
    con_dict = {'itemlist' : itemlist}
    addurl = url_qstr(reverse('search_property',
                                           kwargs={'fformat':fformat}),
                                           ref=requestor_path)
    add = {'url':addurl, 'label':'add parameter'}
    con_dict['add'] = add
    conurl = url_qstr(reverse('search_maps'),
                                  ref=requestor_path)
    concepts = {'url':conurl, 'label':'find mappings'}
    con_dict['search'] = concepts
    clearurl = url_qstr(reverse('search',
                                            kwargs={'fformat':fformat}), ref='')
    con_dict['clear'] = {'url':clearurl, 'label':'clear parameters'}
    context = RequestContext(request,con_dict)
    return render_to_response('main.html', context)


def search_property(request, fformat):
    """
    returns a view to define an individual property
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    requestor = json.loads(requestor_path)
    if request.method == 'POST':
        form = forms.Value(request.POST, fformat=fformat)
        if form.is_valid():
            new_value = {}
            if form.cleaned_data.get('name'):
                new_value['mr:name'] = form.cleaned_data['name']
            if form.cleaned_data['value'] != '""':
                new_value['rdf:value'] =  form.cleaned_data['value']
            if form.cleaned_data.get('operator'):
                new_value['mr:operator'] = form.cleaned_data['operator']
            requestor.append(new_value)
            requestor_path = json.dumps(requestor)
            url = url_qstr(reverse('search',
                                               kwargs={'fformat':fformat}),
                                       ref=requestor_path)
            response = HttpResponseRedirect(url)
        else:
            con_dict = {'form':form}
            context = RequestContext(request, con_dict)
            response = render_to_response('simpleform.html', context)
    else:
        form = forms.Value(fformat=fformat)
        con_dict = {'form':form}
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response

def _process_mapping_list(map_ids, label):
    mapurls = {'label': label,
               'mappings':[]}
    for amap in map_ids:
        qstr = metarelate.Mapping.sparql_retriever(amap)
        mapping = fuseki_process.retrieve(qstr)
        if mapping is not None:
            sm = fuseki_process.structured_mapping(mapping)
            referrer = sm.json_referrer()
            map_json = json.dumps(referrer)
            url = url_qstr(reverse('mapping_edit'), ref=map_json)
            label = 'mapping'
            label = '{source} -> {target} mapping'
            label = label.format(source=sm.source.scheme.notation,
                                 target=sm.target.scheme.notation)
            if isinstance(sm.source.components[0], metarelate.PropertyComponent):
                sps = ''
                for prop in sm.source.components[0].values():
                    pname = prop.name.notation
                    pval = ''
                    # if hasattr(prop, 'value'):
                    if prop.value:
                        pval = prop.value.notation
                    sps += '{pn}:{pv}; '.format(pn=pname, pv=pval)
                label += '({})'.format(sps)
            mapurls['mappings'].append({'url':url, 'label':label})
    context_dict = {'invalid': [mapurls]}  
    return context_dict
    

def search_maps(request):
    """
    returns a view of the mappings containing the search pattern properties
    """
    requestor_path = request.GET.get('ref', '')
    requestor_path = urllib.unquote(requestor_path).decode('utf8')
    if requestor_path == '':
        requestor_path = '[]'
    prop_list = json.loads(requestor_path)
    mappings = fuseki_process.mapping_by_properties(prop_list)
    con_dict = _process_mapping_list(mappings,
                                     'Mappings containing search properties')
    context = RequestContext(request, con_dict)
    response = render_to_response('select_list.html', context)
    return response


def review(request):
    """
    returns a view of a list of mapping links
    which are different from upstream/master

    """
    if metarelate.site_config.get('static_dir'):
        cwd = os.path.join(metarelate.site_config.get('static_dir'),
                           'metarelate.net')
    data = subprocess.check_output(['git', 'diff', 'upstream/master',
                                    'mappings.ttl'],
                                    cwd=cwd,
                                    stderr=subprocess.STDOUT)

    pattern = re.compile('http://metarelate.net/metOcean/mapping/*')

    pattern1 = re.compile(r'\+<http://www.metarelate.net/metOcean/mapping/(?P<map_sha>\w+)>')
    pattern2 = re.compile(r'\+map:(?P<map_sha>\w+)')

    datalines = data.split('\n')

    map_ids = []
    map_str = '<http://www.metarelate.net/metOcean/mapping/{}>'

    for line in datalines:
        m1 = pattern1.match(line)
        m2 = pattern2.match(line)
        if m1:
            map_ids.append(map_str.format(m1.group(1)))
        elif m2:
            map_ids.append(map_str.format(m2.group(1)))
    label = 'Mappings in this branch but not on upstream master'
    con_dict = _process_mapping_list(map_ids, label)
    context = RequestContext(request, con_dict)
    response = render_to_response('select_list.html', context)
    return response

def add_contact(request):
    """
    returns a form to add a new contact
    """
    if request.method == 'POST':
        form = forms.ContactForm(request.POST)
        if form.is_valid():
            new_contact = {}
            if form.cleaned_data.get('name'):
                new_contact['skos:prefLabel'] = '"{}"'.format(form.cleaned_data['name'])
            if form.cleaned_data.get('github_id'):
                ghid = 'github:{}'.format(form.cleaned_data['github_id'])
                new_contact['skos:definition'] =  ghid
            if form.cleaned_data.get('scheme'):
                new_contact['skos:inScheme'] = '<{}>'.format(form.cleaned_data['scheme'])
            globalDateTime = datetime.datetime.now().isoformat()
            new_contact['dc:valid'] = '"%s"^^xsd:dateTime' % globalDateTime
            qstr, instr = metarelate.Contact.sparql_creator(new_contact)
            contact = fuseki_process.create(qstr, instr)
            rstr = '<script type="text/javascript">window.close()</script>'
            reload(forms)
            return HttpResponse(rstr)
    else:
        form = forms.ContactForm()
        con_dict = {'form':form}
        context = RequestContext(request, con_dict)
        response = render_to_response('simpleform.html', context)
    return response
