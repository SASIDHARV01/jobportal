from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html

from .emails import send_application_status_changed_email
from .models import Application, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "job_type", "is_open", "deadline", "created_at")
    list_filter = ("job_type", "is_open", "deadline", "created_at")
    search_fields = ("title", "description", "location", "skills", "employer__username")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "job", "status", "applied_at")
    list_filter = ("status",)
    list_select_related = ("applicant", "job")
    search_fields = ("applicant__username", "job__title")
    fields = ("job", "applicant", "status", "cover_letter", "resume_download", "applied_at")
    readonly_fields = ("job", "applicant", "cover_letter", "resume_download", "applied_at")

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if "status" in form.changed_data:
            transaction.on_commit(lambda: send_application_status_changed_email(obj))

    @admin.display(description="Resume")
    def resume_download(self, application):
        if not application.resume:
            return "No resume"
        url = reverse("jobs:download_resume", args=[application.pk])
        return format_html('<a href="{}">Download resume</a>', url)
