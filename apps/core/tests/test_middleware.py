"""Tests for the request-id and current-user thread-local middleware."""
from django.test import RequestFactory, TestCase

from apps.core.middleware.audit_user import (
    CurrentUserMiddleware,
    get_current_request_meta,
    get_current_user,
)
from apps.core.middleware.request_id import RequestIDMiddleware
from apps.users.models import User


class RequestIDMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_generates_a_request_id_when_absent(self):
        middleware = RequestIDMiddleware(get_response=lambda request: {})
        request = self.factory.get("/")
        middleware(request)
        self.assertTrue(request.request_id)

    def test_propagates_an_incoming_request_id(self):
        captured = {}

        def get_response(request):
            captured["request_id"] = request.request_id
            response = {}
            return response

        middleware = RequestIDMiddleware(get_response=get_response)
        request = self.factory.get("/", HTTP_X_REQUEST_ID="abc-123")
        middleware(request)
        self.assertEqual(captured["request_id"], "abc-123")

    def test_response_header_matches_request_id(self):
        def get_response(request):
            return {}

        middleware = RequestIDMiddleware(get_response=get_response)
        request = self.factory.get("/", HTTP_X_REQUEST_ID="fixed-id")
        response = middleware(request)
        self.assertEqual(response["X-Request-ID"], "fixed-id")


class CurrentUserMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user("mw-user", "mw@x.io", "pw-strong-123")

    def test_thread_local_set_during_request_and_cleared_after(self):
        seen = {}

        def get_response(request):
            seen["user"] = get_current_user()
            seen["meta"] = get_current_request_meta()
            return {}

        middleware = CurrentUserMiddleware(get_response=get_response)
        request = self.factory.get("/", REMOTE_ADDR="1.2.3.4")
        request.user = self.user
        request.request_id = "req-1"

        middleware(request)

        self.assertEqual(seen["user"], self.user)
        self.assertEqual(seen["meta"]["ip_address"], "1.2.3.4")
        self.assertEqual(seen["meta"]["request_id"], "req-1")

        # State must not leak to code running outside the request lifecycle.
        self.assertIsNone(get_current_user())

    def test_x_forwarded_for_takes_precedence(self):
        def get_response(request):
            return {}

        middleware = CurrentUserMiddleware(get_response=get_response)
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="9.9.9.9, 10.0.0.1"
        )
        request.user = self.user
        ip = middleware._client_ip(request)
        self.assertEqual(ip, "9.9.9.9")
