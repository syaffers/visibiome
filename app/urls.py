from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import auth, jobs, views, search

app_name = 'app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^tutorial/$', views.tutorial, name='tutorial'),

    url(r'^login/$', auth.login, name='login'),
    url(r'^logout/$', auth.logout, name='logout'),
    url(r'^register/$', auth.register, name='register'),
    url(r'^update/$', auth.update_details, name='update_details'),

    url(r'^guest_search/$', search.guest_search, name='guest_search'),
    url(r'^search/$', search.user_search, name='search'),

    url(r'^job/(?P<job_id>[0-9]+)$', jobs.details, name='job_details'),
    url(r'^job/(?P<job_id>[0-9]+)/remove$', jobs.remove, name='job_remove'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
