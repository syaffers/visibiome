from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from posixpath import basename, dirname, join
from .models import BiomSearchJob
from .tasks import validate_biom

# general context for all pages
context = {"flash": None, "is_example": False, "is_public": False}
unauthorized_access_message = "Unauthorized access."
json_encoder = DjangoJSONEncoder()

# default number of jobs per page
jobs_per_page_default_limit = 10


@login_required
def dashboard(request):
    """Dashboard page route. Static HTML can be found in
    templates/app/dashboard.html
    """
    msg_storage = messages.get_messages(request)
    all_jobs = BiomSearchJob.objects.filter(user=request.user.pk) \
        .order_by('-created_at')

    page_number = request.GET.get('page')
    limit = request.GET.get('limit') or jobs_per_page_default_limit
    dashboard_paginator = Paginator(all_jobs, limit)

    try:
        jobs_in_current_page = dashboard_paginator.page(page_number)
    except PageNotAnInteger:
        # if page is not an integer, deliver first page.
        jobs_in_current_page = dashboard_paginator.page(1)
        page_number = 1
    except EmptyPage:
        # if page is out of range (e.g. 9999), deliver last page of results.
        jobs_in_current_page = dashboard_paginator.page(paginator.num_pages)

    context['jobs'] = jobs_in_current_page
    context['pages'] = dashboard_paginator.page_range
    context['curr_page_number'] = int(page_number)
    context['limit'] = limit
    context['flash'] = msg_storage
    return render(request, 'app/dashboard.html', context)


@login_required
def remove(request, job_id):
    """Remove job route. Called from app/static/script.js"""
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        deleted_job_name = job.name
        job.delete()

        messages.add_message(
            request, messages.SUCCESS,
            "{} successfully deleted".format(deleted_job_name)
        )
        context["flash"] = msg_storage
        return redirect('app:dashboard')
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def rerun(request, job_id):
    """Rerun a job route. Called from app/static/script.js"""
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        if job.status == BiomSearchJob.COMPLETED or job.status == BiomSearchJob.STOPPED:
            job.status = BiomSearchJob.RERUN
            job.save()
            validate_biom.delay(job, job.biom_file.path)

            messages.add_message(
                request, messages.SUCCESS,
                "{} queued for re-running".format(job.name)
            )
            context["flash"] = msg_storage
            return redirect('app:dashboard')

        else:
            messages.add_message(request, messages.ERROR, "Cannot re-run a currently running job.")
            return redirect('app:dashboard')
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def make_public(request, job_id):
    """Route for making jobs public. Called in details.html page"""
    msg_storage = messages.get_messages(request)
    if request.method == "POST":
        job = get_object_or_404(BiomSearchJob, id=job_id)

        if job.user_id == request.user.pk:
            job.is_public = True
            job.save()

            public_path = reverse("app:public_job_details", kwargs={"job_id": job.pk})
            msg_base = 'Job is now public and viewable at <a href="{}">this link</a>'

            messages.add_message(request, messages.SUCCESS,
                                 msg_base.format(public_path),
                                 extra_tags='safe')
            return redirect('app:job_details', job_id=job.pk)
        else:
            messages.add_message(request, messages.ERROR, unauthorized_access_message)
            return redirect("app:job_details", job_id=job.pk)


@login_required
def details(request, job_id):
    """Job details page route. Static HTML can be found in
    templates/job/details.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        context["job"] = job
        context["criteria"] = ", ".join(map(str, job.criteria.all()))
        context["flash"] = msg_storage
        return render(request, 'job/details.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def details_json(request, job_id):
    """Job status json route. Called from app/static/script.js"""
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        o = {
            "status": 200,
            "data": {
                "id": job.pk,
                "error": job.get_error_code_display(),
                "errorCode": job.error_code,
                "status": job.get_status_display(),
                "statusCode": job.status,
                "lastRunAt": job.last_run_at,
                "updatedAt": job.updated_at,
            }
        }

        return JsonResponse(o)
    else:
        o = {
            "status": 401,
            "data": unauthorized_access_message
        }
        return JsonResponse(o, status=401)


@login_required
def ranking(request, job_id):
    """Job ranking page route. Static HTML can be found in
    templates/job/ranking.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
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
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def plot_summary(request, job_id):
    """Plot summary page route. Static HTML can be found in
    templates/job/plot_summary.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_dir = dirname(job.biom_file.url)
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["job_dir"] = job_dir
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/plot_summary.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def heatmap(request, job_id):
    """Job heatmap page route. Static HTML can be found in
    templates/job/heatmap.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_dir = dirname(job.biom_file.url)

        context["job_dir"] = job_dir
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/heatmap.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def pcoa_reps(request, job_id):
    """Job representative PCOA page route. Static HTML can be found in
    templates/job/pcoa_reps.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["pcoa_file_path"] = join(dirname(job.biom_file.url), "pcoa_1000.json")
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/pcoa_reps.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def pcoa_similar(request, job_id):
    """Job most similar samples PCOA page route. Static HTML can be found in
    templates/job/pcoa_250.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["pcoa_file_path"] = join(dirname(job.biom_file.url), "pcoa_250.csv")
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/pcoa_250.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def dend_reps(request, job_id):
    """Job representative dendrogram page route. Static HTML can be found in
    templates/job/dend_reps.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["dendrogram_file_path"] = join(dirname(job.biom_file.url), "d3dendrogram.json")
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/dend_reps.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')


@login_required
def dend_similar(request, job_id):
    """Job most similar samples dendrogram page route. Static HTML can be found
    in templates/job/dend_250.html
    """
    msg_storage = messages.get_messages(request)
    job = get_object_or_404(BiomSearchJob, id=job_id)

    if job.user_id == request.user.pk:
        job_samples = map(
            lambda sample: sample.name, job.samples.all()
        )

        context["dendrogram_file_path"] = join(dirname(job.biom_file.url), "d3dendrogram_sub.json")
        context["samples"] = json_encoder.encode(job_samples)
        context["job"] = job
        context["flash"] = msg_storage
        return render(request, 'job/dend_250.html', context)
    else:
        messages.add_message(request, messages.ERROR, unauthorized_access_message)
        return redirect('app:dashboard')
