from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from TrueID_BE.config import Settings


@dataclass(slots=True)
class TelecomRegistryResult:
    number_status: str | None = None
    network: str | None = None
    verification_status: str | None = None
    request_id: str | None = None
    occurrence_of_status_date: str | None = None


class TelecomRegistryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def lookup(self, normalized_phone_number: str) -> TelecomRegistryResult | None:
        if not self.settings.tirms_enabled:
            return None

        request = Request(
            url=f"{self.settings.tirms_base_url.rstrip('/')}/phone-numbers/verify",
            data=json.dumps(
                {
                    "phoneNumber": normalized_phone_number.lstrip("+"),
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.tirms_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.settings.tirms_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        data = payload.get("data")
        if not isinstance(data, dict):
            return None

        return TelecomRegistryResult(
            number_status=_clean(data.get("status")),
            network=_clean(data.get("mobileNetwork")),
            verification_status=_clean(data.get("verificationStatus")),
            request_id=_clean(data.get("requestId")),
            occurrence_of_status_date=_clean(data.get("occurrenceOfStatusDate")),
        )


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None
