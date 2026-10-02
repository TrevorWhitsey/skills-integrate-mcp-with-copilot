# Mergington High School Activities API

A FastAPI application for viewing extracurricular activities and managing student enrollment.

## Features

- View activities and current participants
- Sign in with a provisioned school account
- Restrict enrollment changes to teachers and coordinators
- Maintain student profiles and roles in trusted server configuration

## Getting Started

Install dependencies from the repository root:

```sh
pip install -r requirements.txt
```

From this directory, generate a password hash for each account. The password is prompted and is not included in shell history:

```sh
python -c 'import getpass; from app import hash_password; print(hash_password(getpass.getpass("Password: ")))'
```

Configure accounts with the generated hashes. Roles are assigned only in this trusted server-side configuration; users cannot grant themselves roles.

```sh
export SCHOOL_EMAIL_DOMAIN="mergington.edu"
export SESSION_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AUTH_USERS_JSON='{"teacher@mergington.edu":{"name":"School Teacher","role":"teacher","password_hash":"REPLACE_WITH_HASH"},"student@mergington.edu":{"name":"Student Name","grade":"11","role":"student","password_hash":"REPLACE_WITH_HASH"}}'
```

Run the app from this directory:

```sh
uvicorn app:app --reload
```

Open http://localhost:8000. API documentation is available at http://localhost:8000/docs.

For production, configure a persistent, private `SESSION_SECRET_KEY` and set `COOKIE_SECURE=true` when serving over HTTPS. Do not commit account configuration, password hashes, or secrets. This setup uses pre-provisioned accounts; it does not integrate with an external school SSO provider or provide self-registration.

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get activities and current participants |
| POST | `/auth/login` | Sign in with a configured school account |
| GET | `/auth/me` | Get the current account profile and the user's enrollments |
| POST | `/auth/logout` | Sign out |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher or coordinator enrolls a configured student |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher or coordinator removes a student |

Activity and enrollment data is currently stored in memory and resets when the server restarts.
