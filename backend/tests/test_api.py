"""API tests against a real (SQLite-backed) FastAPI TestClient, not a
mocked service layer, mirroring
ai-governance-audit-readiness-register's test_api.py."""

import uuid

import pytest
from fastapi.testclient import TestClient

from incident_harness.api import create_app


@pytest.fixture()
def client():
    database_url = f"sqlite:///file:{uuid.uuid4().hex}?mode=memory&cache=shared&uri=true"
    app = create_app(database_url=database_url, seed=True)
    try:
        yield TestClient(app)
    finally:
        app.state.engine.dispose()


def test_list_scenarios_returns_all_six_with_four_steps_and_five_injects_each(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    for scenario in scenarios:
        assert len(scenario["steps"]) == 4
        assert len(scenario["injects"]) == 5


def test_list_injects_returns_all_thirty(client):
    response = client.get("/api/injects")
    assert response.status_code == 200
    assert len(response.json()) == 30


def test_list_runs_returns_the_six_seeded_official_runs(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 6
    assert all(r["kind"] == "official" for r in runs)
    assert all(r["action_count"] == 4 for r in runs)


def test_get_run_detail_reports_clean_timing_and_no_deviations(client):
    runs = client.get("/api/runs").json()
    run_id = runs[0]["run_id"]
    response = client.get(f"/api/runs/{run_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["deviations"] == []
    assert detail["timing"]["time_to_detect_minutes"] is not None
    assert detail["timing"]["time_to_contain_minutes"] is not None
    assert detail["timing"]["time_to_detect_minutes"] >= 0
    assert detail["timing"]["time_to_contain_minutes"] >= 0


def test_get_missing_run_is_404(client):
    response = client.get("/api/runs/does-not-exist")
    assert response.status_code == 404


def test_after_action_report_is_fully_exercised_from_the_seeded_demo_data(client):
    response = client.get("/api/after-action-report")
    assert response.status_code == 200
    report = response.json()
    assert report["total_steps"] == 24
    assert report["exercised_count"] == 24
    assert report["not_exercised_count"] == 0
    assert all(line["status"] == "exercised" for line in report["lines"])
