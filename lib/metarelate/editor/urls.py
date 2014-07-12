from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'metarelate.editor.app.views.home', name='home'),
    url(r'^newmapping/$', 'metarelate.editor.app.views.newmapping', name='newmapping'),
    url(r'^invalid_mappings/$', 'metarelate.editor.app.views.invalid_mappings',
        name='invalid_mappings'),
    url(r'^fsearch/$', 'metarelate.editor.app.views.fsearch', name='fsearch'),
    url(r'^review/$', 'metarelate.editor.app.views.review', name='review'),
    url(r'^search/(?P<fformat>[^/]+)/$', 'metarelate.editor.app.views.search',
        name='search'),
    url(r'^searchproperty/(?P<fformat>[^/]+)/$',
        'metarelate.editor.app.views.search_property', name='search_property'),
    url(r'^searchmaps/$', 'metarelate.editor.app.views.search_maps', name='search_maps'),
    # url(r'^mappingformats/$', 'metarelate.editor.app.views.mapping_formats',
    #     name='mapping_formats'),
    url(r'^definemediator/(?P<mediator>[^/]+)/(?P<fformat>[^/]+)/$',
        'metarelate.editor.app.views.define_mediator', name='define_mediator'),
    url(r'^createmediator/(?P<fformat>[^/]+)/$',
        'metarelate.editor.app.views.create_mediator', name='create_mediator'),
    url(r'^mappingconcepts/$', 'metarelate.editor.app.views.mapping_concepts',
        name='mapping_concepts'),
    url(r'^defineproperty/(?P<fformat>[^/]+)/$',
        'metarelate.editor.app.views.define_property', name='define_property'),
    url(r'^valuemap/$', 'metarelate.editor.app.views.value_maps', name='value_maps'),
    url(r'^definevaluemap', 'metarelate.editor.app.views.define_valuemap',
        name='define_valuemaps'),
    url(r'^derivedvalue/(?P<role>[^/]+)/$', 'metarelate.editor.app.views.derived_value', 
        name='derived_value'),
    url(r'^mappingedit/$', 'metarelate.editor.app.views.mapping_edit', name='mapping_edit'),
    url(r'^add_contact/$', 'metarelate.editor.app.views.add_contact', name='add_contact')
)
