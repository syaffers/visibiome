from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages, auth
from .models import Guest


def guest_search(request):
    if request.method == "POST":
        # create a guest user
        u = User.objects.create_user("guest", "email@example.com", "guest123")
        u.username += u.pk
        u.save()

        guest = Guest(status=True, user_id=u.id)
        u.username = "guest" + str(u.id)
        guest.save()
        u.save()

        # log 'em in
        user = auth.authenticate(username=u.username, password="guest")
        auth.login(request, user)

        # TODO: Start running task

        messages.add_message(
            request, messages.SUCCESS, "Successfully created task.")
        return redirect('/dashboard')


@login_required
def user_search(request):
    # TODO: Handle normal users login
    pass
