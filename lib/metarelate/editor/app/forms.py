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

import datetime
import json
from string import Template
import sys
import time
import urllib

from django import forms
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.safestring import mark_safe
from django.forms.formsets import Form, BaseFormSet, formset_factory, \
            ValidationError

import metarelate
import metarelate.prefixes as prefixes
from metarelate.editor.settings import READ_ONLY
from metarelate.editor.settings import fuseki_process

DS = metarelate.site_config['fuseki_dataset']


class MappingMetadata(forms.Form):
    readonly=True
    _uri = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    invertible = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _creator = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    note = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _replaces = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _valuemaps = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _rights = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _rightsHolders = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _contributors = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
    _dateAccepted = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))


class SearchStatement(forms.Form):
    predicate = forms.CharField(required=False, 
                                widget=forms.TextInput(attrs={'size':'100%'}))
    rdfobject = forms.CharField(required=False, 
                                widget=forms.TextInput(attrs={'size':'100%'}))


# class Search(forms.Form):
#     statements = formset_factory(SearchStatement)
#     # additive_search = forms.BooleanField(required=False)
#     def __init__(self, *args, **kwargs):
#         super(Search, self).__init__(*args, **kwargs)
#         # self.statements = formset_factory(SearchStatement)

    


#class SearchStatements(forms.Form):
    



def get_states():
    """
    Helper method to return valid states.
    (consider storing these in the triple store and
    providing access via a query).
    
    """
    STATES = (
        '"Draft"',
        '"Proposed"',
        '"Approved"',
        '"Broken"',
        '"Deprecated"',
    )
    return STATES

def get_reasons():
    """
    Helper method to return valid reasons.
    (consider storing these in the triple store and
    providing access via a query).
    
    """
    REASONS = (
        '"new mapping"',
        '"added metadata"',
        '"corrected metadata"',
        '"linked to new format"',
        '"corrected links"',
        '"changed status"'
        )
    return REASONS


def formats():
    """
    Temporary, returns formats
    These should be stored in the triple store and
    provided by a query

    """
    choices = [('<http://www.metarelate.net/{}/format/grib>'.format(DS), 'GRIB'),
               ('<http://www.metarelate.net/{}/format/um>'.format(DS), 'UM'),
               ('<http://www.metarelate.net/{}/format/cf>'.format(DS), 'CF')]
    return choices

class MappingFormats(forms.Form):
    """
    form to define the file format of the source and target
    for a mapping
    
    """
    source_format = forms.ChoiceField(choices=formats())
    target_format = forms.ChoiceField(choices=formats())
    def clean(self):
        data = self.cleaned_data
        if data['source_format'] == data['target_format']:
            raise forms.ValidationError(
                'The source and target formats must be different')
        return self.cleaned_data


class Mediator(forms.Form):
    """
    form to select a mediator from the list of mediators
    defined mappings, grouped into a named collection 
    
    """
    mediator = forms.ChoiceField()
    def __init__(self, *args, **kwargs):
        fformat = kwargs.pop('fformat')
        super(Mediator, self).__init__(*args, **kwargs)
        qstr = metarelate.Mediator.sparql_retriever(fformat=fformat)
        meds = fuseki_process.retrieve(qstr)
        if isinstance(meds, list):
            meds = [(med['mediator'], med['label']) for med in meds]
        elif isinstance(meds, dict):
            meds = [(meds['mediator'], meds['label'])]
        else:
            meds = []
        self.fields['mediator'].choices = meds

class NewMediator(forms.Form):
    """ form to create a new mediator """
    mediator = forms.CharField()





class MappingConcept(forms.Form):
    """
    form to define the concepts for a mapping
    the work of the form is handled by the json
    in the referrer, not the form class
    
    """
    def clean(self):
        return self.cleaned_data

class Value(forms.Form):
    """
    form to define a value for use in a concept
    format specific
    
    """
    #two name fields are provided, 'name' is a drop down list of known names,
    #'_name' is a free text field for unknown names
    #only one may be used, validated in clean()
    name = forms.ChoiceField(required=False)
    _name = forms.CharField(required=False)
    operator = forms.CharField(required=False)
    ops = fuseki_process.subject_and_plabel('http://openmath/tests.ttl')
    ops = [(op['subject'], op['notation']) for op in ops]
    ops = [('','')] + ops
    operator = forms.ChoiceField(required=False, choices=ops)
    value = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        self.fformat = kwargs.pop('fformat')
        super(Value, self).__init__(*args, **kwargs)
        if self.fformat == 'um':
            umRes = fuseki_process.subject_and_plabel('http://um/umdpF3.ttl')
            choices = [(um['subject'], um['notation']) for um in umRes]
            choices = [('','')] + choices
            self.fields['name'].choices = choices
            sns = fuseki_process.subject_and_plabel('http://um/stashconcepts.ttl')
            sn_choices = [('','')]
            sn_choices += [(um['subject'], um['notation']) for um in sns]
            self.fields['stash_code'] = forms.ChoiceField(required=False,
                                                          choices=sn_choices)
            fcs = fuseki_process.subject_and_plabel('http://um/fieldcode.ttl')
            fc_choices = [('','')]
            fc_choices += [(um['subject'], um['notation']) for um in fcs]
            self.fields['field_code'] = forms.ChoiceField(required=False,
                                                          choices=fc_choices)
        elif self.fformat == 'cf':
            cfRes = fuseki_process.subject_and_plabel('http://cf/cf-model.ttl')
            choices = [(cf['subject'], cf['notation']) for cf in cfRes]
            choices = [('','')] + choices
            self.fields['name'].choices = choices
            sns = fuseki_process.subject_and_plabel('http://cf/cf-standard-name-table.ttl')
            sn_choices = [('','')]
            sn_choices += [(sn['subject'], sn['notation']) for sn in sns]
            self.fields['standard_name'] = forms.ChoiceField(required=False,
                                                             choices=sn_choices)
            mod = fuseki_process.subject_and_plabel('http://cf/cf-model.ttl')
            md_choices = [('','')]
            md_choices += [(mo['subject'], mo['notation']) for mo in mod]
            print md_choices
            self.fields['cf model'] = forms.ChoiceField(required=False,
                                                        choices=md_choices)
        elif self.fformat == 'grib':
            grRes = fuseki_process.subject_and_plabel('http://grib/apikeys.ttl')
            choices = [(grib['subject'], grib['notation']) for grib in grRes]
            choices = [('','')] + choices
            self.fields['name'].choices = choices
        else:
            raise ValueError('invalid format supplied: {}'.format(self.fformat))
    def clean(self):
        name = self.cleaned_data.get('name')
        _name = self.cleaned_data.get('_name')
        stcode = self.cleaned_data.get('stash_code')
        fcode = self.cleaned_data.get('field_code')
        lit = self.cleaned_data.get('value')
        st_name = self.cleaned_data.get('standard_name')
        cfmodel = self.cleaned_data.get('cf model')
        op = self.cleaned_data.get('operator')
        if name and _name:
            # only one of name and _name may be used in a valid form entry
            raise forms.ValidationError('Name, name are mutually exclusive')
        elif not name and not _name:
            # one name must be selected
            raise forms.ValidationError('a name must be selected')
        elif _name:
            n = '<http://'
            if self.fformat == 'cf':
                n += 'def.cfconventions.org/datamodel/attribute_name#{}>'
            elif self.fformat == 'um':
                n += 'reference.metoffice.gov.uk/def/um/computed_value#{}>'
            elif self.fformat == 'grib':
                n += 'reference.metoffice.gov.uk/def/grib/computed_value#{}>'
            self.cleaned_data['name'] = n.format(_name) 
        if op and not (fcode or lit or stcode or st_name or cfmodel):
            raise forms.ValidationError('if operator is set '
                                        'then a value or code is '
                                        'required')
        if not op and (fcode or lit or stcode or st_name or cfmodel):
            raise forms.ValidationError('if operator is not set '
                                        'then no value or code can be '
                                        'interpreted')
        if stcode:
            if fcode or lit:
                raise forms.ValidationError('only one of value, stash code'
                                            ' or fieldcode may be entered')
            else:
                lit = stcode
        elif fcode:
            if stcode or lit:
                raise forms.ValidationError('only one of value, stash code'
                                            ' or fieldcode may be entered')
            else:
                lit = fcode
        elif st_name:
            if lit or cfmodel:
                raise forms.ValidationError('only one of value or standard_name'
                                            ' or cf model may be entered')
            else:
                lit = st_name
        elif cfmodel:
            if lit or st_name:
                raise forms.ValidationError('only one of value or standard_name'
                                            ' or cf model may be entered')
            else:
                lit = cfmodel
        try:
            float(lit)
        except ValueError:
            if lit.startswith('http'):
                lit = '<{}>'.format(lit)
            elif lit.startswith('<http'):
                lit = lit
            else:
                lit = '"{}"'.format(lit)
        self.cleaned_data['value'] = lit
        return self.cleaned_data



def _unpack_values(vals):
    """
    return the entries for the ChoiceField choices for a list of values
    available to map
    
    """
    vals = [json.loads(aVal) for aVal in vals]
    newVals = []
    for aVal in vals:
        newS = [json.dumps(aVal), '', '', '']
        if not aVal.get('mr:subject'):
            newS[1] = aVal.get('mr:hasProperty',{}).get('mr:name', '').split('/')[-1]
        else:
            newS[1] = aVal.get('mr:subject').get('mr:hasProperty',{}).get('mr:name', '').split('/')[-1]
            newS[2] = aVal.get('mr:operator', '').split('#')[-1]
            if isinstance(aVal.get('mr:object'), unicode):
                newS[3] = aVal.get('mr:object')
            else:
                newS[3] = aVal.get('mr:object', {}).get('mr:hasProperty',{})
                newS[3] = newS[3].get('mr:name', '').split('/')[-1]
        newVals.append(newS)
    choices = [(aVal[0],'{su} {op} {ob}'.format(su=aVal[1], op=aVal[2],
                                           ob=aVal[3])) for aVal in newVals]
    return choices


class ValueMap(forms.Form):
    """
    form to define a value map
    using the available values
    
    """
    source_value = forms.ChoiceField()
    target_value = forms.ChoiceField()
    def __init__(self, *args, **kwargs):
        sc_vals = kwargs.pop('sc')
        sc = _unpack_values(sc_vals)
        tc_vals = kwargs.pop('tc')
        tc = _unpack_values(tc_vals)
        super(ValueMap, self).__init__(*args, **kwargs)
        self.fields['source_value'].choices = sc
        self.fields['target_value'].choices = tc
        
class DerivedValue(forms.Form):
    """
    form to define a derived value
    using the available values
    
    """        
    ops = fuseki_process.subject_and_plabel('http://openmath/ops.ttl')
    ops = [('','')] + [(op['subject'], op['notation']) for op in ops]
    _operator = forms.ChoiceField(choices=ops)
    _subject = forms.ChoiceField()
    _object = forms.ChoiceField(required=False)
    _object_literal = forms.CharField(required=False)
    def __init__(self, *args, **kwargs):
        comp_vals = kwargs.pop('components')
        components = _unpack_values(comp_vals)
        super(DerivedValue, self).__init__(*args, **kwargs)
        # components = [json.loads(component) for component in components]
        # components = [(json.dumps(component),component['mr:subject']['mr:hasProperty']['mr:name']) for
        #        component in components]
        self.fields['_subject'].choices = components
        self.fields['_object'].choices = [('','')] + components
    def clean(self):
        op = self.data.get('_operator')
        obj = self.data.get('_object')
        obj_lit = self.data.get('_object_literal')
        if not (obj or obj_lit):
            msg = 'an object (choice or literal) is required'
            raise forms.ValidationError(msg)
        elif obj and obj_lit:
            msg = 'the object and object_literal fields are mutually exclusive'
            raise forms.ValidationError(msg)
        elif obj_lit:
            try:
                float(obj_lit)
            except ValueError:
                raise forms.ValidationError('object_literal must be a number')
        return self.cleaned_data
            
class SelectWithPop(forms.Select):
    def render(self, name, *args, **kwargs):
        html = super(SelectWithPop, self).render(name, *args, **kwargs)
        popupplus = render_to_string("popupplus.html", {'field': name})
        return html+popupplus
        
    
class MappingMeta(forms.Form):
    """
    form to define the metadata for a mapping
    once the source, target and value maps are defined
    
    """
    isoformat = "%Y-%m-%dT%H:%M:%S.%f"
    #invertible = forms.BooleanField(required=False)
    invertible = forms.ChoiceField(choices=[('"True"', 'True'),
                                            ('"False"', 'False')])
    mapping = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={'readonly':True}))
    last_edit = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'readonly':True}))
    last_editor = forms.CharField(required=False,
                                  widget=forms.TextInput(
                                      attrs={'readonly':True}))
    people = [{'s':'', 'prefLabel':''}] + fuseki_process.get_contacts('people')
    # editor = forms.ChoiceField([(r['s'],r['prefLabel'].split('/')[-1]) for
    #                             r in people])
    editor = forms.ChoiceField([(r['s'],r['prefLabel'].split('/')[-1]) for
                                r in people], widget=SelectWithPop) 
#                                 , required=False)
#    editor = forms.ChoiceField([(r['s'],r['s'].split('/')[-1]) for
                                # r in moq.get_contacts('people')],
                                # widget=SelectWithPopUp)
    note = forms.CharField(required=False,
                           widget=forms.Textarea(attrs={'readonly':True}))
    comment = forms.CharField(required=False,
                              widget=forms.Textarea)
    reason = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'readonly':True}))
    next_reason = forms.ChoiceField(choices=[(x,x) for x in get_reasons()],
                                    required=False)
    # owners = forms.CharField(max_length=200, required=False,
    #                          widget=forms.TextInput(attrs={'readonly':True}))
    # add_owners = forms.CharField(max_length=200, required=False)
    # remove_owners = forms.CharField(max_length=200, required=False)
    # watchers = forms.CharField(max_length=200, required=False,
    #                            widget=forms.TextInput(attrs={'readonly':True}))
    # add_watchers = forms.CharField(max_length=200, required=False)
    # remove_watchers = forms.CharField(max_length=200, required=False)
    replaces = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'readonly':True}))
    status = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'readonly':True}))
    next_status = forms.ChoiceField(choices=[(x,x) for x in get_states()],
                                    required=False)
    source = forms.CharField(widget=forms.TextInput(attrs={'hidden':True}))
    target = forms.CharField(widget=forms.TextInput(attrs={'hidden':True}))
    valueMaps = forms.CharField(required=False, widget=forms.TextInput(attrs={'hidden':True}))

    def clean(self):
        """process the form"""
        source = self.data.get('source')
        map_id = self.data.get('mapping')
        # if source:
        #     src_maps = moq.multiple_mappings(fuseki_process, source)
        #     if len(src_maps) > 1:
        #         e = 'mappings already exist for this source'
        #         raise forms.ValidationError(e)
        #  worried about this, prevents updates to deprecate etc
        if map_id:
            qstr = metarelate.Mapping.sparql_retriever(map_id)
            mapping = fuseki_process.retrieve(qstr)
            if not mapping:
                raise forms.ValidationError('the mapping Id is not valid')
            if self.data.get('next_status') == '"new mapping"':
                raise forms.ValidationError('This mapping is not new')
            changed = False
            changes = []
            change_keys = [('source','source'), ('target','target'),
                           ('invertible','invertible'), ('status','status'),
                           ('replaces', 'replaces'), ('comment','note'),
                           ('next_reason', 'reason'), ('editor', 'creator'),
                           ('valueMaps', 'valueMaps')]
            for fkey, mkey in change_keys:
                if self.data.get(fkey) != mapping.get(mkey, ''):
                    changed = True
                    changes.append((mkey,(self.data.get(fkey),
                                          mapping.get(mkey, ''))))
            if not changed:
                raise forms.ValidationError('No update: mapping not changed')
        return self.cleaned_data
        

class URLwidget(forms.TextInput):
    """helper widget"""
    def render(self, name, value, attrs=None):
        if value in ('None', None):
            tpl = value
        else:
            tpl = u'<a href="%s">%s</a>' % (reverse('mapdisplay', 
                kwargs={'hashval' : value}), "go to replaces")
        return mark_safe(tpl)

    def clean(self):
        return self.cleaned_data


class HomeForm(forms.Form):
    """
    Form to support the home control panel
    and control buttons
    """
    # cache_status = forms.CharField(max_length=200, 
    #                                widget=forms.TextInput(attrs={'size': '100',
    #                                                              'readonly':True
    #                                                              }))
    # cache_state = forms.CharField(required=False,
    #                               widget=forms.Textarea(attrs={'cols': 100,
    #                                                            'rows': 50,
    #                                                            'readonly':True
    #                                                            }))

    def clean(self):
        # if self.data.has_key('load'):
        #     print 'data loaded'
        #     fuseki_process.load()
        # elif self.data.has_key('revert'):
        #     print 'save cache reverted'
        #     fuseki_process.revert()
        if self.data.has_key('save'):
            print  'cached changes saved'
            fuseki_process.save()
        elif self.data.has_key('validate'):
            print 'validate triplestore'
            self.cleaned_data['validation'] = fuseki_process.validate()
        return self.cleaned_data


class ContactForm(forms.Form):
    name = forms.CharField()
    github_id = forms.CharField()
    scheme_list = (('http://www.metarelate.net/{}/people'.format(DS),'people'),
             ('http://www.metarelate.net/{}/organisations'.format(DS),
              'organisations'))
    scheme = forms.ChoiceField(scheme_list)


class MappingForm(forms.Form):
    """Form for the display and selection of mappings"""
    mapping = forms.CharField(max_length=200)
    source = forms.CharField(max_length=200)
    target = forms.CharField(max_length=200)
    display = forms.BooleanField(required=False)
    def __init__(self, *args, **kwargs):
       super(MappingForm, self).__init__(*args, **kwargs)
       self.fields['mapping'].widget.attrs['readonly'] = True
       self.fields['source'].widget.attrs['readonly'] = True
       self.fields['target'].widget.attrs['readonly'] = True
#       self.fields['mapping'].widget = forms.HiddenInput()



#class Concept(forms.Form, BaseFormSet):
class Concept (forms.Form):
    def __init__(self, *args, **kwargs):
        super(Concept, self).__init__(*args, **kwargs)
        self.properties = formset_factory(ConceptProperty)
        self.concepts = formset_factory(Concept)

    choices = [('',''),
               ('<http://reference.metoffice.gov.uk/um/f3/UMField>', 'PP Field'),
               ('<http://reference.metoffice.gov.uk/um/f3/UMFieldCollection>', 'PP Field Set'),
               ('<http://test.wmocodes.info/def/common/grib_message>', 'GRIB message'),
               ('<http://test.wmocodes.info/def/common/grib_message_collection>', 'GRIB message Collection'),
               ('<http://def.scitools.org.uk/cfmodel/Field>', 'CF Field'),
               ('<http://def.scitools.org.uk/cfmodel/DomainAxis>', 'CF Domain Axis'),
               ('<http://def.scitools.org.uk/cfmodel/DimensionCoordinate>', 'CF Dimension Coordinate'),
               ('<http://def.scitools.org.uk/cfmodel/CellMethod>', 'CF Cell Method'),
               ]
    concept_type = forms.ChoiceField(choices=choices)


    # def __init__(self, *args, **kwargs):
    #     self.properties = formset_factory(ConceptProperty)
    #     # CODE TRICK #3 - same as #1:
    #     # pass in a valid quiz object from the view
    #     # pop removes arg, so we don't pass to the parent
    #     self.pref = kwargs.pop('pref')

class ConceptProperty(forms.Form):
    """Form for a property in a concept"""
    def __init__(self, *args, **kwargs):
        # CODE TRICK #1
        # pass in a fformat from the formset
        # use the property to build the form
        # pop removes from dict, so we don't pass to the parent
        #self.fformat = kwargs.pop('fformat')
        super(ConceptProperty, self).__init__(*args, **kwargs)
    pchoices = [('<stash>','stash'),
                ('<standard_name>','standard_name'),
                ]
    property = forms.ChoiceField(choices=pchoices)
    vchoices = [('<stash/m01s00i004>','m01s00i004'),
                ('<air_potential_temperature>','air potential temperature'),
                ]
    values = forms.ChoiceField(choices=vchoices)

class TestConceptProperty(forms.Form):
    """Form for a property in a concept"""
    def __init__(self, *args, **kwargs):
        # CODE TRICK #1
        # pass in a fformat from the formset
        # use the property to build the form
        # pop removes from dict, so we don't pass to the parent
        #self.fformat = kwargs.pop('fformat')
        super(TestConceptProperty, self).__init__(*args, **kwargs)
    pchoices = [('<standard_name>','standard_name'),
                ]
    property = forms.ChoiceField(choices=pchoices)
    vchoices = [('<air_potential_temperature>','air potential temperature'),
                ]
    values = forms.ChoiceField(choices=vchoices)


# ConceptFormSet = formset_factory(QuestionForm, formset=BaseConceptFormSet)


## https://djangosnippets.org/snippets/1955/

## https://djangosnippets.org/snippets/1863/
## https://djangosnippets.org/snippets/1389/
