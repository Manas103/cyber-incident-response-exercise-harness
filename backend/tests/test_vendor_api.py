"""API tests for the vendor-feed extension against a real (SQLite-backed) FastAPI
TestClient, mirroring test_intake_api.py's own fixture pattern."""

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


def _ingest_one_chain(client):
    client.post(
        "/api/vendor-alerts/identity-provider",
        json={
            "event_id": "idp-api-1", "user": "api-user@example.com", "source_ip": "203.0.113.9",
            "risk_event_type": "impossible_travel", "data_sensitivity": "none", "scope": "single_customer",
            "actively_exploited": False, "observed_at_minutes": 0,
        },
    )
    client.post(
        "/api/vendor-alerts/email-gateway",
        json={
            "message_id": "msg-api-1", "recipient_user": "api-user@example.com",
            "sender_domain": "lookalike.example", "verdict": "phishing_delivered",
            "data_sensitivity": "none", "scope": "single_customer", "actively_exploited": False,
            "delivered_at_minutes": 15,
        },
    )
    client.post(
        "/api/vendor-alerts/endpoint-detection",
        json={
            "detection_id": "edr-api-1", "host": "WKS-API-1", "process_name": "powershell.exe",
            "rule_name": "suspicious_macro_spawned_shell", "data_sensitivity": "none",
            "scope": "single_customer", "actively_exploited": False, "detected_at_minutes": 40,
        },
    )
    response = client.post(
        "/api/vendor-alerts/mdr-escalation",
        json={
            "escalation_id": "mdr-api-1", "host": "WKS-API-1", "user": "api-user@example.com",
            "escalation_reason": "phishing-to-shell chain confirmed", "data_sensitivity": "customer_pii",
            "scope": "multiple_customers", "actively_exploited": True, "escalated_at_minutes": 55,
        },
    )
    assert response.status_code == 200
    return response


def test_four_feeds_ingest_and_correlate_into_one_incident(client):
    _ingest_one_chain(client)
    response = client.get("/api/vendor-incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) == 1
    incident = incidents[0]
    assert len(incident["alert_ids"]) == 4
    assert set(incident["feeds"]) == {
        "endpoint_detection", "email_gateway", "identity_provider", "managed_detection_escalation",
    }
    assert incident["severity"] == "SEV2"


def test_ack_and_executed_containment_produce_timing(client):
    _ingest_one_chain(client)
    incident_id = client.get("/api/vendor-incidents").json()[0]["incident_id"]

    client.post(
        "/api/vendor-incidents/ack",
        json={"incident_id": incident_id, "analyst_name": "A. Ng", "ack_minutes": 10},
    )
    client.post(
        "/api/containment-actions",
        json={
            "action_id": "api-contain-1", "incident_id": incident_id, "action_type": "host_isolation",
            "target_entity": "WKS-API-1", "action_minutes": 30, "approved_by": "J. Alvarez (IR Lead)",
        },
    )

    incident = client.get("/api/vendor-incidents").json()[0]
    assert incident["time_to_detect_minutes"] == 10
    assert incident["time_to_contain_minutes"] == 30


def test_containment_without_approval_is_refused_and_leaves_no_trace(client):
    _ingest_one_chain(client)
    incident_id = client.get("/api/vendor-incidents").json()[0]["incident_id"]

    response = client.post(
        "/api/containment-actions",
        json={
            "action_id": "api-contain-2", "incident_id": incident_id, "action_type": "session_revoke",
            "target_entity": "api-user@example.com", "action_minutes": 20, "approved_by": None,
        },
    )
    body = response.json()
    assert body["executed"] is False
    assert body["approved_by"] is None
    assert body["state_before"] == body["state_after"] == "normal"


def test_containment_action_can_be_undone(client):
    _ingest_one_chain(client)
    incident_id = client.get("/api/vendor-incidents").json()[0]["incident_id"]

    created = client.post(
        "/api/containment-actions",
        json={
            "action_id": "api-contain-3", "incident_id": incident_id, "action_type": "token_reset",
            "target_entity": "api-user@example.com", "action_minutes": 20, "approved_by": "M. Chen (Trust & Safety Manager)",
        },
    ).json()
    assert created["executed"] is True
    assert created["state_after"] == "token_reset"

    undone = client.post(f"/api/containment-actions/{created['action_id']}/undo")
    assert undone.status_code == 200
    assert undone.json()["undone"] is True

    second_undo = client.post(f"/api/containment-actions/{created['action_id']}/undo")
    assert second_undo.status_code == 409


def test_undo_of_a_never_executed_action_is_rejected(client):
    _ingest_one_chain(client)
    incident_id = client.get("/api/vendor-incidents").json()[0]["incident_id"]

    refused = client.post(
        "/api/containment-actions",
        json={
            "action_id": "api-contain-4", "incident_id": incident_id, "action_type": "host_isolation",
            "target_entity": "WKS-API-1", "action_minutes": 20, "approved_by": None,
        },
    ).json()
    response = client.post(f"/api/containment-actions/{refused['action_id']}/undo")
    assert response.status_code == 400
