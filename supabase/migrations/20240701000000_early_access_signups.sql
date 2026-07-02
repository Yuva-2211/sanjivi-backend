-- Migration: early_access_signups
-- Run this in your Supabase SQL editor or via `supabase db push`.

create table if not exists public.early_access_signups (
  id          uuid primary key default gen_random_uuid(),
  name        text        not null,
  email       text        not null,
  created_at  timestamptz not null default now()
);

-- Prevent duplicate email submissions
create unique index if not exists early_access_signups_email_idx
  on public.early_access_signups (lower(email));

-- (Optional) Restrict direct browser access — service role key bypasses this
alter table public.early_access_signups enable row level security;

-- Allow inserts from the service role only (no anon/public writes needed)
-- The Next.js API route uses the service role key, so no additional policy is required.
