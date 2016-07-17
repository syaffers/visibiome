from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from .models import Guest, UserForm


def register(request):
    """
    User registration handler. This is called when users access the /register/
    route. It takes user details passed in the form and adds a new non-guest
    user if successful.

    :param request: Request object
    :return: Redirects new registered users to /dashboard/ or renders the
    registration page
    """
    msg_storage = messages.get_messages(request)
    form = UserForm(request.POST or None)

    if form.is_valid():
        # create user object and get it
        u = form.save(commit=False)
        u.set_password(form.cleaned_data.get("password"))
        u.save()

        # set the user to not be a guest
        g = Guest(status=False, user_id=u.id)
        g.save()

        user = auth.authenticate(
            username=u.username,
            password=form.cleaned_data.get("password")
        )

        auth.login(request, user)

        return redirect("app:dashboard")

    else:
        if request.method == "POST":
            messages.add_message(
                request, messages.ERROR, "Failed to create user."
            )

    context = {
        "form": form,
        "flash": msg_storage,
    }
    return render(request, "auth/register.html", context)


def login(request):
    """
    Login handler. Called when user logs in from /login/ route. Checks if
    user exists using the auth.authenticate function and checks if user is
    activated on the site. Then redirects user to the location they were
    initially trying to access. This route interrupts all unauthorized access
    to handlers with the @login_required decorator

    :param request: Request object
    :return: Redirects user to original path or renders the login page
    """
    msg_storage = messages.get_messages(request)
    if request.user.is_authenticated():
        return redirect("app:dashboard")
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
                    request, messages.ERROR, "Your account is not activated!"
                )
                return render(
                    request, "auth/login.html", {"flash": msg_storage}
                )
        else:
            messages.add_message(
                request, messages.ERROR, "Invalid email and/or password")
            return render(
                request, "auth/login.html", {"flash": msg_storage})


def logout(request):
    """
    Logout handler

    :param request: Request object
    :return: Redirects user to home while ending session
    """
    auth.logout(request)
    return redirect('app:index')


@login_required
def update_details(request):
    """
    Update user details handler. Called when users access the /update/ route.
    Loads user's current data and takes new information to be updated.
    Successful updates are redirected to /dashboard/. Guest users who update
    their profile automatically gain full user-ship status.

    :param request: Request object
    :return: Redirects user to /dashboard/ or renders the update page
    """
    msg_storage = messages.get_messages(request)
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data.get('password'))
        user.save()

        # change guest users to full users
        guest = user.guest
        if guest.status:
            guest.status = False
            guest.save()

        messages.add_message(
                request, messages.SUCCESS, "Information saved.")

        # update the authentication session so that user doesn't have to
        # log back in
        auth.update_session_auth_hash(request, user)
        redirect('app:dashboard')

    else:
        if request.method == "POST":
            messages.add_message(
                request, messages.ERROR, "Failed to save information.")

    request.user.refresh_from_db()
    context = {
        "form": form,
        "flash": msg_storage,
    }
    return render(request, 'auth/update.html', context)
