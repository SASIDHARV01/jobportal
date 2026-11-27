from django import forms
from django.contrib.auth.forms import BaseUserCreationForm

from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(strip=False, widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)


class SignupForm(BaseUserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[
        ("applicant", "Applicant"),
        ("employer", "Employer"),
    ])

    class Meta:
        model = User
        fields = ["username", "email", "role", "company", "summary", "skills"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        if role == "employer" and not cleaned.get("company"):
            self.add_error("company", "Company name is required for employer accounts.")
        if role == "applicant":
            if not cleaned.get("summary"):
                self.add_error("summary", "Profile summary is required for applicants.")
            if not cleaned.get("skills"):
                self.add_error("skills", "Skills are required for applicants.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role == "employer":
            user.summary = ""
            user.skills = ""
        else:
            user.company = ""
        if commit:
            user.save()
        return user
