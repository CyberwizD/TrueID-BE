create extension if not exists pgcrypto;

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    phone_number text unique not null,
    email text unique,
    created_at timestamptz not null default now()
);

create table if not exists caller_profiles (
    id uuid primary key default gen_random_uuid(),
    phone_number text unique not null,
    display_name text not null,
    city text,
    state text,
    country text not null default 'Nigeria',
    spam_score integer not null default 0 check (spam_score between 0 and 100),
    confidence_score integer not null default 0 check (confidence_score between 0 and 100),
    is_business boolean not null default false,
    verified boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists contact_contributions (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    phone_number text not null,
    contact_name text not null,
    source_city text,
    source_state text,
    created_at timestamptz not null default now()
);

create unique index if not exists contact_contributions_user_phone_name_idx
    on contact_contributions(user_id, phone_number, lower(contact_name));

create table if not exists spam_reports (
    id uuid primary key default gen_random_uuid(),
    reporter_id text,
    phone_number text not null,
    reason text not null,
    notes text,
    created_at timestamptz not null default now()
);

create index if not exists caller_profiles_phone_idx on caller_profiles(phone_number);
create index if not exists contact_contributions_phone_idx on contact_contributions(phone_number);
create index if not exists spam_reports_phone_idx on spam_reports(phone_number);
