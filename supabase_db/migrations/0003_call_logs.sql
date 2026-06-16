create table if not exists public.call_logs (
    id uuid primary key,
    caller_number text not null,
    callee_identifier text,
    resolved_name text not null,
    created_at timestamptz not null default now()
);

create index if not exists call_logs_created_at_idx on public.call_logs(created_at desc);
