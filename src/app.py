"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

PASSWORD_HASH_ITERATIONS = 600_000
ALLOWED_ROLES = {"student", "teacher", "coordinator", "activity_leader"}
STAFF_ROLES = {"teacher", "coordinator"}


class LoginCredentials(BaseModel):
    email: str
    password: str


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"),
        PASSWORD_HASH_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256" or int(iterations) < PASSWORD_HASH_ITERATIONS:
            return False
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("ascii"), int(iterations)
        ).hex()
        return hmac.compare_digest(actual_digest, expected_digest)
    except (AttributeError, ValueError):
        return False


def load_auth_users() -> dict[str, dict[str, str | None]]:
    configured_users = os.getenv("AUTH_USERS_JSON", "{}")
    school_domain = os.getenv("SCHOOL_EMAIL_DOMAIN", "mergington.edu").strip().lower()
    try:
        raw_users = json.loads(configured_users)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=503, detail="Authentication configuration is invalid") from error

    if not isinstance(raw_users, dict):
        raise HTTPException(status_code=503, detail="Authentication configuration is invalid")

    users = {}
    for configured_email, account in raw_users.items():
        email = configured_email.strip().lower()
        email_parts = email.rsplit("@", 1)
        if (len(email_parts) != 2 or not email_parts[0]
                or email_parts[1] != school_domain or not isinstance(account, dict)):
            raise HTTPException(status_code=503, detail="Authentication account configuration is invalid")

        role = account.get("role")
        password_hash = account.get("password_hash")
        if not isinstance(role, str) or role not in ALLOWED_ROLES or not isinstance(password_hash, str):
            raise HTTPException(status_code=503, detail="Authentication account configuration is invalid")

        users[email] = {
            "email": email,
            "name": account.get("name") if isinstance(account.get("name"), str) else "",
            "grade": account.get("grade") if isinstance(account.get("grade"), str) else None,
            "role": role,
            "password_hash": password_hash,
        }
    return users


def public_profile(user: dict[str, str | None]) -> dict[str, str | None | list[str]]:
    profile = {key: user[key] for key in ("email", "name", "grade", "role")}
    email = user["email"]
    profile["enrollments"] = [
        activity_name
        for activity_name, activity in activities.items()
        if email and email in activity["participants"]
    ]
    return profile


def get_current_user(request: Request) -> dict[str, str | None]:
    email = request.session.get("email")
    user = load_auth_users().get(email) if isinstance(email, str) else None
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_staff(request: Request) -> dict[str, str | None]:
    user = get_current_user(request)
    if user["role"] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Teacher or coordinator access required")
    return user

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY") or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    max_age=8 * 60 * 60,
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: LoginCredentials, request: Request):
    users = load_auth_users()
    user = users.get(credentials.email.strip().lower())
    if user is None or not verify_password(credentials.password, user["password_hash"] or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    request.session.clear()
    request.session["email"] = user["email"]
    return {"user": public_profile(user)}


@app.get("/auth/me")
def get_profile(request: Request):
    return {"user": public_profile(get_current_user(request))}


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Signed out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, request: Request, email: str):
    """Sign up a student for an activity"""
    require_staff(request)

    student = load_auth_users().get(email.strip().lower())
    if student is None or student["role"] != "student":
        raise HTTPException(status_code=400, detail="Student account not found")
    email = student["email"] or ""

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: Request, email: str):
    """Unregister a student from an activity"""
    require_staff(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
