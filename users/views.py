from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Dataset  # Make sure to import your models
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import logout


@login_required
def profile_view(request):
    return render(request, 'users/profile.html')  # Ensure this template exists


def home(request):
    return render(request, 'home.html')  # Ensure this template exists


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard(request):
    datasets = request.user.dataset_set.all()
    return render(request, 'users/dashboard.html', {'datasets': datasets})


@require_POST
def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
    # Redirect to login page after logout
    # Ensure you have a URL pattern for 'login' in your urls.py file        