from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


SpamReason = Literal[
    "scam_fraud",
    "telemarketing",
    "harassment",
    "loan_spam",
    "robocall",
    "unknown_threat",
]

CallerType = Literal["individual", "business", "unknown"]
MatchStrategy = Literal["verified_profile", "known_profile", "crowd_consensus", "unknown"]


class LookupRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=24)
    requester_id: str | None = None


class SourceSignal(BaseModel):
    source: Literal["profile", "crowd_contact", "spam_reports", "location_hint", "telecom_registry"]
    weight: int
    label: str


class LookupResponse(BaseModel):
    phone_number: str
    name: str
    location: str
    spam: bool
    confidence: int = Field(ge=0, le=100)
    spam_score: int = Field(ge=0, le=100)
    caller_type: CallerType
    verified: bool = False
    match_strategy: MatchStrategy
    network: str | None = None
    number_status: str | None = None
    sources: list[SourceSignal]


class SpamReportRequest(BaseModel):
    phone_number: str = Field(min_length=7, max_length=24)
    reason: SpamReason
    reporter_id: str | None = None
    notes: str | None = Field(default=None, max_length=240)


class SpamReportResponse(BaseModel):
    phone_number: str
    spam_score: int = Field(ge=0, le=100)
    spam: bool
    total_reports: int = Field(ge=0)


class ContactContributionInput(BaseModel):
    phone_number: str = Field(min_length=7, max_length=24)
    contact_name: str = Field(min_length=2, max_length=120)
    source_city: str | None = Field(default=None, max_length=80)
    source_state: str | None = Field(default=None, max_length=80)

    @field_validator("contact_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return " ".join(value.split())


class UploadContactsRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=120)
    contacts: list[ContactContributionInput] = Field(min_length=1, max_length=1000)


class UploadContactsResponse(BaseModel):
    uploaded: int = Field(ge=0)
    unique_numbers: int = Field(ge=0)
    ignored_duplicates: int = Field(ge=0)


class CuratedCallerProfileInput(BaseModel):
    phone_number: str = Field(min_length=7, max_length=24)
    display_name: str = Field(min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)
    country: str = Field(default="Nigeria", min_length=2, max_length=80)
    spam_score: int = Field(default=0, ge=0, le=100)
    confidence_score: int = Field(default=60, ge=0, le=100)
    is_business: bool = False
    verified: bool = True
    network: str | None = Field(default=None, max_length=80)
    number_status: str | None = Field(default=None, max_length=32)
    source_provider: str = Field(default="curated_import", min_length=2, max_length=80)
    source_reference: str | None = Field(default=None, max_length=160)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        return " ".join(value.split())


class ImportCallerProfilesRequest(BaseModel):
    profiles: list[CuratedCallerProfileInput] = Field(min_length=1, max_length=5000)


class ImportCallerProfilesResponse(BaseModel):
    imported: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str
    backend: Literal["memory", "supabase"]


@dataclass(slots=True)
class CallerProfileRecord:
    phone_number: str
    display_name: str
    city: str | None = None
    state: str | None = None
    country: str = "Nigeria"
    spam_score: int = 0
    confidence_score: int = 0
    is_business: bool = False
    verified: bool = False
    network: str | None = None
    number_status: str | None = None
    source_provider: str | None = None
    source_reference: str | None = None
    last_verified_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class ContactContributionRecord:
    user_id: str
    phone_number: str
    contact_name: str
    source_city: str | None = None
    source_state: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class SpamReportRecord:
    phone_number: str
    reason: SpamReason
    reporter_id: str | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class CallLogRecord:
    caller_number: str
    callee_identifier: str | None
    resolved_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))
