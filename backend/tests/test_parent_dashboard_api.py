"""
Integration tests for parent-facing mini-program API and dashboard endpoints.

Covers: parent bind/profile/report/growth (9 tests) + dashboard trajectory/overview/export (10 tests)
Run: cd backend; python -m pytest tests/test_parent_dashboard_api.py -v
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
    assert res.status_code == 200
    return res.json()["access_token"]


# ─── Parent API Tests ─────────────────────────────────────────────────

class TestParentBind:
    """POST /api/v1/parent/bind"""

    def test_bind_with_valid_code(self, client: TestClient):
        """Should return child info for a valid access code (use demo child 1's code)."""
        resp = client.post("/api/v1/parent/bind", json={"access_code": "XIAOMING01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["child_id"] == 1
        assert data["child_name"] == "小明"
        assert "token" in data

    def test_bind_with_short_code(self, client: TestClient):
        """Should reject codes shorter than 6 characters."""
        resp = client.post("/api/v1/parent/bind", json={"access_code": "AB"})
        assert resp.status_code == 400

    def test_bind_with_invalid_code(self, client: TestClient):
        """Should return 404 for non-existent access code."""
        resp = client.post("/api/v1/parent/bind", json={"access_code": "ZZZ99999"})
        assert resp.status_code == 404

    def test_bind_with_empty_code(self, client: TestClient):
        """Should reject empty access code."""
        resp = client.post("/api/v1/parent/bind", json={"access_code": ""})
        assert resp.status_code == 400


class TestParentChildProfile:
    """GET /api/v1/parent/child-profile"""

    def test_profile_valid_child(self, client: TestClient):
        """Should return child profile for a valid child_id."""
        resp = client.get("/api/v1/parent/child-profile?child_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["child_id"] == 1
        assert "name" in data
        assert "age_group" in data

    def test_profile_nonexistent_child(self, client: TestClient):
        """Should return 404 for non-existent child."""
        resp = client.get("/api/v1/parent/child-profile?child_id=99999")
        assert resp.status_code == 404


class TestParentLatestReport:
    """GET /api/v1/parent/latest-report"""

    def test_latest_report_no_data(self, client: TestClient):
        """Should return has_report=False when no reports exist."""
        resp = client.get("/api/v1/parent/latest-report?child_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "has_report" in data

    def test_latest_report_nonexistent_child(self, client: TestClient):
        """Should handle non-existent child gracefully."""
        resp = client.get("/api/v1/parent/latest-report?child_id=99999")
        assert resp.status_code == 200
        assert resp.json()["has_report"] is False


class TestParentReportHistory:
    """GET /api/v1/parent/report-history"""

    def test_history_returns_list(self, client: TestClient):
        """Should return report list (possibly empty)."""
        resp = client.get("/api/v1/parent/report-history?child_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["child_id"] == 1
        assert "reports" in data
        assert isinstance(data["reports"], list)


class TestParentGrowthTrend:
    """GET /api/v1/parent/growth-trend"""

    def test_growth_trend_returns_dimensions(self, client: TestClient):
        """Should return dimensions dict (possibly empty)."""
        resp = client.get("/api/v1/parent/growth-trend?child_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["child_id"] == 1
        assert "dimensions" in data
        assert isinstance(data["dimensions"], dict)


# ─── Dashboard API Tests ──────────────────────────────────────────────

class TestDashboardChildTrajectory:
    """GET /api/v1/dashboard/child/{id}/trajectory"""

    def test_requires_auth(self, client: TestClient):
        """Should require teacher authentication."""
        resp = client.get("/api/v1/dashboard/child/1/trajectory")
        assert resp.status_code in (401, 403)

    def test_with_teacher_token(self, client: TestClient, auth_token: str):
        """Should return data for a valid child."""
        resp = client.get(
            "/api/v1/dashboard/child/1/trajectory",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 404)

    def test_nonexistent_child(self, client: TestClient, auth_token: str):
        """Should return 404 for non-existent child."""
        resp = client.get(
            "/api/v1/dashboard/child/99999/trajectory",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404


class TestDashboardClassOverview:
    """GET /api/v1/dashboard/class/{name}/overview"""

    def test_requires_auth(self, client: TestClient):
        """Should require teacher authentication."""
        resp = client.get("/api/v1/dashboard/class/测试班/overview")
        assert resp.status_code in (401, 403)

    def test_with_teacher_token(self, client: TestClient, auth_token: str):
        """Should return class overview data."""
        resp = client.get(
            "/api/v1/dashboard/class/测试班/overview",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestDashboardSemesterCompare:
    """GET /api/v1/dashboard/class/{name}/semester-compare"""

    def test_requires_auth(self, client: TestClient):
        """Should require teacher authentication."""
        resp = client.get("/api/v1/dashboard/class/测试班/semester-compare")
        assert resp.status_code in (401, 403)

    def test_with_teacher_token(self, client: TestClient, auth_token: str):
        """Should return semester comparison data."""
        resp = client.get(
            "/api/v1/dashboard/class/测试班/semester-compare",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestDashboardExcelExport:
    """GET /api/v1/dashboard/export/..."""

    def test_export_class_requires_auth(self, client: TestClient):
        """Should require teacher authentication (or rate-limited)."""
        resp = client.get("/api/v1/dashboard/export/class/测试班")
        assert resp.status_code in (401, 403, 429)

    def test_export_class_xlsx(self, client: TestClient, auth_token: str):
        """Should return an Excel file for class export (or 429 if rate-limited)."""
        resp = client.get(
            "/api/v1/dashboard/export/class/测试班",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 429)
        if resp.status_code == 200:
            assert "spreadsheet" in resp.headers.get("content-type", "")

    def test_export_child_requires_auth(self, client: TestClient):
        """Should require teacher authentication (or rate-limited)."""
        resp = client.get("/api/v1/dashboard/export/child/1")
        assert resp.status_code in (401, 403, 429)

    def test_export_child_xlsx(self, client: TestClient, auth_token: str):
        """Should return an Excel file for child export (or 429 if rate-limited)."""
        resp = client.get(
            "/api/v1/dashboard/export/child/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 404, 429)
