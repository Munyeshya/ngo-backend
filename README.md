# NGO Backend

Django REST backend for the NGO management platform. It handles authentication, staff verification, projects, beneficiaries, donations, reports, moderation, cashouts, analytics, and the backend API documentation page at `/`.

## Stack

- Python 3.12+
- Django 5
- Django REST Framework
- MySQL
- JWT auth with SimpleJWT
- SMTP email delivery

## Requirements

- Python installed
- MySQL server running
- A database created for the project
- Optional SMTP credentials if you want email features to work locally

## Clone And Folder Structure

Clone the backend and frontend into the same parent folder so local development stays organized:

```powershell
mkdir NGOs
cd NGOs
git clone https://github.com/Munyeshya/ngo-backend.git
git clone https://github.com/Munyeshya/ngo-frontend.git
```

Recommended structure:

```text
NGOs/
  ngo-backend/
  ngo-frontend/
```

Run backend commands inside `ngo-backend` and frontend commands inside `ngo-frontend`.

## Install

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

4. Update `.env` with your local database and email values.

## Environment Variables

The backend reads environment values from `.env` using `python-decouple`.

Use `.env.example` as the reference for:

- `SECRET_KEY`
- `DEBUG`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`
- `FRONTEND_LOGIN_URL`
- `FRONTEND_DONOR_CLAIM_URL`
- `FRONTEND_STAFF_GUIDE_URL`

## Database Setup

Run migrations:

```powershell
python manage.py migrate
```

Create an admin account:

```powershell
python manage.py createsuperuser
```

Optional sanity check:

```powershell
python manage.py check
```

## Demo Data

Reset and reseed the platform:

```powershell
python manage.py reset_demo_data
```

Optional larger dataset:

```powershell
python manage.py reset_demo_data --donors 30 --staff 10 --partners 12 --projects 20
```

Seeded donor and staff password:

```text
DemoPass123!
```

## Run The Server

```powershell
python manage.py runserver
```

Important URLs:

- Backend docs: `http://127.0.0.1:8000/`
- Health check: `http://127.0.0.1:8000/api/health/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Key Features

- JWT login, logout, and refresh
- Donor account claim by email verification
- Staff registration plus verification review flow
- Project ownership for staff and oversight for admin
- Public project reporting and admin moderation
- Donation tracking and anonymous donation handling
- Project cashouts that publish money-usage updates publicly
- Admin analytics by project type

## Notes

- Real `.env` files are intentionally ignored and should stay local.
- `media/` is intentionally local and should not be committed.
- If you update environment variables, restart the Django server.
