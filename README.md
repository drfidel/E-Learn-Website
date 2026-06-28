# E-Learning Platform (Django + DRF)

A full-stack e-learning platform with role-based learning workflows for **Admins**, **Instructors**, and **Students**.

## Features

- Custom user model with role support (admin/instructor/student)
- Email/password authentication + profile management
- Course catalog with search and free/paid filters
- Course structure: **Course → Module → Lesson**
- Lesson content types: video, text, file
- Quizzes and questions
- Enrollment and progress tracking
- Reviews and ratings
- REST API (DRF) + JWT auth
- Payment flow scaffold (Stripe/Flutterwave-ready)
- Instructor and student dashboards
- Django admin management
- Dockerized deployment with Gunicorn + Nginx + PostgreSQL

## Project Structure

- `accounts/` – users, roles, registration, profile
- `courses/` – categories, courses, enrollment, progress, dashboards
- `lessons/` – modules, lessons, quizzes
- `payments/` – payment records and verification scaffold
- `reviews/` – ratings and comments
- `api/` – DRF serializers and endpoints
- `templates/` – Bootstrap 5 templates
- `static/` – static assets
- `fixtures/` – sample seed data

## Local Setup (SQLite quick-start)

```bash
python -m venv .venv
source .venv/bin/activate or source .venv/Scripts/activate or .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/sample_data.json
python manage.py runserver
```

## PostgreSQL + Docker

```bash
docker compose up --build
```

Then open `http://localhost`.

## API Endpoints

- `POST /api/auth/register/` – register a user
- `GET|PUT /api/auth/me/` – view or update the authenticated profile
- `POST /api/token/` – obtain JWT token
- `POST /api/token/refresh/` – refresh JWT token
- `GET|POST /api/categories/`
- `GET|POST /api/courses/`
- `GET|PUT|DELETE /api/courses/<id>/`
- `POST /api/courses/<id>/enroll/`
- `GET|POST /api/modules/`
- `GET|PUT|DELETE /api/modules/<id>/`
- `GET|POST /api/lessons/`
- `GET|PUT|DELETE /api/lessons/<id>/`
- `POST /api/lessons/<id>/progress/` – mark a lesson complete/incomplete
- `GET|POST /api/quizzes/`
- `GET|PUT|DELETE /api/quizzes/<id>/`
- `GET|POST /api/questions/`
- `GET|PUT|DELETE /api/questions/<id>/`
- `GET /api/enrollments/`
- `GET|POST /api/progress/`
- `GET /api/certificates/`
- `POST /api/certificates/issue/<enrollment_id>/`
- `GET /api/certificates/verify/<certificate_id>/`
- `GET|POST /api/payments/`
- `GET|POST /api/reviews/`

## Payment Notes

Current payment verification uses a placeholder service in `payments/services.py`. Replace with real:

- Stripe Checkout + webhook verification
- Flutterwave transaction verification endpoint

On successful verification, users are auto-enrolled.

## Low Bandwidth & UX Notes

- Server-rendered templates for reduced JS payload
- Mobile-first Bootstrap layout
- Designed for progressive enhancement

## Testing

```bash
python manage.py test
```

## psycopg2 Install Error Fix

If you see:

`If you prefer to avoid building psycopg2 from source, please install the PyPI 'psycopg2-binary' package instead.`

Run:

```bash
pip uninstall -y psycopg2 psycopg2-binary
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

## Optional Enhancements

- Social login (`django-allauth`)
- Email backend (SendGrid/Mailgun)
- S3 media storage via `django-storages`
- Zoom live classes integration
- Recommendation engine and forums
