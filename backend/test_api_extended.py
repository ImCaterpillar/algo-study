"""Extended API regression tests: cover route branches that smoke/regression miss.

Run with:
    python -m coverage run --source=app -m pytest test_api_extended.py -q
"""
from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def _register_and_login(client: TestClient, prefix: str) -> dict[str, str]:
    username = f"{prefix}_{time.time_ns()}"
    password = "pass12345"
    email = f"{username}@example.com"
    resp = client.post("/api/auth/register", json={"username": username, "email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = client.post("/api/auth/login", data={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_notes_crud() -> None:
    with TestClient(app) as client:
        h = _register_and_login(client, "notes")

        # GET note for a non-existent problem -> 404
        assert client.get("/api/notes/999999", headers=h).status_code == 404

        # GET note with no existing note -> empty NoteOut
        empty = client.get("/api/notes/1", headers=h)
        assert empty.status_code == 200, empty.text
        assert empty.json()["problem_id"] == 1
        assert empty.json()["idea"] == ""

        # PUT upsert (create)
        created = client.put(
            "/api/notes/1",
            headers=h,
            json={"idea": "binary search", "key_points": "mid=(l+r)//2", "complexity": "O(log n)", "pitfalls": "overflow", "summary": "template"},
        )
        assert created.status_code == 200, created.text
        note = created.json()
        assert note["idea"] == "binary search"
        assert note["key_points"] == "mid=(l+r)//2"

        # GET returns the saved note
        fetched = client.get("/api/notes/1", headers=h)
        assert fetched.status_code == 200
        assert fetched.json()["idea"] == "binary search"

        # PUT update
        updated = client.put("/api/notes/1", headers=h, json={"idea": "updated idea"})
        assert updated.status_code == 200
        assert updated.json()["idea"] == "updated idea"

        # PUT on non-existent problem -> 404
        assert client.put("/api/notes/999999", headers=h, json={"idea": "x"}).status_code == 404


def test_templates_full_matrix() -> None:
    with TestClient(app) as client:
        h = _register_and_login(client, "tpl")

        # list categories / languages endpoints
        cats = client.get("/api/templates/categories", headers=h)
        assert cats.status_code == 200 and isinstance(cats.json(), list)
        langs = client.get("/api/templates/languages", headers=h)
        assert langs.status_code == 200 and isinstance(langs.json(), list)

        # create personal template with tags & usage_scenario
        created = client.post(
            "/api/templates",
            headers=h,
            json={"name": "py-dp", "category": "dp", "language": "python", "code": "def f(): pass",
                  "explanation": "dp template", "tags": ["dp", "array"], "usage_scenario": "knapsack"},
        )
        assert created.status_code == 201, created.text
        tpl = created.json()
        assert tpl["is_system"] is False
        assert "dp" in tpl["tags"]

        # filter by language/category/tag
        by_lang = client.get("/api/templates?language=python", headers=h)
        assert by_lang.status_code == 200 and by_lang.json()["total"] >= 1
        by_cat = client.get("/api/templates?category=dp", headers=h)
        assert by_cat.status_code == 200 and by_cat.json()["total"] >= 1
        by_tag = client.get("/api/templates?tag=dp", headers=h)
        assert by_tag.status_code == 200 and any("dp" in t["tags"] for t in by_tag.json()["items"])

        # get one template by id
        got = client.get(f"/api/templates/{tpl['id']}", headers=h)
        assert got.status_code == 200 and got.json()["name"] == "py-dp"

        # recommend templates for a problem (match by tags)
        rec = client.get("/api/templates/recommend/1", headers=h)
        assert rec.status_code == 200 and isinstance(rec.json(), list)
        rec_missing = client.get("/api/templates/recommend/999999", headers=h)
        assert rec_missing.status_code == 200 and rec_missing.json() == []

        # update personal template (full fields)
        upd = client.put(
            f"/api/templates/{tpl['id']}", headers=h,
            json={"name": "py-dp-v2", "code": "def g(): return 1", "tags": ["dp", "greedy"]},
        )
        assert upd.status_code == 200
        assert upd.json()["name"] == "py-dp-v2"
        assert "greedy" in upd.json()["tags"]

        # delete personal template
        deleted = client.delete(f"/api/templates/{tpl['id']}", headers=h)
        assert deleted.status_code == 200 and deleted.json()["success"] is True

        # after delete -> 404 on get
        assert client.get(f"/api/templates/{tpl['id']}", headers=h).status_code == 404

        # delete a system template -> 403
        system_id = next(
            t["id"] for t in client.get("/api/templates", headers=h).json()["items"] if t["is_system"]
        )
        assert client.delete(f"/api/templates/{system_id}", headers=h).status_code == 403

        # limit validation: limit=0 -> 422, limit=1000 -> 422
        assert client.get("/api/templates?limit=0", headers=h).status_code == 422
        assert client.get("/api/templates?limit=1000", headers=h).status_code == 422


def test_problems_filters_and_progress() -> None:
    with TestClient(app) as client:
        h = _register_and_login(client, "probs")

        # difficulty filter
        med = client.get("/api/problems?difficulty=Medium&limit=5", headers=h)
        assert med.status_code == 200, med.text
        assert all(p["difficulty"] == "Medium" for p in med.json()["items"])

        # stage filter
        stage = client.get("/api/problems?stage=Graph&limit=5", headers=h)
        assert stage.status_code == 200

        # tag filter
        tagged = client.get("/api/problems?tag=dp&limit=5", headers=h)
        assert tagged.status_code == 200

        # progress update + favorite/archive fields
        prog = client.patch(
            "/api/problems/1/progress",
            headers=h,
            json={"status": "Accepted", "is_favorite": True, "mastery_level": 3, "confidence": 4, "attempts": 5},
        )
        assert prog.status_code == 200, prog.text
        out = prog.json()["progress"]
        assert out["status"] == "Accepted"
        assert out["is_favorite"] is True
        assert out["mastery_level"] == 3

        # status filter "Accepted" now returns problem 1
        solved = client.get("/api/problems?status=Accepted&limit=5", headers=h)
        assert solved.status_code == 200 and any(p["id"] == 1 for p in solved.json()["items"])

        # invalid status value is accepted as filter (no crash)
        weird = client.get("/api/problems?status=Not%20Exists&limit=5", headers=h)
        assert weird.status_code == 200


def test_reviews_and_stats() -> None:
    with TestClient(app) as client:
        h = _register_and_login(client, "revs")

        # create a submission first so stats have data
        sub = client.post(
            "/api/submissions",
            headers=h,
            json={"problem_id": 1, "language": "python", "code": "print(1)", "status": "Accepted"},
        )
        assert sub.status_code == 200, sub.text

        # review effectiveness
        eff = client.get("/api/stats/review-effectiveness", headers=h)
        assert eff.status_code == 200 and "total_reviews" in eff.json()

        # dashboard with weakness analysis
        dash = client.get("/api/stats/dashboard", headers=h)
        assert dash.status_code == 200 and "weakness_analysis" in dash.json()

        # submissions with filters
        subs = client.get("/api/submissions/problem/1?limit=10&offset=0", headers=h)
        assert subs.status_code == 200 and subs.json()["total"] >= 1

        # quick-review full flow then history
        qr = client.post("/api/reviews/quick-review", headers=h, json={"problem_id": 1, "result": "掌握"})
        assert qr.status_code == 200, qr.text
        history = client.get("/api/reviews/history?problem_id=1", headers=h)
        assert history.status_code == 200 and len(history.json()["items"]) >= 1


def test_execute_endpoints() -> None:
    with TestClient(app) as client:
        h = _register_and_login(client, "exec")

        # javascript execution
        js = client.post("/api/execute", headers=h, json={"language": "javascript", "code": "console.log(2+2)"})
        assert js.status_code == 200, js.text

        # sandbox python execution
        py = client.post("/api/sandbox/execute", headers=h, json={"language": "python", "code": "print(3*3)"})
        assert py.status_code == 200, py.text

        # invalid language -> expect 4xx validation error
        bad = client.post("/api/execute", headers=h, json={"language": "brainfuck", "code": "x"})
        assert bad.status_code in (400, 422), bad.text


def test_health_and_auth_edges() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200 and health.json()["status"] == "ok"

        # me without token -> 401
        assert client.get("/api/auth/me").status_code == 401

        # register with bad email -> 422
        bad = client.post("/api/auth/register", json={"username": "baduser", "email": "not-an-email", "password": "pass12345"})
        assert bad.status_code == 422, bad.text

        # login with wrong password -> 401
        h = _register_and_login(client, "auth")
        wrong = client.post("/api/auth/login", data={"username": "auth", "password": "wrongpass"})
        assert wrong.status_code in (400, 401), wrong.text
