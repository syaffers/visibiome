from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, render_to_response
from posixpath import join
from .models import BiomSearchJob, BiomSearchForm
import cPickle
import os

context = {'flash': None, 'is_example': True}
json_encoder = DjangoJSONEncoder()


def index(request):
    """Home page route. Contains a BIOM search form for submission which is
    handled by guest_search() or search() in search.py depending on user.
    HTML file can be found in templates/app/index.html
    """
    form = BiomSearchForm()
    context['form'] = form

    return render(request, 'app/index.html', context)


def contact(request):
    """Contact page route. Static HTML can be found in
    templates/app/contact.html
    """
    return render(request, 'app/contact.html', context)


def help(request):
    """Help page route. Static HTML can be found in
    templates/app/help.html
    """
    return render(request, 'app/help.html', context)


def ex_details(request):
    """Example job details page route. HTML can be found in
    templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    context["example_biom_file"] = \
        staticfiles_storage.url("example_data/example_input.biom")
    context["job"] = example_job
    context["criteria"] = ", ".join(map(str, example_job.criteria.all()))
    context["flash"] = msg_storage

    return render(request, 'job/details.html', context)


def ex_ranking(request):
    """Example job ranking page route. HTML can be found in
    templates/job/ranking.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["ranking_file_path"] = \
        staticfiles_storage.url("example_data/LD_ptepar_single.json")
    context["samples"] = json_encoder.encode(job_samples)
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/ranking.html', context)


def ex_plot_summary(request):
    """Example job plot summary page route. HTML can be found in
    templates/job/plot_summary.html. This HTML file is shared by the job views
    of actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_dir = staticfiles_storage.url("example_data")
    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["job_dir"] = job_dir
    context["samples"] = json_encoder.encode(job_samples)
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/plot_summary.html', context)


def ex_heatmap(request):
    """Example job heatmap page route. HTML can be found in
    templates/job/heatmap.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_dir = staticfiles_storage.url("example_data")

    context["job_dir"] = job_dir
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/heatmap.html', context)


def ex_pcoa_reps(request):
    """Example job representative samples PCOA page route. HTML can be found
    in templates/job/pcoa_reps.html. This HTML file is shared by the job views
    of actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["pcoa_file_path"] = \
        staticfiles_storage.url("example_data/pcoa_1000.json")
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/pcoa_reps.html', context)


def ex_pcoa_similar(request):
    """Example job most similar samples PCOA page route. HTML can be found
    in templates/job/pcoa_250.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["pcoa_file_path"] = \
        staticfiles_storage.url("example_data/pcoa_250.csv")
    context["samples"] = json_encoder.encode(job_samples)
    context["job"] = example_job
    context["flash"] = msg_storage

    return render(request, 'job/pcoa_250.html', context)


def ex_dend_reps(request):
    """Example job representative dendrogram page route. HTML can be found
    in templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["dendrogram_file_path"] = \
        staticfiles_storage.url("example_data/d3dendrogram.json")
    context["samples"] = json_encoder.encode(job_samples)
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/dend_reps.html', context)


def ex_dend_similar(request):
    """Example job most similar dendrogram route. HTML can be found in
    templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.
    """
    msg_storage = messages.get_messages(request)
    example_job = BiomSearchJob.objects.filter(pk=1)[0]

    job_samples = map(
        lambda sample: sample.name, example_job.samples.all()
    )

    context["dendrogram_file_path"] = \
        staticfiles_storage.url("example_data/d3dendrogram_sub.json")
    context["samples"] = json_encoder.encode(job_samples)
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/dend_250.html', context)


def handler404(request):
    response = render_to_response('404.html', context,
                                  context_instance=RequestContext(request))

    response.status_code = 404
    return response
