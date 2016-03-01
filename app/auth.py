from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib import messages


def register(request):
    if request.method == "GET":
        return render(request, 'auth/register.html')
    elif request.method == "POST":
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']

        auth.models.User.objects.create_user(username, email, password)
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
