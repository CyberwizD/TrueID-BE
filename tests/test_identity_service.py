from types import SimpleNamespace

from fastapi.testclient import TestClient

from TrueID_BE.api import app
from TrueID_BE.config import get_settings
from TrueID_BE.repository import InMemoryRepository
from TrueID_BE.services.identity import IdentityService


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


def test_import_caller_profiles_endpoint_upserts_with_admin_token(monkeypatch) -> None:
    monkeypatch.setenv("TRUEID_PROFILE_IMPORT_TOKEN", "test-import-token")
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/admin/import-caller-profiles",
        headers={"x-admin-token": "test-import-token"},
        json={
            "profiles": [
                {
                    "phone_number": "08035550000",
                    "display_name": "Prime Dental Clinic",
                    "city": "Lekki",
                    "state": "Lagos",
                    "verified": True,
                    "is_business": True,
                    "confidence_score": 88,
                    "network": "MTN",
                    "number_status": "NORMAL",
                    "source_provider": "trusted_partner",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["imported"] == 1

    lookup = client.post("/api/v1/lookup", json={"phone_number": "08035550000"})
    assert lookup.status_code == 200
    payload = lookup.json()
    assert payload["name"] == "Prime Dental Clinic"
    assert payload["location"] == "Lekki, Lagos"
    assert payload["network"] == "MTN"
    assert payload["number_status"] == "NORMAL"
    assert payload["match_strategy"] == "verified_profile"

    monkeypatch.delenv("TRUEID_PROFILE_IMPORT_TOKEN", raising=False)
    get_settings.cache_clear()


def test_lookup_can_include_tirms_signal_without_curated_profile() -> None:
    repository = InMemoryRepository()
    settings = get_settings()
    telecom_registry = SimpleNamespace(
        lookup=lambda _: SimpleNamespace(
            number_status="SWAPPED",
            network="GLOBACOM",
            verification_status="VERIFIED",
            request_id="req-123",
            occurrence_of_status_date="2026-05-22",
        )
    )
    service = IdentityService(repository=repository, settings=settings, telecom_registry=telecom_registry)

    payload = service.lookup("09099990000")
    assert payload.name == "Unknown caller"
    assert payload.network == "GLOBACOM"
    assert payload.number_status == "SWAPPED"
    assert payload.spam is True
    assert any(signal.source == "telecom_registry" for signal in payload.sources)


def test_imported_number_status_can_raise_spam_signal(monkeypatch) -> None:
    monkeypatch.setenv("TRUEID_PROFILE_IMPORT_TOKEN", "test-import-token")
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/admin/import-caller-profiles",
        headers={"x-admin-token": "test-import-token"},
        json={
            "profiles": [
                {
                    "phone_number": "08036660000",
                    "display_name": "Flagged Enterprise",
                    "city": "Ikeja",
                    "state": "Lagos",
                    "verified": True,
                    "is_business": True,
                    "confidence_score": 84,
                    "number_status": "BLACKLISTED",
                    "source_provider": "trusted_partner",
                }
            ]
        },
    )
    assert response.status_code == 200

    lookup = client.post("/api/v1/lookup", json={"phone_number": "08036660000"})
    assert lookup.status_code == 200
    payload = lookup.json()
    assert payload["number_status"] == "BLACKLISTED"
    assert payload["spam"] is True

    monkeypatch.delenv("TRUEID_PROFILE_IMPORT_TOKEN", raising=False)
    get_settings.cache_clear()
