from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import BiomSearchForm
from .models import Job
from .tasks import run_fibs


def index(request):
    form = BiomSearchForm()
    # dereference the fields from the form so we can slice
    biom_fields = [f for f in form][:2]
    ecosystems = form
    return render(
        request, 'app/index.html',
        {
            'biom_fields': biom_fields,
            'ecosystems': ecosystems,
        }
    )


def contact(request):
    return render(request, 'app/contact.html')


def tutorial(request):
    return render(request, 'app/tutorial.html')


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
            return redirect('/dashboard')
        messages.add_message(request, messages.SUCCESS, "Task started for "
                                                        "fibs(%s)" % n)
        return redirect('/dashboard')
    return redirect('/dashboard')


@login_required
def dashboard(request):
    msg_storage = messages.get_messages(request)
    jobs = Job.objects.filter(user=request.user.id)\
        .order_by('-updated_at').all()[:5]
    return render(request, 'app/dashboard.html',
                  {'jobs': jobs, 'flash': msg_storage})


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if job.user_id == request.user.id:
        return render(request, 'app/job.html', {'job': job})
    else:
        messages.add_message(request, messages.ERROR,
                             "Unauthorized access to Job " + job_id)
        return redirect('/dashboard')
