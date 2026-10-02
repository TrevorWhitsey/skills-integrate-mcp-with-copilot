import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import app


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.student_password_hash = app.hash_password("student-password")
        cls.teacher_password_hash = app.hash_password("teacher-password")
        cls.users = {
            "student@mergington.edu": {
                "name": "Test Student",
                "grade": "11",
                "role": "student",
                "password_hash": cls.student_password_hash,
            },
            "teacher@mergington.edu": {
                "name": "Test Teacher",
                "role": "teacher",
                "password_hash": cls.teacher_password_hash,
            },
        }

    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "AUTH_USERS_JSON": json.dumps(self.users),
            "SCHOOL_EMAIL_DOMAIN": "mergington.edu",
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        if "student@mergington.edu" in app.activities["Chess Club"]["participants"]:
            app.activities["Chess Club"]["participants"].remove("student@mergington.edu")

    @staticmethod
    def make_request(email=None):
        session = {} if email is None else {"email": email}
        return Request({"type": "http", "session": session})

    def test_password_hash_verifies_without_storing_plaintext(self):
        self.assertTrue(app.verify_password("teacher-password", self.teacher_password_hash))
        self.assertFalse(app.verify_password("wrong-password", self.teacher_password_hash))
        self.assertFalse(app.verify_password("teacher-password", "invalid"))

    def test_login_sets_session_and_returns_profile_without_hash(self):
        request = self.make_request()
        result = app.login(
            app.LoginCredentials(email="teacher@mergington.edu", password="teacher-password"),
            request,
        )

        self.assertEqual(request.session["email"], "teacher@mergington.edu")
        self.assertEqual(result["user"]["role"], "teacher")
        self.assertNotIn("password_hash", result["user"])

    def test_student_cannot_change_enrollment(self):
        request = self.make_request("student@mergington.edu")

        with self.assertRaises(HTTPException) as signup_error:
            app.signup_for_activity("Chess Club", request, "student@mergington.edu")
        self.assertEqual(signup_error.exception.status_code, 403)

        with self.assertRaises(HTTPException) as unregister_error:
            app.unregister_from_activity("Chess Club", request, "michael@mergington.edu")
        self.assertEqual(unregister_error.exception.status_code, 403)

    def test_teacher_can_manage_only_configured_students(self):
        request = self.make_request()
        app.login(
            app.LoginCredentials(email="teacher@mergington.edu", password="teacher-password"),
            request,
        )

        app.signup_for_activity("Chess Club", request, "student@mergington.edu")
        self.assertIn("student@mergington.edu", app.activities["Chess Club"]["participants"])
        student_profile = app.get_profile(self.make_request("student@mergington.edu"))["user"]
        self.assertEqual(student_profile["enrollments"], ["Chess Club"])

        with self.assertRaises(HTTPException) as signup_error:
            app.signup_for_activity("Chess Club", request, "unknown@mergington.edu")
        self.assertEqual(signup_error.exception.status_code, 400)

        app.unregister_from_activity("Chess Club", request, "student@mergington.edu")
        self.assertNotIn("student@mergington.edu", app.activities["Chess Club"]["participants"])


if __name__ == "__main__":
    unittest.main()