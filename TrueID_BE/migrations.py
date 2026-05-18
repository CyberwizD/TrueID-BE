from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from TrueID_BE.config import Settings


@dataclass(frozen=True, slots=True)
class MigrationFile:
    version: str
    path: Path


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "supabase" / "migrations"


def ensure_schema(settings: Settings) -> None:
    if settings.resolved_backend != "supabase" or not settings.auto_migrate:
        return

    database_url = settings.migration_database_url
    if not database_url:
        return

    from psycopg import connect

    migration_files = _discover_migrations()
    if not migration_files:
        return

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                create table if not exists schema_migrations (
                    version text primary key,
                    applied_at timestamptz not null default now()
                )
                """
            )
            cursor.execute("select version from schema_migrations")
            applied_versions = {row[0] for row in cursor.fetchall()}

            for migration in migration_files:
                if migration.version in applied_versions:
                    continue
                cursor.execute(migration.path.read_text(encoding="utf-8"))
                cursor.execute(
                    "insert into schema_migrations (version) values (%s)",
                    (migration.version,),
                )
        connection.commit()
def _discover_migrations() -> list[MigrationFile]:
    if not MIGRATIONS_DIR.exists():
        return []

    migration_files: list[MigrationFile] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = path.stem.split("_", 1)[0]
        migration_files.append(MigrationFile(version=version, path=path))
    return migration_files
