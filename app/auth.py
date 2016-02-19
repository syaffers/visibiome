from django.shortcuts import render, redirect
from django.contrib import auth


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
        return render(request, "auth/dashboard.html")


def login(request):
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
                return render(request, "auth/login.html",
                              {"warning": "Your account is not activated!"})
        else:
            return render(request, "auth/login.html",
                          {"warning": "Invalid email and/or password"})


def logout(request):
    auth.logout(request)
    return redirect('/')
