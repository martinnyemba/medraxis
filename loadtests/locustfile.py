"""Locust load test against a running Medraxis instance.

Read-only by design (no POST/PATCH/DELETE) so it can be run repeatedly
against a shared environment without polluting data. Usage::

    pip install -r requirements-dev.txt
    LOAD_TEST_PASSWORD=... locust -f loadtests/locustfile.py --host=http://localhost:8000
"""
import os

from locust import HttpUser, between, task

USERNAME = os.environ.get("LOAD_TEST_USERNAME", "admin")
PASSWORD = os.environ.get("LOAD_TEST_PASSWORD")
ORG = os.environ.get("LOAD_TEST_ORG", "demo-clinic")


class MedraxisUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/token/", json={"username": USERNAME, "password": PASSWORD}
        )
        access = response.json()["access"]
        self.client.headers.update(
            {"Authorization": f"Bearer {access}", "X-Organization": ORG}
        )

    @task(3)
    def list_concepts(self):
        self.client.get("/api/v1/concepts/?page_size=20")

    @task(3)
    def list_patients(self):
        self.client.get("/api/v1/patients/?page_size=20")

    @task(2)
    def list_products(self):
        self.client.get("/api/v1/inventory/products/?page_size=20")

    @task(2)
    def list_lab_tests(self):
        self.client.get("/api/v1/lab/tests/?page_size=20")

    @task(1)
    def me(self):
        self.client.get("/api/v1/users/me/")
