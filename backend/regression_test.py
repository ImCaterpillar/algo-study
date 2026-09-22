"""Focused regression checks for bug fixes that smoke_test.py does not cover.

Usage:
    cd backend
    source .venv/bin/activate
    python regression_test.py
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.migrations import migrate_sqlite_database


def assert_api_regressions() -> None:
    with TestClient(app) as client:
        username = f"reg_{time.time_ns()}"
        password = "pass12345"
        email = f"{username}@example.com"

        response = client.post(
            "/api/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert response.status_code == 200, response.text

        duplicate_username = client.post(
            "/api/auth/register",
            json={"username": username.upper(), "email": f"dup_{email}", "password": password},
        )
        assert duplicate_username.status_code == 400, duplicate_username.text

        login_upper = client.post(
            "/api/auth/login",
            data={"username": username.upper(), "password": password},
        )
        assert login_upper.status_code == 200, login_upper.text

        token = client.post(
            "/api/auth/login",
            data={"username": username, "password": password},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get("/api/templates").status_code == 401
        assert client.get("/api/templates", headers=headers).status_code == 200
        assert client.patch(
            "/api/problems/999999/progress",
            headers=headers,
            json={"status": "Accepted"},
        ).status_code == 404

        not_started = client.get(
            "/api/problems",
            headers=headers,
            params={"status": "Not Started", "limit": 5},
        )
        assert not_started.status_code == 200, not_started.text
        not_started_page = not_started.json()
        assert len(not_started_page["items"]) > 0, not_started.text
        assert not_started_page["total"] >= len(not_started_page["items"])
        assert "has_more" in not_started_page
        assert client.post(
            "/api/templates",
            headers=headers,
            json={"name": "x", "category": "x", "language": "", "code": "x"},
        ).status_code == 422


        templates = client.get("/api/templates", headers=headers)
        templates_page = templates.json()
        assert templates.status_code == 200 and templates_page["items"], templates.text
        assert templates_page["total"] >= len(templates_page["items"])
        system_template = next(t for t in templates_page["items"] if t["is_system"])

        readonly_update = client.put(
            f"/api/templates/{system_template['id']}",
            headers=headers,
            json={"name": "should-not-change"},
        )
        assert readonly_update.status_code == 403, readonly_update.text

        copied = client.post(f"/api/templates/{system_template['id']}/copy", headers=headers)
        assert copied.status_code == 201, copied.text
        copied_payload = copied.json()
        assert copied_payload["is_system"] is False
        assert copied_payload["owner_user_id"] is not None

        updated_copy = client.put(
            f"/api/templates/{copied_payload['id']}",
            headers=headers,
            json={"name": "personal-copy"},
        )
        assert updated_copy.status_code == 200, updated_copy.text
        assert updated_copy.json()["name"] == "personal-copy"

        username2 = f"reg2_{time.time_ns()}"
        response2 = client.post(
            "/api/auth/register",
            json={"username": username2, "email": f"{username2}@example.com", "password": password},
        )
        assert response2.status_code == 200, response2.text
        token2 = client.post(
            "/api/auth/login",
            data={"username": username2, "password": password},
        ).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        hidden_copy = client.get(f"/api/templates/{copied_payload['id']}", headers=headers2)
        assert hidden_copy.status_code == 404, hidden_copy.text

        invalid_quick_review = client.post(
            "/api/reviews/quick-review",
            headers=headers,
            json={"problem_id": 1, "result": "随便填"},
        )
        assert invalid_quick_review.status_code == 422, invalid_quick_review.text

        progress = client.patch(
            "/api/problems/1/progress",
            headers=headers,
            json={"status": "Need Review", "mastery_level": 2},
        )
        assert progress.status_code == 200, progress.text

        quick_review = client.post(
            "/api/reviews/quick-review",
            headers=headers,
            json={"problem_id": 1, "result": "掌握"},
        )
        assert quick_review.status_code == 200, quick_review.text

        history = client.get("/api/reviews/history", headers=headers, params={"problem_id": 1})
        history_page = history.json()
        assert history.status_code == 200 and len(history_page["items"]) >= 1, history.text
        assert history_page["total"] >= len(history_page["items"])

        effectiveness = client.get("/api/stats/review-effectiveness", headers=headers)
        assert effectiveness.status_code == 200, effectiveness.text
        assert effectiveness.json()["total_reviews"] >= 1, effectiveness.text

        dashboard = client.get("/api/stats/dashboard", headers=headers)
        assert dashboard.status_code == 200, dashboard.text
        assert "by_tag" in dashboard.json()["weakness_analysis"], dashboard.text

        ai_too_large = client.post(
            "/api/ai/hints",
            headers=headers,
            json={"description": "x" * 50001, "examples": [], "tags": []},
        )
        assert ai_too_large.status_code == 422, ai_too_large.text

        for _ in range(2):
            created_submission = client.post(
                "/api/submissions",
                headers=headers,
                json={
                    "problem_id": 1,
                    "language": "python",
                    "code": "print(1)",
                    "status": "Accepted",
                },
            )
            assert created_submission.status_code == 200, created_submission.text
        limited_submissions = client.get(
            "/api/submissions/problem/1",
            headers=headers,
            params={"limit": 1, "offset": 0},
        )
        assert limited_submissions.status_code == 200, limited_submissions.text
        limited_page = limited_submissions.json()
        assert len(limited_page["items"]) == 1, limited_submissions.text
        assert limited_page["total"] >= 2, limited_submissions.text
        assert limited_page["has_more"] is True, limited_submissions.text


def assert_legacy_migration() -> None:
    fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    Path(temp_path).unlink()
    db_path = Path(temp_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR)")
    cursor.execute("INSERT INTO users(id, username) VALUES (7, 'legacy')")
    cursor.execute("CREATE TABLE problems (id INTEGER PRIMARY KEY)")
    cursor.execute("INSERT INTO problems(id) VALUES (1)")
    cursor.execute(
        """
        CREATE TABLE progress (
            id INTEGER PRIMARY KEY,
            problem_id INTEGER NOT NULL UNIQUE,
            status VARCHAR,
            attempts INTEGER,
            solved_count INTEGER,
            mastery_level INTEGER,
            confidence INTEGER,
            is_favorite BOOLEAN,
            is_archived BOOLEAN
        )
        """
    )
    cursor.execute("INSERT INTO progress(id, problem_id, status) VALUES (1, 1, NULL)")
    cursor.execute(
        """
        CREATE TABLE problem_notes (
            id INTEGER PRIMARY KEY,
            problem_id INTEGER NOT NULL UNIQUE,
            idea TEXT,
            key_points TEXT,
            complexity TEXT,
            pitfalls TEXT,
            summary TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
        """
    )
    cursor.execute("INSERT INTO problem_notes(id, problem_id, idea) VALUES (1, 1, NULL)")
    cursor.execute("CREATE TABLE submissions (id INTEGER PRIMARY KEY, problem_id INTEGER, status VARCHAR)")
    cursor.execute("INSERT INTO submissions(id, problem_id, status) VALUES (1, 1, 'Accepted')")
    cursor.execute("CREATE TABLE templates (id INTEGER PRIMARY KEY, name VARCHAR, category VARCHAR, language VARCHAR, code TEXT)")
    cursor.execute("INSERT INTO templates(id, name, category, language, code) VALUES (1, 'legacy-template', 'array', 'python', 'print(1)')")
    conn.commit()
    conn.close()

    migrate_sqlite_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        for table in ["progress", "problem_notes", "submissions"]:
            columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})")]
            assert "user_id" in columns, (table, columns)

        for index_name in ["ux_progress_user_problem", "ux_problem_notes_user_problem"]:
            row = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                (index_name,),
            ).fetchone()
            assert row, index_name

        migration_row = cursor.execute(
            "SELECT name FROM schema_migrations WHERE name='2026-05-18-v4-hardening'"
        ).fetchone()
        assert migration_row, "schema_migrations marker missing"

        assert cursor.execute("SELECT user_id, status, attempts FROM progress").fetchone() == (
            7,
            "Not Started",
            0,
        )
        template_columns = [row[1] for row in cursor.execute("PRAGMA table_info(templates)")]
        assert "owner_user_id" in template_columns
        assert "is_system" in template_columns
        assert cursor.execute("SELECT owner_user_id, is_system FROM templates").fetchone() == (None, 1)
    finally:
        conn.close()
        # Windows: sqlite 连接对象可能仍持有句柄，强制 GC 后重试删除临时文件
        import gc
        gc.collect()
        for _ in range(3):
            try:
                db_path.unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.2)


def main() -> None:
    assert_api_regressions()
    print("OK api-regressions")
    assert_legacy_migration()
    print("OK legacy-migration")
    print("Regression checks passed.")


if __name__ == "__main__":
    main()
