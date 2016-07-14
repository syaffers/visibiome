from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BiomSearchJob

context = {'flash': None}


@login_required
def details(request, job_id):
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
            request, messages.ERROR,
            "Unauthorized access to Job {}".format(job.id)
        )
        return redirect('app:dashboard')


@login_required
def remove(request, job_id):
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)
    if job.user_id == request.user.id:
        deleted_job_id = job.id
        job.delete()

        messages.add_message(
            request, messages.SUCCESS,
            "Job {} successfully deleted".format(deleted_job_id)
        )
        context['flash'] = msg_storage
        return redirect('app:dashboard')

    else:
        messages.add_message(
            request, messages.ERROR, "Unauthorized access to Job " + job_id
        )
        return redirect('app:dashboard')

