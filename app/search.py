from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages, auth
from .models import BiomSearchForm, Guest, BiomSearchJob


def guest_search(request):
    """
    Handler when user performs a search from the homepage without signing in

    :param request:
    :return:
    """
    msg_storage = messages.get_messages(request)
    if request.method == "POST":
        # get data
        # from the search form submission
        bsf = BiomSearchForm(request.POST)
        print(request.POST)
        # check if form submission is correct
        # TODO: validate the number of ecosystems and work on m2m
        if bsf.is_valid():
            # # create a guest user with a user number
            # u = User.objects.create_user(
            #     "guest", "email@example.com", "guest123"
            # )
            # u.username += str(u.pk)
            # u.save()
            #
            # guest = Guest(status=True, user_id=u.id)
            # guest.save()
            #
            # # log 'em in
            # user = auth.authenticate(username=u.username, password="guest123")
            # auth.login(request, user)

            job = bsf.save()
            print(job)
            # messages.add_message(
            #     request, messages.SUCCESS, "Successfully created task."
            # )
            # return redirect('/dashboard')
        else:
            print(bsf.errors)
            messages.add_message(
                request, messages.ERROR, "Form has some errors"
            )

            context = {
                "form": bsf,
                "flash": msg_storage,
            }
            return render(request, "app/index.html", context)


@login_required
def user_search(request):
    msg_storage = messages.get_messages(request)
    if request.method == "POST":
        form = BiomSearchForm(request.POST, request.FILES)
        # print("Okay")
        # print(request.POST.get("otu_text"))
        # print(request.FILES["otu_file"])
        # print(request.POST.getlist("criteria"))
        if form.is_valid():
            return HttpResponse(request.POST, content_type="text/html")
        else:
            print(form.errors)
            messages.add_message(
                request, messages.ERROR, "Validation errors."
            )

            return redirect('/')

    # TODO: Handle normal users login
    pass
