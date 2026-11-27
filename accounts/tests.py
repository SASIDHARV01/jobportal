from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import SignupForm

User = get_user_model()
PASSWORD = "Starlight-Passage-725!"


class AuthenticationTests(TestCase):
    def test_invalid_employer_signup_keeps_role_and_displays_field_error(self):
        response = self.client.post(reverse("signup"), {
            "username": "employer",
            "email": "employer@example.test",
            "role": "employer",
            "password1": PASSWORD,
            "password2": PASSWORD,
        })
        self.assertContains(response, "Company name is required for employer accounts.")
        self.assertContains(response, '<option value="employer" selected>Employer</option>', html=True)
        self.assertFalse(User.objects.exists())

    def test_disabled_account_cannot_sign_in_through_portal_or_admin(self):
        user = User.objects.create_superuser(
            "disabled", "disabled@example.test", PASSWORD, is_disabled=True,
        )
        portal = self.client.post(reverse("login"), {
            "username": user.username, "password": PASSWORD, "role": "admin",
        })
        admin = self.client.post(reverse("admin:login"), {
            "username": user.username, "password": PASSWORD,
        })
        self.assertEqual(portal.status_code, 200)
        self.assertEqual(admin.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        user = User.objects.create_user("applicant")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_public_signup_has_only_applicant_and_employer_roles(self):
        self.assertEqual(dict(SignupForm().fields["role"].choices), {
            "applicant": "Applicant", "employer": "Employer",
        })
