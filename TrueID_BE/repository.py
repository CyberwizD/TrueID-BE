from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone

from TrueID_BE.config import Settings
from TrueID_BE.migrations import ensure_schema
from TrueID_BE.schemas import CallerProfileRecord, ContactContributionRecord, SpamReportRecord, CallLogRecord
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

    @abstractmethod
    def upsert_caller_profiles(self, profiles: list[CallerProfileRecord]) -> int:
        raise NotImplementedError

    @abstractmethod
    def save_call_log(self, record: CallLogRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_call_logs(self) -> list[CallLogRecord]:
        raise NotImplementedError


class InMemoryRepository(BaseRepository):
    def __init__(self) -> None:
        self._profiles = {profile.phone_number: deepcopy(profile) for profile in SEED_PROFILES}
        self._contributions = [deepcopy(item) for item in SEED_CONTRIBUTIONS]
        self._reports = [deepcopy(item) for item in SEED_REPORTS]
        self._call_logs: list[CallLogRecord] = []

    def get_profile(self, phone_number: str) -> CallerProfileRecord | None:
        return deepcopy(self._profiles.get(phone_number))

    def get_contributions(self, phone_number: str) -> list[ContactContributionRecord]:
        return [deepcopy(item) for item in self._contributions if item.phone_number == phone_number]

    def get_spam_reports(self, phone_number: str) -> list[SpamReportRecord]:
        return [deepcopy(item) for item in self._reports if item.phone_number == phone_number]

    def save_spam_report(self, report: SpamReportRecord) -> None:
        self._reports.append(deepcopy(report))

    def save_contact_contributions(self, contributions: list[ContactContributionRecord]) -> tuple[int, int]:
        existing_by_key = {
            (item.user_id, item.phone_number, item.contact_name.casefold()): item for item in self._contributions
        }
        saved = 0
        duplicates = 0
        for contribution in contributions:
            key = (
                contribution.user_id,
                contribution.phone_number,
                contribution.contact_name.casefold(),
            )
            existing = existing_by_key.get(key)
            if existing:
                if contribution.source_city and not existing.source_city:
                    existing.source_city = contribution.source_city
                if contribution.source_state and not existing.source_state:
                    existing.source_state = contribution.source_state
                duplicates += 1
                continue
            self._contributions.append(deepcopy(contribution))
            existing_by_key[key] = self._contributions[-1]
            saved += 1
        return saved, duplicates

    def upsert_caller_profiles(self, profiles: list[CallerProfileRecord]) -> int:
        imported = 0
        for profile in profiles:
            self._profiles[profile.phone_number] = deepcopy(profile)
            imported += 1
        return imported

    def save_call_log(self, record: CallLogRecord) -> None:
        self._call_logs.append(deepcopy(record))

    def get_call_logs(self) -> list[CallLogRecord]:
        return [deepcopy(item) for item in self._call_logs]


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
            network=row.get("network"),
            number_status=row.get("number_status"),
            source_provider=row.get("source_provider"),
            source_reference=row.get("source_reference"),
            last_verified_at=_parse_optional_datetime(row.get("last_verified_at")),
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
        grouped_existing = defaultdict(dict)
        phone_numbers = sorted({item.phone_number for item in contributions})
        if phone_numbers:
            response = (
                self._execute(
                    self._client.table("contact_contributions")
                    .select("id, user_id, phone_number, contact_name, source_city, source_state")
                    .in_("phone_number", phone_numbers)
                )
            )
            for row in response.data or []:
                grouped_existing[row["phone_number"]][
                    (row["user_id"], row["contact_name"].casefold())
                ] = row

        payload = []
        duplicates = 0
        for contribution in contributions:
            existing_key = (contribution.user_id, contribution.contact_name.casefold())
            existing = grouped_existing[contribution.phone_number].get(existing_key)
            if existing:
                updates = {}
                if contribution.source_city and not existing.get("source_city"):
                    updates["source_city"] = contribution.source_city
                if contribution.source_state and not existing.get("source_state"):
                    updates["source_state"] = contribution.source_state
                if updates:
                    self._execute(
                        self._client.table("contact_contributions")
                        .update(updates)
                        .eq("id", existing["id"])
                    )
                    existing.update(updates)
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
            grouped_existing[contribution.phone_number][existing_key] = payload[-1]

        if payload:
            self._execute(self._client.table("contact_contributions").insert(payload))
        return len(payload), duplicates

    def upsert_caller_profiles(self, profiles: list[CallerProfileRecord]) -> int:
        if not profiles:
            return 0

        payload = [
            {
                "phone_number": profile.phone_number,
                "display_name": profile.display_name,
                "city": profile.city,
                "state": profile.state,
                "country": profile.country,
                "spam_score": profile.spam_score,
                "confidence_score": profile.confidence_score,
                "is_business": profile.is_business,
                "verified": profile.verified,
                "network": profile.network,
                "number_status": profile.number_status,
                "source_provider": profile.source_provider,
                "source_reference": profile.source_reference,
                "last_verified_at": profile.last_verified_at.isoformat() if profile.last_verified_at else None,
                "updated_at": profile.updated_at.isoformat(),
            }
            for profile in profiles
        ]

        self._execute(
            self._client.table("caller_profiles").upsert(payload, on_conflict="phone_number")
        )
        return len(payload)

    def save_call_log(self, record: CallLogRecord) -> None:
        self._execute(self._client.table("call_logs").insert(
            {
                "id": record.id,
                "caller_number": record.caller_number,
                "callee_identifier": record.callee_identifier,
                "resolved_name": record.resolved_name,
                "created_at": record.created_at.isoformat(),
            }
        ))

    def get_call_logs(self) -> list[CallLogRecord]:
        response = self._execute(
            self._client.table("call_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(1000)
        )
        return [
            CallLogRecord(
                id=row["id"],
                caller_number=row["caller_number"],
                callee_identifier=row.get("callee_identifier"),
                resolved_name=row["resolved_name"],
                created_at=_parse_datetime(row.get("created_at")),
            )
            for row in response.data or []
        ]

    def _execute(self, request_builder):
        from postgrest.exceptions import APIError

        try:
            return request_builder.execute()
        except APIError as error:
            code = getattr(error, "code", None)
            if code == "PGRST205":
                raise MissingSupabaseSchemaError(
                    "Supabase is configured, but required tables are missing. "
                    "Apply the tracked SQL migrations in supabase/migrations or enable automatic migrations."
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


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
