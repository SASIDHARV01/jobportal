from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_disabled")
    list_filter = ("role", "is_active", "is_disabled")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Job Portal", {"fields": ("role", "company", "summary", "skills", "is_disabled")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Job Portal", {"fields": ("role", "email", "company", "summary", "skills")}),
    )
