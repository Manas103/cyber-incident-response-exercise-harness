"""API tests for the intake extension against a real (SQLite-backed) FastAPI TestClient,
mirroring test_api.py's own fixture pattern."""

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


def test_customer_report_ingest_is_normalized_and_scored(client):
    response = client.post(
        "/api/incidents/customer-report",
        json={
            "account_id": "acct-9001",
            "reported_by_email": "user@example.com",
            "description": "I can see another customer's invoices",
            "affected_product": "billing-api",
            "data_sensitivity": "customer_pii",
            "scope": "multiple_customers",
            "actively_exploited": False,
            "reported_at_minutes": 0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["channel"] == "customer_report"
    assert body["source_reference"] == "acct-9001"
    assert body["severity"] == "SEV3"


def test_internal_alert_and_researcher_disclosure_also_ingest(client):
    alert_response = client.post(
        "/api/incidents/internal-alert",
        json={
            "alert_id": "alert-9002",
            "source_system": "waf-edge",
            "rule_name": "sql-injection-pattern",
            "data_sensitivity": "payment_or_credentials",
            "scope": "platform_wide",
            "actively_exploited": True,
            "detected_at_minutes": 1,
        },
    )
    assert alert_response.status_code == 200
    assert alert_response.json()["severity"] == "SEV1"

    disclosure_response = client.post(
        "/api/incidents/researcher-disclosure",
        json={
            "researcher_handle": "researcher-009",
            "disclosure_channel": "security.txt",
            "vulnerability_summary": "IDOR on /api/invoices/{id}",
            "data_sensitivity": "none",
            "scope": "single_customer",
            "actively_exploited": False,
            "submitted_at_minutes": 2,
        },
    )
    assert disclosure_response.status_code == 200
    assert disclosure_response.json()["severity"] == "SEV4"


def test_list_incidents_returns_every_ingested_incident_across_channels(client):
    client.post(
        "/api/incidents/customer-report",
        json={
            "account_id": "acct-1",
            "reported_by_email": "a@example.com",
            "description": "d",
            "affected_product": "p",
            "data_sensitivity": "none",
            "scope": "single_customer",
            "actively_exploited": False,
            "reported_at_minutes": 0,
        },
    )
    client.post(
        "/api/incidents/internal-alert",
        json={
            "alert_id": "alert-1",
            "source_system": "edr-fleet",
            "rule_name": "r",
            "data_sensitivity": "none",
            "scope": "single_customer",
            "actively_exploited": False,
            "detected_at_minutes": 0,
        },
    )
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_notification_without_approval_is_held(client):
    created = client.post(
        "/api/incidents/customer-report",
        json={
            "account_id": "acct-2",
            "reported_by_email": "a@example.com",
            "description": "d",
            "affected_product": "p",
            "data_sensitivity": "customer_pii",
            "scope": "platform_wide",
            "actively_exploited": True,
            "reported_at_minutes": 0,
        },
    ).json()
    response = client.post(
        f"/api/incidents/{created['incident_id']}/notifications",
        json={"incident_id": created["incident_id"], "message": "your data may have been exposed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sent"] is False
    assert body["approved_by"] is None


def test_notification_with_named_approval_is_sent(client):
    created = client.post(
        "/api/incidents/customer-report",
        json={
            "account_id": "acct-3",
            "reported_by_email": "a@example.com",
            "description": "d",
            "affected_product": "p",
            "data_sensitivity": "customer_pii",
            "scope": "platform_wide",
            "actively_exploited": True,
            "reported_at_minutes": 0,
        },
    ).json()
    response = client.post(
        f"/api/incidents/{created['incident_id']}/notifications",
        json={
            "incident_id": created["incident_id"],
            "message": "your data may have been exposed",
            "approved_by": "J. Alvarez (IR Lead)",
        },
    )
    body = response.json()
    assert body["sent"] is True
    assert body["approved_by"] == "J. Alvarez (IR Lead)"


def test_notification_for_missing_incident_is_404(client):
    response = client.post("/api/incidents/999999/notifications", json={"incident_id": 999999, "message": "x"})
    assert response.status_code == 404
