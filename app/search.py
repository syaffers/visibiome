from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages, auth
from .models import BiomSearchForm, Guest, BiomSearchJob
from .tasks import simulate_task, validate_input

def guest_search(request):
    """
    Handler when user performs a search from the homepage without signing in

    :param request:
    :return:
    """
    msg_storage = messages.get_messages(request)
    if request.method == "POST":
        # get data from the search form submission
        bsf = BiomSearchForm(request.POST, request.FILES)
        # check if form submission is correct
        if bsf.is_valid():
            # create a guest user with a user number
            u = User.objects.create_user(
                "guest", "email@example.com", "guest123"
            )
            u.username += str(u.pk)
            u.save()

            guest = Guest(status=True, user_id=u.id)
            guest.save()

            # log 'em in
            user = auth.authenticate(username=u.username, password="guest123")
            auth.login(request, user)

            # Make a job object from the form and add the newly created guest
            # user as the user initiating this job
            job = bsf.save(commit=False)
            job.user = user
            job.save()
            bsf.save_m2m()

            if job.biom_file.name == "" or job.biom_file.name is None:
                validate_input.delay(job.id, job.otu_text, 1)
            else:
                validate_input.delay(job.id, job.biom_file, 0)

            messages.add_message(
                request, messages.SUCCESS, "Successfully created task."
            )
            return redirect('app:dashboard')
        else:
            messages.add_message(
                request, messages.ERROR, "Search form has some errors."
            )

            context = {
                "form": bsf,
                "flash": msg_storage,
            }
            return render(request, "app/index.html", context)


@login_required
def user_search(request):
    """
    Handler when user performs a search from the homepage while signed in

    :param request:
    :return:
    """
    msg_storage = messages.get_messages(request)
    if request.method == "POST":
        bsf = BiomSearchForm(request.POST, request.FILES)
        if bsf.is_valid():
            job = bsf.save(commit=False)
            job.user = request.user
            job.save()
            bsf.save_m2m()

            if job.biom_file.name == "" or job.biom_file.name is None:
                validate_input.delay(job.id, job.otu_text, 1)
            else:
                validate_input.delay(job.id, job.biom_file, 0)

            messages.add_message(
                request, messages.SUCCESS, "Successfully created task."
            )
            return redirect('app:dashboard')
        else:
            messages.add_message(
                request, messages.ERROR, "Search form has some errors."
            )

            context = {
                "form": bsf,
                "flash": msg_storage,
            }
            return render(request, "app/index.html", context)
