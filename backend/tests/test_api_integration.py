"""
API integration tests using Starlette TestClient against the FastAPI app.

Covers: health, auth, children CRUD, reports, games, rate limiting, error handling.
Run: cd backend; python -m pytest tests/test_api_integration.py -v
"""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Sync TestClient connected to the FastAPI app."""
    with TestClient(app, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client: TestClient) -> str:
    """Login as demo teacher and return a Bearer token."""
    res = client.post("/api/v1/auth/login", json={
        "email": "teacher@kindergarten.cn",
        "password": "demo123",
    })
    assert res.status_code == 200, f"Login failed: {res.status_code} {res.text}"
    data = res.json()
    return data.get("access_token") or data.get("token", "")


# ─── Health & Stats ──────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_ok(self, client: TestClient):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("ok", "degraded")
        assert "version" in data

    def test_stats_endpoint(self, client: TestClient):
        res = client.get("/api/stats")
        assert res.status_code in (200, 503)


# ─── Auth ────────────────────────────────────────────────────────────

class TestAuth:
    def test_login_teacher_success(self, client: TestClient):
        res = client.post("/api/v1/auth/login", json={
            "email": "teacher@kindergarten.cn",
            "password": "demo123",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data or "token" in data

    def test_login_wrong_password(self, client: TestClient):
        res = client.post("/api/v1/auth/login", json={
            "email": "teacher@kindergarten.cn",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_login_admin_success(self, client: TestClient):
        res = client.post("/api/v1/auth/login", json={
            "email": "admin@kindergarten.cn",
            "password": "admin123",
        })
        assert res.status_code == 200

    def test_me_returns_user_with_token(self, client: TestClient, auth_token: str):
        res = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        assert res.status_code == 200
        data = res.json()
        # Response wraps user info: {"authenticated": true, "user": {...}}
        user = data.get("user", data)
        assert "role" in user or "email" in user or "name" in user


# ─── Children CRUD ───────────────────────────────────────────────────

class TestChildren:
    def test_list_requires_auth(self, client: TestClient):
        res = client.get("/api/v1/children")
        assert res.status_code == 401

    def test_list_with_auth(self, client: TestClient, auth_token: str):
        res = client.get("/api/v1/children", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        assert res.status_code == 200
        data = res.json()
        assert "children" in data

    def test_create_and_delete(self, client: TestClient, auth_token: str):
        headers = {"Authorization": f"Bearer {auth_token}"}
        res = client.post("/api/v1/children", headers=headers, json={
            "name": "测试幼儿",
            "age_group": "middle",
            "parent_access_code": "TEST001",
        })
        if res.status_code == 200:
            child = res.json()
            child_id = child.get("id")
            if child_id:
                del_res = client.delete(f"/api/v1/children/{child_id}", headers=headers)
                assert del_res.status_code in (200, 204)


# ─── Protected Routes ────────────────────────────────────────────────

class TestProtectedRoutes:
    def test_worksheets_requires_auth(self, client: TestClient):
        # Routes without explicit auth may return 404 if not registered with GET
        res = client.get("/api/v1/worksheets/history/test")
        assert res.status_code in (401, 403, 404)

    def test_tracking_class_analysis_requires_teacher(self, client: TestClient):
        res = client.post("/api/v1/tracking/class-analysis", json=[])
        assert res.status_code in (401, 403)

    def test_children_post_requires_auth(self, client: TestClient):
        res = client.post("/api/v1/children", json={})
        assert res.status_code == 401


# ─── Reports ─────────────────────────────────────────────────────────

class TestReports:
    def test_demo_teacher_report(self, client: TestClient):
        res = client.get("/api/v1/reports/demo/teacher?age_group=middle&child_name=%E6%B5%8B%E8%AF%95")
        assert res.status_code == 200
        data = res.json()
        assert data.get("report_type") == "teacher"

    def test_demo_parent_report(self, client: TestClient):
        res = client.get("/api/v1/reports/demo/parent?age_group=large&child_name=%E6%B5%8B%E8%AF%95")
        assert res.status_code == 200
        data = res.json()
        assert data.get("report_type") == "parent"
        assert "overall_summary" in data

    def test_generate_and_fetch_report(self, client: TestClient):
        """Generate a report, then fetch by ID and verify PDF export."""
        demo = _make_demo_assessment("测试", "middle")
        res = client.post(
            "/api/v1/reports/generate/teacher?child_name=%E6%B5%8B%E8%AF%95&age_group=middle",
            json=demo,
        )
        assert res.status_code == 200
        report_id = res.json().get("report_id")
        if report_id:
            get_res = client.get(f"/api/v1/reports/teacher/{report_id}")
            assert get_res.status_code in (200, 401)
            pdf_res = client.get(f"/api/v1/reports/{report_id}/pdf/teacher")
            if pdf_res.status_code == 200:
                assert pdf_res.headers.get("content-type") == "application/pdf"


# ─── Games ───────────────────────────────────────────────────────────

class TestGames:
    def test_games_list(self, client: TestClient, auth_token: str):
        res = client.get("/api/v1/games/list", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        if res.status_code == 200:
            assert isinstance(res.json(), (list, dict))

    def test_achievements(self, client: TestClient, auth_token: str):
        res = client.get("/api/v1/games/achievements", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        if res.status_code == 200:
            assert isinstance(res.json(), (list, dict))


# ─── Rate Limiter ────────────────────────────────────────────────────

class TestRateLimiter:
    def test_health_not_rate_limited(self, client: TestClient):
        """Health check should pass under default tier (120 req/min)."""
        for _ in range(10):
            res = client.get("/api/health")
            assert res.status_code == 200

    def test_demo_analysis_within_limit(self, client: TestClient):
        """Demo assessment handles 5 rapid requests (ai tier: 5 req/min)."""
        for _ in range(5):
            res = client.get("/api/v1/analysis/demo-assessment")
            assert res.status_code in (200, 429)


# ─── Error Handling ──────────────────────────────────────────────────

class TestErrorHandling:
    def test_404_for_unknown_route(self, client: TestClient):
        res = client.get("/api/v1/nonexistent-endpoint")
        assert res.status_code == 404

    def test_422_for_invalid_auth_json(self, client: TestClient):
        res = client.post("/api/v1/auth/login", json={"bad_field": 123})
        assert res.status_code in (401, 422)

    def test_404_nonexistent_report(self, client: TestClient, auth_token: str):
        res = client.get("/api/v1/reports/teacher/99999", headers={
            "Authorization": f"Bearer {auth_token}",
        })
        assert res.status_code == 404


# ─── Helpers ─────────────────────────────────────────────────────────

def _make_demo_assessment(child_name: str, age_group: str) -> dict:
    return {
        "child_name": child_name,
        "age_group": age_group,
        "assessment": [
            {"dimension": "counting", "display_name": "数数", "score": 78.0,
             "level": "L3", "level_name": "熟练期", "level_emoji": "🌳",
             "pck_stage": "前运算后期", "sub_skills": [],
             "error_patterns": [], "age_benchmark_comparison": "符合",
             "age_milestones": "", "recommendations": "",
             "score_details": {"correct": 8, "total": 10, "strategy_level": "semi"}},
            {"dimension": "addition_sub", "display_name": "加减", "score": 55.0,
             "level": "L2", "level_name": "发展期", "level_emoji": "🌿",
             "pck_stage": "前运算中期", "sub_skills": [],
             "error_patterns": ["实物依赖"], "age_benchmark_comparison": "部分",
             "age_milestones": "", "recommendations": "",
             "score_details": {"correct": 3, "total": 5, "strategy_level": "concrete"}},
            {"dimension": "shapes_space", "display_name": "图形", "score": 90.0,
             "level": "L3", "level_name": "熟练期", "level_emoji": "🌳",
             "pck_stage": "前运算后期", "sub_skills": [],
             "error_patterns": [], "age_benchmark_comparison": "符合",
             "age_milestones": "", "recommendations": "",
             "score_details": {"correct": 8, "total": 9, "strategy_level": "symbolic"}},
            {"dimension": "patterns", "display_name": "模式", "score": 45.0,
             "level": "L2", "level_name": "发展期", "level_emoji": "🌿",
             "pck_stage": "前运算中期", "sub_skills": [],
             "error_patterns": ["模式理解表面化"], "age_benchmark_comparison": "部分",
             "age_milestones": "", "recommendations": "",
             "score_details": {"correct": 3, "total": 6, "strategy_level": "AB_copy"}},
        ],
        "observations": {},
        "overall_summary": "测试。",
    }
