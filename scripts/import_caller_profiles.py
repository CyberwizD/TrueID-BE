from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from TrueID_BE.api import get_identity_service
from TrueID_BE.schemas import CuratedCallerProfileInput


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_caller_profiles.py <file.csv|file.json>")
        return 1

    source_path = Path(sys.argv[1]).expanduser().resolve()
    if not source_path.exists():
        print(f"File not found: {source_path}")
        return 1

    profiles = load_profiles(source_path)
    response = get_identity_service().import_caller_profiles(profiles)
    print(json.dumps(response.model_dump(mode="json"), indent=2))
    return 0


def load_profiles(source_path: Path) -> list[CuratedCallerProfileInput]:
    if source_path.suffix.casefold() == ".json":
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        rows = payload.get("profiles", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("JSON file must contain a list or an object with a 'profiles' list.")
        return [CuratedCallerProfileInput.model_validate(row) for row in rows]

    if source_path.suffix.casefold() == ".csv":
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [CuratedCallerProfileInput.model_validate(row) for row in reader]

    raise ValueError("Unsupported file type. Use .csv or .json")


if __name__ == "__main__":
    raise SystemExit(main())
