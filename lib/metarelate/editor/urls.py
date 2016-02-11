from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'metarelate.editor.app.views.home', name='home'),
    url(r'^homegraph/$', 'metarelate.editor.app.views.homegraph', name='homegraph'),
    url(r'^controlpanel/$', 'metarelate.editor.app.views.controlpanel', name='control_panel'),
    url(r'^upload/(?P<importer>[^/]+)/$', 'metarelate.editor.app.views.upload', name='upload'),
    url(r'^newmapping/$', 'metarelate.editor.app.views.newmapping', name='newmapping'),
    url(r'^anewmapping/$', 'metarelate.editor.app.views.anewmapping', name='anewmapping'),

    url(r'^list_mappings/(?P<validate>[^/]+)/$', 'metarelate.editor.app.views.list_mappings',
        name='list_mappings'),
    url(r'^review/$', 'metarelate.editor.app.views.review', name='review'),
    url(r'^search/$', 'metarelate.editor.app.views.search', name='search'),
    url(r'^add_contact/$', 'metarelate.editor.app.views.add_contact', name='add_contact'),
    url(r'^mapping/(?P<mapping_id>[^/]+)/$', 'metarelate.editor.app.views.mapping', name='mapping'),
    url(r'^mappingviewgraph/(?P<mapping_id>[^/]+)/$', 'metarelate.editor.app.views.mapping_view_graph', name='mapping_view_graph'),
    url(r'^mapping_json/(?P<mapping_id>[^/]+)/$', 'metarelate.editor.app.views.mapping_json', name='mapping_json'),
    url(r'^component/(?P<component_id>[^/]+)/$', 'metarelate.editor.app.views.component', name='component'),
    url(r'^componentviewgraph/(?P<component_id>[^/]+)/$', 'metarelate.editor.app.views.component_view_graph', name='component_view_graph'),
    url(r'^latest_sha/$', 'metarelate.editor.app.views.latest_sha', name='latest_sha'),
    url(r'^login/$', 'metarelate.editor.app.views.login', name='login'),
    url(r'^email-sent/', 'metarelate.editor.app.views.validation_sent'),
    url(r'^logout/$', 'metarelate.editor.app.views.logout', name='logout'),
    url(r'^done/$', 'metarelate.editor.app.views.done', name='done'),
    url(r'^ajax-auth/(?P<backend>[^/]+)/$', 'metarelate.editor.app.views.ajax_auth',
        name='ajax-auth'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
)
