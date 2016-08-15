from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BiomSearchJob, BiomSearchForm

context = {'flash': None}


def index(request):
    """
    Home page route. Contains a BIOM search form for submission which is
    handled by guest_search() or search() in search.py depending on user.
    HTML file can be found in templates/app/index.html

    :param request: Request object
    :return: Renders the home page
    """
    form = BiomSearchForm()
    context['form'] = form

    return render(request, 'app/index.html', context)


def contact(request):
    """
    Contact page route. Static HTML can be found in
    templates/app/contact.html

    :param request: Request object
    :return: Renders the contact page
    """
    return render(request, 'app/contact.html', context)


def help(request):
    """
    Tutorial page route. Static HTML can be found in
    templates/app/help.html

    :param request: Request object
    :return: Renders the help page
    """
    return render(request, 'app/help.html', context)


@login_required
def dashboard(request):
    """
    Dashboard page route. Static HTML can be found in
    templates/app/dashboard.html

    :param request: Request object
    :return: Renders the tutorial page
    """
    msg_storage = messages.get_messages(request)
    jobs = BiomSearchJob.objects.filter(user=request.user.id)
    jobs = jobs.order_by('-updated_at').all()

    context['jobs'] = jobs
    context['flash'] = msg_storage
    return render(request, 'app/dashboard.html', context)
