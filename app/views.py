from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import BiomSearchJob, BiomSearchForm
import cPickle
import os

context = {'flash': None, 'is_example': True}
# HACK: Really dirty stuff going on here, won't modularize at all! WTF!
# Paths are bieng set in OS-depedent manner, not using dynamic paths
# Find a better way, and quick! Maybe checkout STATIC_ROOT for production
example_data_path = os.path.join(settings.STATIC_URL, "example_data/")
example_data_abs_path = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0]

# load example job details as if it was loaded from database
example_job_path = os.path.join(example_data_abs_path, "example_data/")
example_job_path = os.path.join(example_job_path, "example_job.pcl")
example_job = cPickle.load(open(example_job_path, "r"))


def index(request):
    """Home page route. Contains a BIOM search form for submission which is
    handled by guest_search() or search() in search.py depending on user.
    HTML file can be found in templates/app/index.html

    :param request: Request object
    :return: Renders the home page
    """
    form = BiomSearchForm()
    context['form'] = form

    return render(request, 'app/index.html', context)


def contact(request):
    """Contact page route. Static HTML can be found in
    templates/app/contact.html

    :param request: Request object
    :return: Renders the contact page
    """
    return render(request, 'app/contact.html', context)


def help(request):
    """Help page route. Static HTML can be found in
    templates/app/help.html

    :param request: Request object
    :return: Renders the help page
    """
    return render(request, 'app/help.html', context)


def ex_details(request):
    """Example job details page route. HTML can be found in
    templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job details page
    """
    msg_storage = messages.get_messages(request)

    context["file_path"] = os.path.join(example_data_path, "example_input.biom")
    context["job"] = example_job
    # I had to do the line below: you can't get a relational criteria list since
    # the job technically doesn't exist in the DB. Another way to handle making
    # a "fake" job is to create a user which is publicly accessible and jobs
    # which are publicly accessible which might be possible in future iterations
    context["criteria"] = ", ".join(["Animal/Human", "Plant", "Soil"])
    context["flash"] = msg_storage

    return render(request, 'job/details.html', context)


def ex_ranking(request):
    """Example job ranking page route. HTML can be found in
    templates/job/ranking.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job ranking page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/ranking.html', context)


def ex_heatmap(request):
    """Example job heatmap page route. HTML can be found in
    templates/job/heatmap.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job ranking page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/heatmap.html', context)


def ex_pcoa_reps(request):
    """Example job representative samples PCOA page route. HTML can be found
    in templates/job/pcoa_reps.html. This HTML file is shared by the job views
    of actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job representative samples PCOA page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/pcoa_reps.html', context)


def ex_pcoa_similar(request):
    """Example job most similar samples PCOA page route. HTML can be found
    in templates/job/pcoa_250.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job most similar samples PCOA page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage

    return render(request, 'job/pcoa_250.html', context)


def ex_dend_reps(request):
    """Example job representative dendrogram page route. HTML can be found
    in templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job representative dendrogram page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/dend_reps.html', context)


def ex_dend_similar(request):
    """Example job most similar dendrogram route. HTML can be found in
    templates/job/details.html. This HTML file is shared by the job views of
    actual processed jobs, be careful when editing.

    :param request: Request object
    :return: Renders the example job most similar dendrogram page
    """
    msg_storage = messages.get_messages(request)

    context["data_path"] = example_data_path
    context["job"] = example_job
    context["flash"] = msg_storage
    return render(request, 'job/dend_250.html', context)


def handler404(request):
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))

    response.status_code = 404
    return response
