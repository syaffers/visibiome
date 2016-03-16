from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib import messages
from .models import Guest


def register(request):
    if request.method == "GET":
        return render(request, 'auth/register.html')
    elif request.method == "POST":
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']

        # create user object and get it
        User.objects.create_user(username, email, password)
        u = User.objects.filter(username=username).first()
        # set the user to not be a guest
        g = Guest(status=False, user_id=u.id)
        g.save()

        user = auth.authenticate(username=username, password=password)
        auth.login(request, user)
        return redirect("/dashboard")


def login(request):
    msg_storage = messages.get_messages(request)
    if request.method == "GET":
        return render(request, 'auth/login.html')
    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth.login(request, user)

                next_url = ""
                if "next" in request.GET:
                    next_url = request.GET["next"]
                if next_url is None or next_url == "":
                    next_url = "/"
                return redirect(next_url)
            else:
                messages.add_message(
                    request, messages.ERROR, "Your account is not activated!")
                return render(
                    request, "auth/login.html", {"flash": msg_storage})
        else:
            messages.add_message(
                request, messages.ERROR, "Invalid email and/or password")
            return render(
                request, "auth/login.html", {"flash": msg_storage})


def logout(request):
    auth.logout(request)
    return redirect('/')


@login_required
def update_details(request):
    msg_storage = messages.get_messages(request)
    if request.method == "GET":
        return render(request, 'auth/update.html')
    elif request.method == "POST":
        # TODO: Complete update details page
        new_username = request.POST['username']
        new_password = request.POST['password']
        new_email = request.POST['email']

        user = User.objects.filter(username=request.user.username).first()
        user.username = new_username
        user.set_password(new_password)
        user.email = new_email

        # TODO: We need to update guest status as well if the user is guest!

        # TODO: This can fail, do a try/except with all cases
        user.save()
        if True:
            messages.add_message(
                request, messages.SUCCESS, "Details updated successfully")
            redirect('/dashboard')
        else:
            messages.add_message(
                request, messages.ERROR, "Invalid email and/or password")
            return render(
                request, "auth/update.html", {"flash": msg_storage})
