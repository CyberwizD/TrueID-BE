# TrueID Backend

TrueID Phase 1 backend provides privacy-safe caller identification APIs for:

- caller lookup
- spam reporting
- contact contribution ingestion

The MVP intentionally returns coarse location only, such as `Lekki, Lagos`. It does not expose exact residential addresses.

## How caller identification works

1. Normalize the phone number into a Nigeria-friendly E.164 format.
2. Check whether the number already has a curated caller profile.
3. If not, aggregate crowdsourced contact contributions for a consensus display name.
4. Build a regional label from stored city/state metadata or fallback country data.
5. Combine profile trust, agreement count, and spam history into a confidence score.

## Endpoints

- `GET /health`
- `POST /api/v1/lookup`
- `POST /api/v1/report-spam`
- `POST /api/v1/upload-contacts`

## Local run

```bash
pip install -r requirements.txt
python main.py
```

## Environment

Create a `.env` file if you want Supabase instead of the built-in memory repository:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
TRUEID_DATA_BACKEND=auto
TRUEID_ALLOWED_ORIGINS=http://localhost:8081,http://localhost:19006
```

If Supabase credentials are missing, the API falls back to seeded memory data.

## Reflex cloud

Reflex cloud now installs from `requirements.txt`, which avoids local package build discovery errors during deployment.
