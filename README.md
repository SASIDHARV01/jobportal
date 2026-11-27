# Job Portal

A Django recruitment portal built for a Flipkart internship task. Employers publish listings and review applications. Applicants find jobs, submit PDF resumes, and track their progress. Administrators manage users, jobs, and applications in Django Admin.

## Hiring workflow

1. An employer creates a listing with a deadline, skills, and an optional salary range.
2. Applicants filter open listings by keyword, location, job type, or skills.
3. An applicant selects **Apply Now**, signs in or registers, and returns to the application form.
4. The applicant uploads one PDF resume up to 5 MB and can add a cover letter.
5. The employer reviews submissions, downloads resumes, and updates application statuses.
6. The applicant sees the updated status in **My Applications**. Email delivery depends on SMTP configuration.

The employer dashboard shows counts for listings and applications. Resume downloads require permission. Public registration is available for applicants and employers.

## Run locally

Use Python 3.11 or newer. Local development defaults to SQLite when `DATABASE_URL` is unset. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [Job Portal](http://127.0.0.1:8000/) or [Django Admin](http://127.0.0.1:8000/admin/). Run tests with `python manage.py test`. By default, local email messages appear in the terminal. An optional `.env` can override settings for local use.

## Supabase PostgreSQL

Use a dedicated Supabase project for Job Portal. Since Django connects directly to PostgreSQL, disable the project's Data API before importing user data. In Supabase, open **Connect** and copy the **Session pooler** URL (port `5432`). It supports IPv4 and suits the Gunicorn deployment. Replace the password placeholder with the URL-encoded database password. Save the connection URL as `DATABASE_URL` in your ignored local `.env` or in the host's secret environment settings. The Django connection requires TLS by default. You can supply `sslmode=verify-full` and `sslrootcert` in the URL if the host has the Supabase CA certificate.

For a fresh database, run `python manage.py migrate` followed by `python manage.py createsuperuser`.

### Move the existing SQLite records

Use a fresh Supabase database for the import. Pause writes to the source during the final copy, and keep an independent backup of SQLite and any uploaded files. Run the following from the environment that has the **source** SQLite file. Keep the generated fixture private because it contains account records and password hashes.

```sh
umask 077
migration_dir=$(mktemp -d)
DATABASE_URL= python manage.py dumpdata --all --natural-foreign \
    --exclude contenttypes --exclude auth.permission --exclude sessions \
    --output "$migration_dir/jobportal.json"
python manage.py migrate
python manage.py loaddata "$migration_dir/jobportal.json"
```

The empty `DATABASE_URL=` on the export command selects SQLite for that command alone. The remaining commands use the Supabase URL from your environment. Migrations recreate Django's content types and built-in permissions. Users sign in again after cutover.

Before switching the hosted app, compare record counts and check an existing sign-in, job posting, application history, and resume download. Resume file paths move with their application rows. PDF files must be copied to private persistent file storage separately.

## Hosting configuration

Set `DEBUG=0`, a unique `SECRET_KEY`, and `ALLOWED_HOSTS` with the deployed hostnames. Set `CSRF_TRUSTED_ORIGINS` with the full HTTPS origins if needed. Set `TRUST_PROXY_HTTPS=1` only when the hosting proxy sets and controls the forwarded HTTPS header. Configure `SECURE_HSTS_SECONDS` after HTTPS is working. Set the email backend and SMTP credentials through the host's environment settings.

Run `python manage.py check --deploy`, `python manage.py migrate`, and `python manage.py collectstatic --noinput` as part of deployment. The start command is `gunicorn jobportal.wsgi:application`. Set `DATABASE_URL` for Supabase PostgreSQL. Uploaded resumes still require private persistent file storage for `media/`. Serve downloads through the application's authorized download route.

## Project structure

| Directory | Responsibility |
|---|---|
| `accounts/` | User model, registration, authentication, and roles |
| `jobs/` | Job listings, applications, resume access, and application notifications |
| `core/` | Role dashboards and home routing |
| `templates/` and `static/` | Django templates and CSS |

## Screenshots from the original internship submission

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/6b79c276-d317-49c7-af69-cf26cc2d62a0" />

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/a69d61f3-f298-4cdb-bf16-6d7607ef68ae" />

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/3aac15a5-f5f4-4d8c-83a4-09d344901ed0" />

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/d46445ff-4867-447d-b600-e703e7a59a0d" />

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/6afc2197-d149-4894-a11c-67eefdf01233" />

Developed by Venkata Sasidhar Guturi.
