import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import send_mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Application, Job

User = get_user_model()


class JobWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employer = User.objects.create_user(
            username="employer", email="employer@example.test", role="employer", company="Studio",
        )
        cls.applicant = User.objects.create_user(
            username="applicant", email="applicant@example.test", role="applicant",
        )
        cls.job = Job.objects.create(
            employer=cls.employer, title="Backend Intern", description="Work on Django.",
            deadline=timezone.now().date() + timedelta(days=5),
        )

    def setUp(self):
        media = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media))
        self.apply_url = reverse("jobs:apply", args=[self.job.pk])

    def application_data(self):
        return {
            "resume": SimpleUploadedFile("resume.pdf", b"%PDF-1.7\n", content_type="application/pdf"),
            "cover_letter": "I would like to work on Django.",
        }

    def test_guest_can_sign_up_sign_in_and_return_to_selected_application(self):
        login_url = reverse("login", query={"next": self.apply_url})
        signup_url = reverse("signup", query={"next": self.apply_url})
        self.assertRedirects(self.client.get(self.apply_url), login_url)
        self.assertContains(self.client.get(login_url), f'href="{signup_url}"')
        password = "Starlight-Passage-725!"
        signup = self.client.post(signup_url, {
            "next": self.apply_url,
            "username": "new_applicant",
            "email": "new@example.test",
            "password1": password,
            "password2": password,
            "role": "applicant",
            "summary": "Backend developer",
            "skills": "Python",
        })
        self.assertRedirects(signup, login_url)
        login = self.client.post(login_url, {
            "next": self.apply_url,
            "username": "new_applicant",
            "password": password,
            "role": "applicant",
        })
        self.assertRedirects(login, self.apply_url)

    def test_submit_review_and_status_notification(self):
        self.client.force_login(self.applicant)
        response = self.client.post(self.apply_url, self.application_data())
        self.assertRedirects(response, reverse("jobs:my_applications"))
        application = Application.objects.get()
        self.assertEqual(len(mail.outbox), 2)
        self.assertRedirects(
            self.client.post(self.apply_url, self.application_data()), self.job.get_absolute_url()
        )
        self.assertEqual(Application.objects.count(), 1)

        self.client.force_login(self.employer)
        review_url = reverse("jobs:job_applicants", args=[self.job.pk])
        self.assertContains(self.client.get(review_url), application.cover_letter)
        self.assertContains(self.client.get(reverse("employer_dashboard")), "1 application")
        status_url = reverse("jobs:update_application_status", args=[application.pk])
        for _ in range(2):
            response = self.client.post(status_url, {"status": "shortlisted"})
            self.assertRedirects(response, review_url)
        self.assertEqual(len(mail.outbox), 3)
        self.client.force_login(self.applicant)
        self.assertContains(self.client.get(reverse("jobs:my_applications")), "Shortlisted")

    def test_failed_employer_email_does_not_block_applicant_confirmation(self):
        self.client.force_login(self.applicant)
        def send_except_to_employer(**kwargs):
            if kwargs["recipient_list"] == [self.employer.email]:
                raise OSError("SMTP unavailable")
            return send_mail(**kwargs)

        with patch("jobs.emails.send_mail", side_effect=send_except_to_employer):
            with self.assertLogs("jobs.emails", "ERROR"):
                response = self.client.post(self.apply_url, self.application_data())

        self.assertRedirects(response, reverse("jobs:my_applications"))
        self.assertTrue(Application.objects.exists())
        self.assertEqual([message.to for message in mail.outbox], [[self.applicant.email]])

    def test_applicant_can_view_closed_job_from_history(self):
        Application.objects.create(job=self.job, applicant=self.applicant)
        Job.objects.filter(pk=self.job.pk).update(is_open=False)
        self.assertEqual(self.client.get(self.job.get_absolute_url()).status_code, 403)

        self.client.force_login(self.applicant)
        self.assertContains(self.client.get(self.job.get_absolute_url()), "Closed")
        self.assertEqual(self.client.get(self.apply_url).status_code, 403)

    def test_resume_download_requires_access_and_handles_missing_file(self):
        application = Application.objects.create(
            job=self.job, applicant=self.applicant, resume=self.application_data()["resume"],
        )
        download_url = reverse("jobs:download_resume", args=[application.pk])
        unrelated = User.objects.create_user("other", role="employer")
        self.client.force_login(unrelated)
        self.assertEqual(self.client.get(download_url).status_code, 403)

        self.client.force_login(self.employer)
        response = self.client.get(download_url)
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.7\n")
        application.resume.storage.delete(application.resume.name)
        self.assertEqual(self.client.get(download_url).status_code, 404)

    def test_admin_can_review_application_and_notify_on_status_change(self):
        application = Application.objects.create(
            job=self.job, applicant=self.applicant, resume=self.application_data()["resume"],
        )
        administrator = User.objects.create_superuser("administrator", "admin@example.test")
        self.client.force_login(administrator)
        change_url = reverse("admin:jobs_application_change", args=[application.pk])
        download_url = reverse("jobs:download_resume", args=[application.pk])
        self.assertContains(self.client.get(change_url), f'href="{download_url}"')

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(change_url, {"status": "hired", "_save": "Save"})
        self.assertRedirects(response, reverse("admin:jobs_application_changelist"))
        application.refresh_from_db()
        self.assertEqual(application.status, "hired")
        self.assertEqual([message.to for message in mail.outbox], [[self.applicant.email]])

    def test_public_pagination_preserves_filters_and_employer_can_reach_page_two(self):
        Job.objects.bulk_create([
            Job(
                employer=self.employer, title=f"Django role {i}", location="New Delhi",
                description="Build tools", deadline=self.job.deadline,
            )
            for i in range(11)
        ])
        job_list = reverse("jobs:list")
        response = self.client.get(job_list, {"q": "Django", "location": "New Delhi"})
        self.assertContains(response, 'href="?q=Django&amp;location=New+Delhi&amp;page=2"')
        self.client.force_login(self.employer)
        employer_jobs = reverse("jobs:employer_jobs")
        response = self.client.get(employer_jobs)
        self.assertContains(response, 'href="?page=2"')
        self.assertContains(self.client.get(f"{employer_jobs}?page=2"), "Backend Intern")
