-- Announcements center (admin publishes, all entities read).
-- Run once in the SQL Editor. Safe to re-run. No data is deleted.

create table if not exists public.announcements (
  id         uuid primary key default gen_random_uuid(),
  text       text not null check (char_length(text) between 3 and 400),
  level      text not null default 'info' check (level in ('info','warn')),
  active     boolean not null default true,
  ends_on    date,
  created_at timestamptz not null default now()
);

alter table public.announcements enable row level security;

drop policy if exists ann_select on public.announcements;
drop policy if exists ann_admin  on public.announcements;

create policy ann_select on public.announcements for select to authenticated
  using (public.my_role() is not null);

create policy ann_admin on public.announcements for all to authenticated
  using (public.my_role() = 'admin') with check (public.my_role() = 'admin');

grant select, insert, update, delete on public.announcements to authenticated;
