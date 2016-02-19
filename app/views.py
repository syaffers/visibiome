from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'app/index.html')


def contact(request):
    return render(request, 'app/contact.html')


def tutorial(request):
    return render(request, 'app/tutorial.html')


@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html')