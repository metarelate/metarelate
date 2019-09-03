# (C) British Crown Copyright 2013 - 2015, Met Office
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
                          # widget=forms.TextInput(attrs={'readonly':readonly, 'size':'100%'}))
                          widget=URLwidget(attrs={'readonly':readonly, 'size':'100%'}))
    
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

            
class SelectWithPop(forms.Select):
    def render(self, name, *args, **kwargs):
        html = super(SelectWithPop, self).render(name, *args, **kwargs)
        popupplus = render_to_string("popupplus.html", {'field': name})
        return html+popupplus        


class URLwidget(forms.TextInput):
    """helper widget"""
    def render(self, name, value, attrs=None):
        if value in ('None', None):
            tpl = value
        else:
            # tpl = u'<a href="%s">%s</a>' % (reverse('mapdisplay',
            #     kwargs={'hashval' : value}), "go to replaces")

            tpl = u'<a href="{u}">{u}</a>'.format(u=value.data.rstrip('>').lstrip('<'))
        return mark_safe(tpl)

    def clean(self):
        return self.cleaned_data


class CPanelForm(forms.Form):
    """
    Form to support the home control panel
    and control buttons
    """
    def clean(self):
        if self.data.has_key('validate'):
            self.cleaned_data['validate'] = True
        elif self.data.has_key('branch'):
            self.cleaned_data['branch'] = True
        elif self.data.has_key('delete'):
            self.cleaned_data['delete'] = True
        elif self.data.has_key('merge'):
            self.cleaned_data['merge'] = True
        return self.cleaned_data

class UploadForm(forms.Form):
    docfile = forms.FileField(label='Select a file', 
                              help_text='max. 2 megabytes')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.branch = kwargs.pop('branch')
        if len(args) == 2:
            self.upfile = args[1].get('docfile', None)
        try:
            from metarelate_metocean.upload import stashc_cfname, grib2_cfname, stash_grib, mapping_jsonld
            importer = kwargs.pop('importer')
            if importer == 'stashc_cfname':
                self.uploader = stashc_cfname
            elif importer == 'grib2_cfname':
                self.uploader = grib2_cfname
            elif importer == 'stash_grib':
                self.uploader = stash_grib
            elif importer == 'general':
                self.uploader = mapping_jsonld
        except ImportError:
            self.uploader = None
        super(UploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        # validate file
        if self.upfile is not None and self.uploader is not None:
            try:
                self.uploader.parse_file(fuseki_process, self.upfile,
                                         self.user, self.branch)
            except ValueError, e:
                verrs = [forms.ValidationError('The file failed to parse;'
                                               ' in order to process this file'
                                               ' you should consider:')]
                for err in e.message.split('||\n'):
                    verrs.append(forms.ValidationError(err))
                raise forms.ValidationError(verrs)
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
