from django.conf.urls import url
from . import auth, views, search

app_name = 'app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^job/(?P<job_id>[0-9]+)$', views.job_detail, name='job_detail'),
    url(r'^tutorial/$', views.tutorial, name='tutorial'),

    url(r'^login/$', auth.login, name='login'),
    url(r'^logout/$', auth.logout, name='logout'),
    url(r'^register/$', auth.register, name='register'),
    url(r'^update/$', auth.update_details, name='update_details'),

    url(r'^guest_search/$', search.guest_search, name='guest_search'),
    url(r'^search/$', search.user_search, name='search'),
]
