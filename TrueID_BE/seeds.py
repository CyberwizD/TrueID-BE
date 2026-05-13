from TrueID_BE.schemas import CallerProfileRecord, ContactContributionRecord, SpamReportRecord


SEED_PROFILES = [
    CallerProfileRecord(
        phone_number="+2348030001111",
        display_name="Kora Logistics",
        city="Victoria Island",
        state="Lagos",
        spam_score=18,
        confidence_score=88,
        is_business=True,
        verified=True,
    ),
    CallerProfileRecord(
        phone_number="+2348091234567",
        display_name="Chiamaka Okafor",
        city="Gwarinpa",
        state="FCT",
        spam_score=4,
        confidence_score=74,
    ),
    CallerProfileRecord(
        phone_number="+2347011112222",
        display_name="QuickCash Loans",
        city="Ikeja",
        state="Lagos",
        spam_score=72,
        confidence_score=79,
        is_business=True,
    ),
]

SEED_CONTRIBUTIONS = [
    ContactContributionRecord(
        user_id="user_ada",
        phone_number="+2348091234567",
        contact_name="Chiamaka Okafor",
        source_city="Gwarinpa",
        source_state="FCT",
    ),
    ContactContributionRecord(
        user_id="user_emeka",
        phone_number="+2348091234567",
        contact_name="Chiamaka",
        source_city="Abuja",
        source_state="FCT",
    ),
    ContactContributionRecord(
        user_id="user_bisi",
        phone_number="+2348112223334",
        contact_name="Dr Tolu Dental",
        source_city="Yaba",
        source_state="Lagos",
    ),
    ContactContributionRecord(
        user_id="user_ife",
        phone_number="+2348112223334",
        contact_name="Tolu Dental Clinic",
        source_city="Sabo",
        source_state="Lagos",
    ),
]

SEED_REPORTS = [
    SpamReportRecord(
        phone_number="+2347011112222",
        reason="loan_spam",
        reporter_id="user_uche",
        notes="Aggressive repeat loan calls",
    ),
    SpamReportRecord(
        phone_number="+2347011112222",
        reason="telemarketing",
        reporter_id="user_sarah",
    ),
]
