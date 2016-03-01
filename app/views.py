from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Job
from .tasks import run_fibs


def index(request):
    return render(request, 'app/index.html')


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
    jobs = Job.objects.filter(user=request.user.id).all()
    return render(request, 'app/dashboard.html',
                  {'jobs': jobs, 'flash': msg_storage})


@login_required
def job_detail(request, job_id):
    job = Job.objects.filter(pk=job_id).first()
    if job.user_id == request.user.id:
        return render(request, 'app/job.html', {'job': job})
    else:
        messages.add_message(request, messages.ERROR,
                             "Unauthorized access to Job " + job_id)
        return redirect('/dashboard')
