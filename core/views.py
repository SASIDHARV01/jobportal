from django.shortcuts import render, redirect
from accounts.decorators import role_required
from jobs.models import Application


def home(request):
    user = request.user

    if not user.is_authenticated:
        return redirect("jobs:list")
    
    if user.is_superuser or getattr(user, "role", None) == "admin":
        return redirect("/admin/")

    if getattr(user, "role", None) == "employer":
        return redirect("employer_dashboard")

    return redirect("applicant_dashboard")

@role_required("employer")
def employer_dashboard(request):
    return render(request, "core/employer_dashboard.html", {
        "job_count": request.user.jobs.count(),
        "application_count": Application.objects.filter(job__employer=request.user).count(),
    })

@role_required("applicant")
def applicant_dashboard(request):
    return render(request, "core/applicant_dashboard.html")