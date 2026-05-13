from __future__ import annotations

from collections import Counter

from fastapi import HTTPException

from TrueID_BE.config import Settings
from TrueID_BE.repository import BaseRepository
from TrueID_BE.schemas import (
    CallerProfileRecord,
    ContactContributionInput,
    ContactContributionRecord,
    LookupResponse,
    SourceSignal,
    SpamReportRecord,
    SpamReportResponse,
    UploadContactsResponse,
)
from TrueID_BE.services.location import format_location, infer_location_from_contributions
from TrueID_BE.services.normalization import normalize_phone_number


BUSINESS_KEYWORDS = {
    "bank",
    "clinic",
    "company",
    "dental",
    "enterprise",
    "hub",
    "limited",
    "ltd",
    "logistics",
    "mart",
    "pharmacy",
    "school",
    "services",
    "shop",
    "studio",
}

SPAM_REASON_WEIGHTS = {
    "scam_fraud": 22,
    "telemarketing": 11,
    "harassment": 18,
    "loan_spam": 16,
    "robocall": 13,
    "unknown_threat": 14,
}


class IdentityService:
    def __init__(self, repository: BaseRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def lookup(self, phone_number: str) -> LookupResponse:
        normalized_phone = self._normalize_or_raise(phone_number)
        profile = self.repository.get_profile(normalized_phone)
        contributions = self.repository.get_contributions(normalized_phone)
        reports = self.repository.get_spam_reports(normalized_phone)

        top_name, name_votes = self._resolve_name(profile, contributions)
        location = self._resolve_location(profile, contributions)
        spam_score = self._resolve_spam_score(profile, reports)
        caller_type = self._resolve_caller_type(profile, top_name)
        match_strategy = self._resolve_match_strategy(profile, name_votes)
        confidence = self._resolve_confidence(profile, name_votes, contributions, reports)

        sources = self._resolve_sources(profile, name_votes, contributions, reports, location)

        return LookupResponse(
            phone_number=normalized_phone,
            name=top_name,
            location=location,
            spam=spam_score >= self.settings.spam_threshold,
            confidence=confidence,
            spam_score=spam_score,
            caller_type=caller_type,
            verified=bool(profile and profile.verified),
            match_strategy=match_strategy,
            sources=sources,
        )

    def report_spam(
        self,
        phone_number: str,
        reason: str,
        reporter_id: str | None,
        notes: str | None,
    ) -> SpamReportResponse:
        normalized_phone = self._normalize_or_raise(phone_number)
        report = SpamReportRecord(
            phone_number=normalized_phone,
            reason=reason,
            reporter_id=reporter_id,
            notes=notes,
        )
        self.repository.save_spam_report(report)
        reports = self.repository.get_spam_reports(normalized_phone)
        profile = self.repository.get_profile(normalized_phone)
        spam_score = self._resolve_spam_score(profile, reports)
        return SpamReportResponse(
            phone_number=normalized_phone,
            spam_score=spam_score,
            spam=spam_score >= self.settings.spam_threshold,
            total_reports=len(reports),
        )

    def upload_contacts(
        self,
        user_id: str,
        contacts: list[ContactContributionInput],
    ) -> UploadContactsResponse:
        normalized_contributions = [
            ContactContributionRecord(
                user_id=user_id,
                phone_number=self._normalize_or_raise(contact.phone_number),
                contact_name=contact.contact_name,
                source_city=contact.source_city,
                source_state=contact.source_state,
            )
            for contact in contacts
        ]
        saved, duplicates = self.repository.save_contact_contributions(normalized_contributions)
        unique_numbers = len({item.phone_number for item in normalized_contributions})
        return UploadContactsResponse(
            uploaded=saved,
            unique_numbers=unique_numbers,
            ignored_duplicates=duplicates,
        )

    def _normalize_or_raise(self, phone_number: str) -> str:
        try:
            return normalize_phone_number(phone_number)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    def _resolve_name(
        self,
        profile: CallerProfileRecord | None,
        contributions: list[ContactContributionRecord],
    ) -> tuple[str, int]:
        if profile and profile.display_name:
            return profile.display_name, max(1, _count_matching_names(profile.display_name, contributions))

        if not contributions:
            return "Unknown caller", 0

        counts = Counter(_canonical_name(item.contact_name) for item in contributions if item.contact_name)
        top_name, votes = counts.most_common(1)[0]
        return top_name, votes

    def _resolve_location(
        self,
        profile: CallerProfileRecord | None,
        contributions: list[ContactContributionRecord],
    ) -> str:
        if profile:
            location = format_location(profile.city, profile.state, profile.country)
            if location:
                return location
        return infer_location_from_contributions(contributions, self.settings.default_country)

    def _resolve_spam_score(
        self,
        profile: CallerProfileRecord | None,
        reports: list[SpamReportRecord],
    ) -> int:
        base_score = profile.spam_score if profile else 0
        weighted_reports = sum(SPAM_REASON_WEIGHTS[report.reason] for report in reports)
        report_pressure = min(weighted_reports // 2, 70)
        score = min(100, max(base_score, report_pressure))
        if profile and profile.verified:
            score = max(0, score - 4)
        return score

    def _resolve_caller_type(self, profile: CallerProfileRecord | None, name: str) -> str:
        if profile:
            return "business" if profile.is_business else "individual"
        return "business" if _looks_like_business(name) else "unknown"

    def _resolve_match_strategy(
        self,
        profile: CallerProfileRecord | None,
        name_votes: int,
    ) -> str:
        if profile and profile.verified:
            return "verified_profile"
        if profile:
            return "known_profile"
        if name_votes >= 1:
            return "crowd_consensus"
        return "unknown"

    def _resolve_confidence(
        self,
        profile: CallerProfileRecord | None,
        name_votes: int,
        contributions: list[ContactContributionRecord],
        reports: list[SpamReportRecord],
    ) -> int:
        if profile:
            base = max(profile.confidence_score, 45)
            if profile.verified:
                base += 10
        else:
            base = 18

        agreement_bonus = min(name_votes * 12, 28)
        location_bonus = 10 if any(item.source_state or item.source_city for item in contributions) else 0
        spam_penalty = min(len(reports) * 2, 12)
        confidence = max(8, min(98, base + agreement_bonus + location_bonus - spam_penalty))
        return confidence

    def _resolve_sources(
        self,
        profile: CallerProfileRecord | None,
        name_votes: int,
        contributions: list[ContactContributionRecord],
        reports: list[SpamReportRecord],
        location: str,
    ) -> list[SourceSignal]:
        sources: list[SourceSignal] = []
        if profile:
            sources.append(
                SourceSignal(
                    source="profile",
                    weight=45 if profile.verified else 32,
                    label="Curated caller profile",
                )
            )
        if contributions:
            sources.append(
                SourceSignal(
                    source="crowd_contact",
                    weight=min(35, name_votes * 10),
                    label=f"{len(contributions)} contributed contact reference(s)",
                )
            )
        if reports:
            sources.append(
                SourceSignal(
                    source="spam_reports",
                    weight=min(30, len(reports) * 8),
                    label=f"{len(reports)} spam report(s)",
                )
            )
        if location != self.settings.default_country:
            sources.append(
                SourceSignal(
                    source="location_hint",
                    weight=12,
                    label="Regional hint from profile or contributor metadata",
                )
            )
        return sources


def _canonical_name(value: str) -> str:
    cleaned = " ".join(value.split())
    return cleaned.title()


def _count_matching_names(
    target_name: str,
    contributions: list[ContactContributionRecord],
) -> int:
    canonical_target = _canonical_name(target_name)
    return sum(1 for item in contributions if _canonical_name(item.contact_name) == canonical_target)


def _looks_like_business(name: str) -> bool:
    name_tokens = {token.casefold() for token in name.replace(",", " ").split()}
    return any(keyword in name_tokens for keyword in BUSINESS_KEYWORDS)
