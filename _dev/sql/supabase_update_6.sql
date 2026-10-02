-- Announcements: what happens after a visitor or an entity hides an announcement.
--   never  = it does not come back (default)
--   visits = it comes back on the next visits until it has been hidden hide_n times
--   days   = it comes back hide_n days after it was hidden
--   pin    = it cannot be hidden (no close button)
-- Run once in the Supabase SQL Editor AFTER supabase_update_5.sql. Safe to re-run. No data is deleted.

alter table public.announcements add column if not exists hide_mode text not null default 'never';
alter table public.announcements add column if not exists hide_n    smallint;

alter table public.announcements drop constraint if exists ann_hide_chk;
alter table public.announcements add  constraint ann_hide_chk check (
  (hide_mode in ('never','pin') and hide_n is null)
  or (hide_mode in ('visits','days') and hide_n between 1 and 30));

-- the visitor function now also returns the hide setting (return type changes, so drop first)
drop function if exists public.q29_public_ann();
create function public.q29_public_ann()
returns table(id uuid, text text, level text, link_url text, link_label text, created_at timestamptz, hide_mode text, hide_n smallint)
language sql stable security definer set search_path = public as $$
  select a.id, a.text, a.level, a.link_url, a.link_label, a.created_at, a.hide_mode, a.hide_n
  from public.announcements a
  where a.active
    and a.audience in ('public','all')
    and (a.starts_on is null or a.starts_on <= (now() at time zone 'Asia/Kuwait')::date)
    and (a.ends_on   is null or a.ends_on   >= (now() at time zone 'Asia/Kuwait')::date)
  order by (a.level = 'warn') desc, a.created_at desc
  limit 10;
$$;
revoke all on function public.q29_public_ann() from public;
grant execute on function public.q29_public_ann() to anon, authenticated;

-- version marker used by the admin page to know this update is installed
create or replace function public.q29_ann_v() returns integer
language sql immutable as $$ select 6 $$;
revoke all on function public.q29_ann_v() from public;
grant execute on function public.q29_ann_v() to authenticated;
