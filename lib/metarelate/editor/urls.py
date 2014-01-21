from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'editor.app.views.home', name='home'),
    url(r'^invalid_mappings/$', 'editor.app.views.invalid_mappings',
        name='invalid_mappings'),
    url(r'^fsearch/$', 'editor.app.views.fsearch', name='fsearch'),
    url(r'^review/$', 'editor.app.views.review', name='review'),
    url(r'^search/(?P<fformat>[^/]+)/$', 'editor.app.views.search',
        name='search'),
    url(r'^searchproperty/(?P<fformat>[^/]+)/$',
        'editor.app.views.search_property', name='search_property'),
    url(r'^searchmaps/$', 'editor.app.views.search_maps', name='search_maps'),
    url(r'^mappingformats/$', 'editor.app.views.mapping_formats',
        name='mapping_formats'),
    url(r'^definemediator/(?P<mediator>[^/]+)/(?P<fformat>[^/]+)/$',
        'editor.app.views.define_mediator', name='define_mediator'),
    url(r'^createmediator/(?P<fformat>[^/]+)/$',
        'editor.app.views.create_mediator', name='create_mediator'),
    url(r'^mappingconcepts/$', 'editor.app.views.mapping_concepts',
        name='mapping_concepts'),
    url(r'^defineproperty/(?P<fformat>[^/]+)/$',
        'editor.app.views.define_property', name='define_property'),
    url(r'^valuemap/$', 'editor.app.views.value_maps', name='value_maps'),
    url(r'^definevaluemap', 'editor.app.views.define_valuemap',
        name='define_valuemaps'),
    url(r'^derivedvalue/(?P<role>[^/]+)/$', 'editor.app.views.derived_value', 
        name='derived_value'),
    url(r'^mappingedit/$', 'editor.app.views.mapping_edit', name='mapping_edit')
)
