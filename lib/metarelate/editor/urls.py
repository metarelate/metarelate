from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'metarelate.editor.app.views.home', name='home'),
    url(r'^homegraph/$', 'metarelate.editor.app.views.homegraph', name='homegraph'),
    url(r'^controlpanel/$', 'metarelate.editor.app.views.controlpanel', name='control_panel'),
    url(r'^newmapping/$', 'metarelate.editor.app.views.newmapping', name='newmapping'),
    url(r'^anewmapping/$', 'metarelate.editor.app.views.anewmapping', name='anewmapping'),

    url(r'^invalid_mappings/$', 'metarelate.editor.app.views.invalid_mappings',
        name='invalid_mappings'),
    url(r'^review/$', 'metarelate.editor.app.views.review', name='review'),
    url(r'^search/$', 'metarelate.editor.app.views.search', name='search'),
    # url(r'^definemediator/(?P<mediator>[^/]+)/(?P<fformat>[^/]+)/$',
    #     'metarelate.editor.app.views.define_mediator', name='define_mediator'),
    # url(r'^createmediator/(?P<fformat>[^/]+)/$',
    #     'metarelate.editor.app.views.create_mediator', name='create_mediator'),
    # url(r'^valuemap/$', 'metarelate.editor.app.views.value_maps', name='value_maps'),
    # url(r'^definevaluemap', 'metarelate.editor.app.views.define_valuemap',
    #     name='define_valuemaps'),
    # url(r'^derivedvalue/(?P<role>[^/]+)/$', 'metarelate.editor.app.views.derived_value', 
    #     name='derived_value'),
    # url(r'^mappingedit/$', 'metarelate.editor.app.views.mapping_edit', name='mapping_edit'),
    url(r'^add_contact/$', 'metarelate.editor.app.views.add_contact', name='add_contact'),
    # url(r'^mappingview/$', 'metarelate.editor.app.views.mapping_view', name='mapping_view'),
    url(r'^mapping/(?P<mapping_id>[^/]+)/$', 'metarelate.editor.app.views.mapping', name='mapping'),
    url(r'^mappingviewgraph/(?P<mapping_id>[^/]+)/$', 'metarelate.editor.app.views.mapping_view_graph', name='mapping_view_graph'),
    url(r'^component/(?P<component_id>[^/]+)/$', 'metarelate.editor.app.views.component', name='component'),
    url(r'^componentviewgraph/(?P<component_id>[^/]+)/$', 'metarelate.editor.app.views.component_view_graph', name='component_view_graph'),
    url(r'^retrievemappings/$', 'metarelate.editor.app.views.retrieve_mappings', name='retrieve_mappings'),
)
