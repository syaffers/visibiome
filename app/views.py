from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Job, BiomSearchJob, BiomSearchForm
from .tasks import run_fibs


def index(request):
    """
    Home page route. Contains a BIOM search form for submission which is
    handled by guest_search() or search() in search.py depending on user.
    HTML file can be found in templates/app/index.html

    :param request: Request object
    :return: Renders the home page
    """
    form = BiomSearchForm()

    return render(request, 'app/index.html', {'form': form, 'flash': None})


def contact(request):
    """
    Contact page route. Static HTML can be found in
    templates/app/contact.html

    :param request: Request object
    :return: Renders the contact page
    """
    return render(request, 'app/contact.html', {'flash': None})


def tutorial(request):
    """
    Tutorial page route. Static HTML can be found in
    templates/app/tutorial.html

    :param request: Request object
    :return: Renders the tutorial page
    """
    return render(request, 'app/tutorial.html', {'flash': None})


def calculate(request):
    if request.method == "POST":
        n = request.POST['number']
        j = Job(user=User.objects.filter(pk=request.user.id).first())
        try:
            n = int(n)
            j.save()
            run_fibs.delay(j.id, n)
        except ValueError:
            messages.add_message(request, messages.ERROR, "Value error.")
            return redirect('app:dashboard')
        messages.add_message(request, messages.SUCCESS, "Task started for "
                                                        "fibs(%s)" % n)
        return redirect('app:dashboard')
    return redirect('app:dashboard')


@login_required
def dashboard(request):
    msg_storage = messages.get_messages(request)
    jobs = BiomSearchJob.objects.filter(user=request.user.id)
    jobs = jobs.order_by('-updated_at').all()[:5]
    return render(request, 'app/dashboard.html',
                  {'jobs': jobs, 'flash': msg_storage})


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(BiomSearchJob, id=job_id)
    if job.user_id == request.user.id:
        return render(request, 'app/job.html', {'job': job, 'flash': None})
    else:
        messages.add_message(request, messages.ERROR,
                             "Unauthorized access to Job " + job_id)
        return redirect('app:dashboard')
