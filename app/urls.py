from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import auth, jobs, views, search

app_name = 'app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^help/$', views.help, name='help'),

    url(r'^help/example-job/details$', views.ex_details,
        name='example_job_details'),
    url(r'^help/example-job/ranking$', views.ex_ranking,
        name='example_job_ranking'),
    url(r'^help/example-job/heatmap$', views.ex_heatmap,
        name='example_job_heatmap'),
    url(r'^help/example-job/pcoa-representatives$', views.ex_pcoa_reps,
        name='example_job_pcoa_reps'),
    url(r'^help/example-job/pcoa-250$', views.ex_pcoa_similar,
        name='example_job_pcoa_similar'),
    url(r'^help/example-job/dend-representatives$', views.ex_dend_reps,
        name='example_job_dend_reps'),
    url(r'^help/example-job/dend-similar$', views.ex_dend_similar,
        name='example_job_dend_similar'),

    url(r'^login/$', auth.login, name='login'),
    url(r'^logout/$', auth.logout, name='logout'),
    url(r'^register/$', auth.register, name='register'),
    url(r'^update/$', auth.update_details, name='update_details'),

    url(r'^guest_search/$', search.guest_search, name='guest_search'),
    url(r'^search/$', search.user_search, name='search'),

    url(r'^dashboard/$', jobs.dashboard, name='dashboard'),
    url(r'^job/(?P<job_id>[0-9]+)/details$', jobs.details, name='job_details'),
    url(r'^job/(?P<job_id>[0-9]+)/ranking$', jobs.ranking, name='job_ranking'),
    url(r'^job/(?P<job_id>[0-9]+)/heatmap$', jobs.heatmap, name='job_heatmap'),
    url(r'^job/(?P<job_id>[0-9]+)/pcoa-representatives$', jobs.pcoa_reps,
        name='job_pcoa_reps'),
    url(r'^job/(?P<job_id>[0-9]+)/pcoa-250$', jobs.pcoa_similar,
        name='job_pcoa_similar'),
    url(r'^job/(?P<job_id>[0-9]+)/dend-representatives$', jobs.dend_reps,
        name='job_dend_reps'),
    url(r'^job/(?P<job_id>[0-9]+)/dend-250$', jobs.dend_similar,
        name='job_dend_similar'),
    url(r'^job/(?P<job_id>[0-9]+)/remove$', jobs.remove, name='job_remove'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
