import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, SignupForm

logger = logging.getLogger(__name__)


def auth_destination(request):
    destination = request.POST.get("next") or request.GET.get("next", "")
    if destination.startswith("/") and url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destination
    return ""


def login_view(request):
    destination = auth_destination(request)
    form = LoginForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        role = form.cleaned_data["role"]
        user = authenticate(request, username=username, password=password)

        if user is None:
            form.add_error(None, "Invalid username or password.")
        elif user.is_staff and (user.is_superuser or user.role == "admin"):
            login(request, user)
            return redirect("admin:index")
        elif user.role != role:
            form.add_error("role", "Incorrect role selected for this account.")
        else:
            login(request, user)
            dashboard = "employer_dashboard" if role == "employer" else "applicant_dashboard"
            return redirect(destination or reverse(dashboard))

    return render(request, "accounts/auth.html", {
        "form": form,
        "mode": "login",
        "next": destination,
    })


def signup_view(request):
    destination = auth_destination(request)
    form = SignupForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        try:
            send_mail(
                subject="Welcome to Job Portal",
                message=(
                    f"Hi {user.username},\n\n"
                    f"Your {user.get_role_display()} account is ready. "
                    "Sign in to get started.\n\nJob Portal Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except (OSError, ValueError):
            logger.exception("Could not send welcome email for user %s", user.pk)

        messages.success(request, "Account created. Please log in.")
        return redirect(reverse("login", query={"next": destination} if destination else None))

    return render(request, "accounts/auth.html", {
        "form": form,
        "mode": "signup",
        "next": destination,
    })


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")
