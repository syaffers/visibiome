from django.conf import settings
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from posixpath import basename, dirname, join
from .models import BiomSearchJob
from .tasks import validate_biom

# general context for all pages
context = {"flash": None, "is_example": False, "is_public": True}
job_is_public_message = "That job was not made public by the owner"
json_encoder = DjangoJSONEncoder()


def details_public(request, job_id):
    """Job details page route for public jobs. Static HTML can be found in
    templates/job/details.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.is_public or (job.user_id == request.user.pk):
        context["job"] = job
        context["criteria"] = ", ".join(map(str, job.criteria.all()))
        context["flash"] = msg_storage
        return render(request, 'job/details.html', context)
    else:
        messages.add_message(request, messages.ERROR, job_is_public_message)
        return redirect('app:dashboard')


def ranking_public(request, job_id):
    """Job ranking page route for public jobs. Static HTML can be found in
    templates/job/ranking.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.is_public or (job.user_id == request.user.pk):
        job_dir = dirname(job.biom_file.url)
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["ranking_file_path"] = join(job_dir, job.file_safe_name() + ".json")
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        context["barchart_files"] = json_encoder.encode([])

        return render(request, 'job/ranking.html', context)
    else:
        messages.add_message(request, messages.ERROR, job_is_public_message)
        return redirect('app:dashboard')


def pcoa_reps_public(request, job_id):
    """Job representative PCOA page route for public jobs. Static HTML can be
    found in templates/job/pcoa_reps.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.is_public or (job.user_id == request.user.pk):
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["pcoa_file_path"] = join(dirname(job.biom_file.url), "pcoa_1000.json")
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/pcoa_reps.html', context)
    else:
        messages.add_message(request, messages.ERROR, job_is_public_message)
        return redirect('app:dashboard')


def dend_reps_public(request, job_id):
    """Job representative dendrogram page route for public jobs. Static HTML
    can be found in templates/job/dend_reps.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.is_public or (job.user_id == request.user.pk):
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["dendrogram_file_path"] = join(dirname(job.biom_file.url), "d3dendrogram.json")
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/dend_reps.html', context)
    else:
        messages.add_message(request, messages.ERROR, job_is_public_message)
        return redirect('app:dashboard')
