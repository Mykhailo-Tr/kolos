from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from activity.models import ActivityLog
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/registration.html", {"form": form, "page": "register"})


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form, "page": "login"})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    context = {
        "page": "profile",
        "user": request.user
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = EditProfileForm(instance=user)

    return render(request, "accounts/edit_profile.html", {"form": form, "page": "edit_profile"})


@login_required
def delete_profile_view(request):
    error = None

    if request.method == "POST":
        password = request.POST.get("password")

        user = authenticate(username=request.user.username, password=password)

        if user is None:
            error = "Невірний пароль."
        else:
            request.user.delete()
            return redirect("login")

    return render(request, "accounts/delete_profile.html", {"error": error})


def home_view(request):
    if not request.user.is_authenticated:
        context = {"page": "home"}
        return render(request, "home.html", context)
    period = request.GET.get("period", "today")
    now = timezone.now()

    if period == "today":
        logs = ActivityLog.objects.filter(user=request.user, created_at__date=now.date())
    elif period == "week":
        logs = ActivityLog.objects.filter(user=request.user, created_at__gte=now - timedelta(days=7))
    elif period == "month":
        logs = ActivityLog.objects.filter(user=request.user, created_at__gte=now - timedelta(days=30))
    else:
        logs = ActivityLog.objects.filter(user=request.user)

    context = {
        "page": "home",
        "logs": logs,
        "filter_period": period,
    }
    return render(request, "home.html", context)