alter table caller_profiles
    add column if not exists network text,
    add column if not exists number_status text,
    add column if not exists source_provider text,
    add column if not exists source_reference text,
    add column if not exists last_verified_at timestamptz;

create index if not exists caller_profiles_source_provider_idx
    on caller_profiles(source_provider);
