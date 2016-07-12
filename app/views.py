from django.shortcuts import render, redirect, get_object_or_404
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


def tutorial(request):
    """
    Tutorial page route. Static HTML can be found in
    templates/app/tutorial.html

    :param request: Request object
    :return: Renders the tutorial page
    """
    return render(request, 'app/tutorial.html', context)


@login_required
def dashboard(request):
    msg_storage = messages.get_messages(request)
    jobs = BiomSearchJob.objects.filter(user=request.user.id)
    jobs = jobs.order_by('-updated_at').all()[:5]

    context['jobs'] = jobs
    context['flash'] = msg_storage
    return render(request, 'app/dashboard.html', context)


@login_required
def job_detail(request, job_id):
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)
    if job.user_id == request.user.id:
        if job.otu_text == "Paste OTU table here":
            context["input_type"] = 1
            context["input"] = job.biom_file
        else:
            context["input_type"] = 0
            context["input"] = job.otu_text
        context['job'] = job
        context['criteria'] = ", ".join(map(str, job.criteria.all()))
        context['flash'] = msg_storage
        return render(request, 'app/job.html', context)

    else:
        messages.add_message(
            request, messages.ERROR, "Unauthorized access to Job " + job_id
        )
        return redirect('app:dashboard')
