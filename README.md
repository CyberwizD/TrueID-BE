# TrueID Backend

TrueID Phase 1 backend provides privacy-safe caller identification APIs for:

- caller lookup
- spam reporting
- contact contribution ingestion

The MVP intentionally returns coarse location only, such as `Lekki, Lagos`. It does not expose exact residential addresses.
For Nigerian mobile numbers, the phone number alone is not a reliable source of city/state after number portability. Broad location should come from curated caller profiles or another verified enrichment source, not guessed from the digits.

## How caller identification works

1. Normalize the phone number into a Nigeria-friendly E.164 format.
2. Check whether the number already has a curated caller profile.
3. If not, aggregate crowdsourced contact contributions for a consensus display name.
4. Optionally verify the number against NCC TIRMS for telecom status and current mobile network.
5. Build a regional label from trusted profile metadata or fallback country data.
6. Combine profile trust, agreement count, telecom status, and spam history into a confidence score.

## Endpoints

- `GET /health`
- `POST /api/v1/lookup`
- `POST /api/v1/report-spam`
- `POST /api/v1/upload-contacts`
- `POST /api/v1/admin/import-caller-profiles`

## Local run

```bash
pip install -r requirements.txt
python main.py
```

## Environment

Create a `.env` file if you want Supabase instead of the built-in memory repository:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-secret-key
SUPABASE_DB_URL=postgresql://postgres:password@db.project-ref.supabase.co:5432/postgres
TRUEID_DATA_BACKEND=auto
TRUEID_AUTO_MIGRATE=true
TRUEID_ALLOWED_ORIGINS=http://localhost:8081,http://localhost:19006
TRUEID_PROFILE_IMPORT_TOKEN=replace-this-with-a-secret
TRUEID_TIRMS_API_KEY=optional-ncc-tirms-api-key
```

If Supabase credentials are missing, the API falls back to seeded memory data.

`sb_publishable_...` keys are public client keys and are not treated as backend admin credentials. Use `SUPABASE_SECRET_KEY` or a legacy `SUPABASE_SERVICE_ROLE_KEY` instead.

`SUPABASE_SECRET_KEY` is used for runtime reads and writes through the Supabase API.
`SUPABASE_DB_URL` or `DATABASE_URL` is used for schema migrations through direct Postgres access.

## Schema migrations

Schema creation and upgrades are tracked in `supabase/migrations/`.
On startup, the backend applies any unapplied migration automatically when:

- `TRUEID_DATA_BACKEND=supabase`
- `TRUEID_AUTO_MIGRATE=true`
- `SUPABASE_DB_URL` or `DATABASE_URL` is configured

No demo seed data is applied automatically.

## Curated profile enrichment

Use curated caller profiles to enrich lookup results with trusted business names and broad locations.

HTTP import endpoint:

- `POST /api/v1/admin/import-caller-profiles`
- header: `X-Admin-Token: <TRUEID_PROFILE_IMPORT_TOKEN>`

Example request:

```json
{
  "profiles": [
    {
      "phone_number": "+2348035550000",
      "display_name": "Prime Dental Clinic",
      "city": "Lekki",
      "state": "Lagos",
      "verified": true,
      "is_business": true,
      "confidence_score": 88,
      "network": "MTN",
      "number_status": "NORMAL",
      "source_provider": "trusted_partner"
    }
  ]
}
```

Local import script:

```bash
python scripts/import_caller_profiles.py profiles.csv
```

CSV columns supported:

- `phone_number`
- `display_name`
- `city`
- `state`
- `country`
- `spam_score`
- `confidence_score`
- `is_business`
- `verified`
- `network`
- `number_status`
- `source_provider`
- `source_reference`

## NCC TIRMS enrichment

If `TRUEID_TIRMS_API_KEY` is configured, lookup can also attach official NCC TIRMS verification signals such as:

- current telecom status (`NORMAL`, `SWAPPED`, `CHURNED`, `REASSIGNED`, `BLACKLISTED`)
- current mobile network

TIRMS is useful for risk and network verification, but it does not provide city/state. Use it alongside curated caller profiles rather than instead of them.

## Reflex cloud

Reflex cloud now installs from `requirements.txt`, which avoids local package build discovery errors during deployment.

Reflex Cloud or Fly will not read your local `.env` automatically unless you pass it during deploy or set the values in the hosted app's secrets/settings UI.
