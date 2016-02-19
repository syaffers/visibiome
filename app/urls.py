from django.conf.urls import url
from . import auth, views

app_name = 'app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^tutorial/$', views.tutorial, name='tutorial'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^login/$', auth.login, name='login'),
    url(r'^logout/$', auth.logout, name='logout'),
    url(r'^register/$', auth.register, name='register'),
]
