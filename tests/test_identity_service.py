from fastapi.testclient import TestClient

from TrueID_BE.api import app


client = TestClient(app)


def test_lookup_known_profile() -> None:
    response = client.post("/api/v1/lookup", json={"phone_number": "08030001111"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Kora Logistics"
    assert payload["location"] == "Victoria Island, Lagos"
    assert payload["match_strategy"] == "verified_profile"


def test_lookup_crowd_consensus_profile() -> None:
    response = client.post("/api/v1/lookup", json={"phone_number": "08112223334"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["location"] == "Lagos"
    assert payload["match_strategy"] == "crowd_consensus"


def test_report_spam_updates_score() -> None:
    response = client.post(
        "/api/v1/report-spam",
        json={"phone_number": "07011112222", "reason": "scam_fraud", "reporter_id": "user_test"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["spam"] is True
    assert payload["spam_score"] >= 72
    assert payload["total_reports"] >= 3


def test_upload_contacts_deduplicates() -> None:
    payload = {
        "user_id": "user_test",
        "contacts": [
            {
                "phone_number": "08091234567",
                "contact_name": "Chiamaka Okafor",
                "source_city": "Abuja",
                "source_state": "FCT",
            },
            {
                "phone_number": "08091234567",
                "contact_name": "Chiamaka Okafor",
                "source_city": "Abuja",
                "source_state": "FCT",
            },
        ],
    }
    response = client.post("/api/v1/upload-contacts", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == 1
    assert body["ignored_duplicates"] == 1


def test_lookup_uses_uploaded_contribution_region() -> None:
    upload_response = client.post(
        "/api/v1/upload-contacts",
        json={
            "user_id": "user_region_test",
            "contacts": [
                {
                    "phone_number": "08170000001",
                    "contact_name": "Debo Printing Press",
                    "source_city": "Osogbo",
                    "source_state": "Osun",
                }
            ],
        },
    )
    assert upload_response.status_code == 200

    lookup_response = client.post("/api/v1/lookup", json={"phone_number": "08170000001"})
    assert lookup_response.status_code == 200
    payload = lookup_response.json()
    assert payload["name"] == "Debo Printing Press"
    assert payload["location"] == "Osogbo, Osun"
    assert payload["match_strategy"] == "crowd_consensus"


def test_resync_enriches_existing_contribution_region() -> None:
    initial_upload = client.post(
        "/api/v1/upload-contacts",
        json={
            "user_id": "user_region_upgrade",
            "contacts": [
                {
                    "phone_number": "08170000002",
                    "contact_name": "Tade Workshop",
                }
            ],
        },
    )
    assert initial_upload.status_code == 200

    enriched_upload = client.post(
        "/api/v1/upload-contacts",
        json={
            "user_id": "user_region_upgrade",
            "contacts": [
                {
                    "phone_number": "08170000002",
                    "contact_name": "Tade Workshop",
                    "source_city": "Osogbo",
                    "source_state": "Osun",
                }
            ],
        },
    )
    assert enriched_upload.status_code == 200

    lookup_response = client.post("/api/v1/lookup", json={"phone_number": "08170000002"})
    assert lookup_response.status_code == 200
    payload = lookup_response.json()
    assert payload["location"] == "Osogbo, Osun"
