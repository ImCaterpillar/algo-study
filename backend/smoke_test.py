"""Backend smoke test for local development.

Usage:
    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
    pip install -r requirements-dev.txt
    python smoke_test.py
"""

from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def _assert_ok(name: str, response, expected_status: int = 200) -> dict[str, Any] | list[Any]:
    if response.status_code != expected_status:
        raise AssertionError(f"{name} failed: {response.status_code} {response.text[:500]}")
    if response.text:
        return response.json()
    return {}


def main() -> None:
    username = f"smoke_{time.time_ns()}"
    password = "pass12345"
    email = f"{username}@example.com"

    with TestClient(app) as client:
        _assert_ok(
            "register",
            client.post(
                "/api/auth/register",
                json={"username": username, "email": email, "password": password},
            ),
        )
        token_payload = _assert_ok(
            "login",
            client.post("/api/auth/login", data={"username": username, "password": password}),
        )
        headers = {"Authorization": f"Bearer {token_payload['access_token']}"}

        checks = [
            ("health", client.get("/health")),
            ("me", client.get("/api/auth/me", headers=headers)),
            ("problems", client.get("/api/problems", headers=headers)),
            ("problem-detail", client.get("/api/problems/1", headers=headers)),
            ("summary", client.get("/api/stats/summary", headers=headers)),
            ("reviews", client.get("/api/reviews/due", headers=headers)),
            ("templates", client.get("/api/templates", headers=headers)),
            ("template-detail", client.get("/api/templates/1", headers=headers)),
            (
                "execute-js",
                client.post(
                    "/api/execute",
                    headers=headers,
                    json={"language": "javascript", "code": "console.log(1 + 1)"},
                ),
            ),
            (
                "sandbox-python",
                client.post(
                    "/api/sandbox/execute",
                    headers=headers,
                    json={"language": "python", "code": "print(1 + 1)"},
                ),
            ),
        ]
        for name, response in checks:
            payload = _assert_ok(name, response)
            if name in {"problems", "reviews", "templates"}:
                assert isinstance(payload, dict) and "items" in payload and "total" in payload, payload
            print(f"OK {name}")

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
