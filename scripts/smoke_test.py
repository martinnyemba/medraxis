#!/usr/bin/env python3
"""Smoke-test a running Medraxis instance: docs page, JWT auth, key endpoints.

Stdlib-only so it can run against a built Docker image without installing
any project dependencies. Usage::

    SMOKE_TEST_BASE_URL=http://localhost:8000 \\
    SMOKE_TEST_PASSWORD=... \\
    python scripts/smoke_test.py

Exits 0 if every check passes, 1 otherwise.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("SMOKE_TEST_BASE_URL", "http://localhost:8000").rstrip("/")
USERNAME = os.environ.get("SMOKE_TEST_USERNAME", "admin")
PASSWORD = os.environ.get("SMOKE_TEST_PASSWORD")
ORG = os.environ.get("SMOKE_TEST_ORG", "demo-clinic")
TIMEOUT = 10

AUTHENTICATED_ENDPOINTS = [
    "/api/v1/users/me/",
    "/api/v1/concepts/?page_size=1",
    "/api/v1/providers/?page_size=1",
    "/api/v1/lab/tests/?page_size=1",
    "/api/v1/inventory/products/?page_size=1",
]


def request(method, path, headers=None, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main():
    if not PASSWORD:
        print("FAIL: SMOKE_TEST_PASSWORD is required")
        return 1

    results = []

    status, _ = request("GET", "/api/docs/")
    results.append(("GET /api/docs/", status == 200, status))

    status, body = request(
        "POST", "/api/v1/auth/token/", data={"username": USERNAME, "password": PASSWORD}
    )
    ok = status == 200
    results.append(("POST /api/v1/auth/token/", ok, status))
    if not ok:
        _report(results)
        return 1
    access = json.loads(body)["access"]
    auth_headers = {"Authorization": f"Bearer {access}", "X-Organization": ORG}

    for path in AUTHENTICATED_ENDPOINTS:
        status, _ = request("GET", path, headers=auth_headers)
        results.append((f"GET {path}", status == 200, status))

    return _report(results)


def _report(results):
    failed = 0
    for name, ok, status in results:
        print(f"{'PASS' if ok else 'FAIL'}: {name} ({status})")
        if not ok:
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
