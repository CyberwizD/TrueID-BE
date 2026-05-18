from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone

from TrueID_BE.config import Settings
from TrueID_BE.migrations import ensure_schema
from TrueID_BE.schemas import CallerProfileRecord, ContactContributionRecord, SpamReportRecord
from TrueID_BE.seeds import SEED_CONTRIBUTIONS, SEED_PROFILES, SEED_REPORTS


class MissingSupabaseSchemaError(RuntimeError):
    """Raised when the configured Supabase project is missing required tables."""


class BaseRepository(ABC):
    @abstractmethod
    def get_profile(self, phone_number: str) -> CallerProfileRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_contributions(self, phone_number: str) -> list[ContactContributionRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_spam_reports(self, phone_number: str) -> list[SpamReportRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_spam_report(self, report: SpamReportRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_contact_contributions(self, contributions: list[ContactContributionRecord]) -> tuple[int, int]:
        raise NotImplementedError


class InMemoryRepository(BaseRepository):
    def __init__(self) -> None:
        self._profiles = {profile.phone_number: deepcopy(profile) for profile in SEED_PROFILES}
        self._contributions = [deepcopy(item) for item in SEED_CONTRIBUTIONS]
        self._reports = [deepcopy(item) for item in SEED_REPORTS]

    def get_profile(self, phone_number: str) -> CallerProfileRecord | None:
        return deepcopy(self._profiles.get(phone_number))

    def get_contributions(self, phone_number: str) -> list[ContactContributionRecord]:
        return [deepcopy(item) for item in self._contributions if item.phone_number == phone_number]

    def get_spam_reports(self, phone_number: str) -> list[SpamReportRecord]:
        return [deepcopy(item) for item in self._reports if item.phone_number == phone_number]

    def save_spam_report(self, report: SpamReportRecord) -> None:
        self._reports.append(deepcopy(report))

    def save_contact_contributions(self, contributions: list[ContactContributionRecord]) -> tuple[int, int]:
        existing_keys = {
            (item.user_id, item.phone_number, item.contact_name.casefold()) for item in self._contributions
        }
        saved = 0
        duplicates = 0
        for contribution in contributions:
            key = (
                contribution.user_id,
                contribution.phone_number,
                contribution.contact_name.casefold(),
            )
            if key in existing_keys:
                duplicates += 1
                continue
            self._contributions.append(deepcopy(contribution))
            existing_keys.add(key)
            saved += 1
        return saved, duplicates


class SupabaseRepository(BaseRepository):
    def __init__(self, settings: Settings) -> None:
        from supabase import Client, create_client

        self._client: Client = create_client(
            settings.supabase_url or "",
            settings.supabase_admin_key or "",
        )

    def get_profile(self, phone_number: str) -> CallerProfileRecord | None:
        response = self._execute(
            self._client.table("caller_profiles")
            .select("*")
            .eq("phone_number", phone_number)
            .limit(1)
        )
        if not response.data:
            return None
        row = response.data[0]
        return CallerProfileRecord(
            phone_number=row["phone_number"],
            display_name=row["display_name"],
            city=row.get("city"),
            state=row.get("state"),
            country=row.get("country") or "Nigeria",
            spam_score=row.get("spam_score") or 0,
            confidence_score=row.get("confidence_score") or 0,
            is_business=bool(row.get("is_business")),
            verified=bool(row.get("verified")),
            created_at=_parse_datetime(row.get("created_at")),
            updated_at=_parse_datetime(row.get("updated_at")),
        )

    def get_contributions(self, phone_number: str) -> list[ContactContributionRecord]:
        response = self._execute(
            self._client.table("contact_contributions")
            .select("*")
            .eq("phone_number", phone_number)
        )
        return [
            ContactContributionRecord(
                id=row["id"],
                user_id=row["user_id"],
                phone_number=row["phone_number"],
                contact_name=row["contact_name"],
                source_city=row.get("source_city"),
                source_state=row.get("source_state"),
                created_at=_parse_datetime(row.get("created_at")),
            )
            for row in response.data or []
        ]

    def get_spam_reports(self, phone_number: str) -> list[SpamReportRecord]:
        response = self._execute(
            self._client.table("spam_reports")
            .select("*")
            .eq("phone_number", phone_number)
        )
        return [
            SpamReportRecord(
                id=row["id"],
                phone_number=row["phone_number"],
                reason=row["reason"],
                reporter_id=row.get("reporter_id"),
                notes=row.get("notes"),
                created_at=_parse_datetime(row.get("created_at")),
            )
            for row in response.data or []
        ]

    def save_spam_report(self, report: SpamReportRecord) -> None:
        self._execute(self._client.table("spam_reports").insert(
            {
                "id": report.id,
                "phone_number": report.phone_number,
                "reason": report.reason,
                "reporter_id": report.reporter_id,
                "notes": report.notes,
                "created_at": report.created_at.isoformat(),
            }
        ))

    def save_contact_contributions(self, contributions: list[ContactContributionRecord]) -> tuple[int, int]:
        grouped_existing = defaultdict(set)
        phone_numbers = sorted({item.phone_number for item in contributions})
        if phone_numbers:
            response = (
                self._execute(
                    self._client.table("contact_contributions")
                    .select("user_id, phone_number, contact_name")
                    .in_("phone_number", phone_numbers)
                )
            )
            for row in response.data or []:
                grouped_existing[row["phone_number"]].add(
                    (row["user_id"], row["contact_name"].casefold()),
                )

        payload = []
        duplicates = 0
        for contribution in contributions:
            existing_key = (contribution.user_id, contribution.contact_name.casefold())
            if existing_key in grouped_existing[contribution.phone_number]:
                duplicates += 1
                continue
            payload.append(
                {
                    "id": contribution.id,
                    "user_id": contribution.user_id,
                    "phone_number": contribution.phone_number,
                    "contact_name": contribution.contact_name,
                    "source_city": contribution.source_city,
                    "source_state": contribution.source_state,
                    "created_at": contribution.created_at.isoformat(),
                }
            )
            grouped_existing[contribution.phone_number].add(existing_key)

        if payload:
            self._execute(self._client.table("contact_contributions").insert(payload))
        return len(payload), duplicates

    def _execute(self, request_builder):
        from postgrest.exceptions import APIError

        try:
            return request_builder.execute()
        except APIError as error:
            code = getattr(error, "code", None)
            if code == "PGRST205":
                raise MissingSupabaseSchemaError(
                    "Supabase is configured, but required tables are missing. "
                    "Run supabase/schema.sql and supabase/seed.sql in your Supabase SQL editor."
                ) from error
            raise


def build_repository(settings: Settings) -> BaseRepository:
    if settings.resolved_backend == "supabase":
        try:
            ensure_schema(settings)
            return SupabaseRepository(settings)
        except ImportError:
            return InMemoryRepository()
    return InMemoryRepository()


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
