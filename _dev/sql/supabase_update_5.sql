-- Announcements by audience: entities only, visitors only, or everyone.
-- Adds: audience, optional link button, optional start date, and a group id
-- (one news item with a different text for visitors and for entities).
-- Run once in the Supabase SQL Editor AFTER supabase_update_3.sql. Safe to re-run. No data is deleted.
-- Existing announcements stay "entities only".

alter table public.announcements add column if not exists audience   text not null default 'ents';
alter table public.announcements add column if not exists starts_on  date;
alter table public.announcements add column if not exists link_url   text;
alter table public.announcements add column if not exists link_label text;
alter table public.announcements add column if not exists grp        uuid;

alter table public.announcements drop constraint if exists ann_audience_chk;
alter table public.announcements add  constraint ann_audience_chk check (audience in ('ents','public','all'));
alter table public.announcements drop constraint if exists ann_link_chk;
alter table public.announcements add  constraint ann_link_chk check (
  link_url is null or (char_length(link_url) <= 300 and link_url ~ '^https://[^[:space:]<>"'']+$'));
alter table public.announcements drop constraint if exists ann_label_chk;
alter table public.announcements add  constraint ann_label_chk check (link_label is null or char_length(link_label) between 1 and 30);
alter table public.announcements drop constraint if exists ann_dates_chk;
alter table public.announcements add  constraint ann_dates_chk check (starts_on is null or ends_on is null or ends_on >= starts_on);

-- Entities see only announcements meant for entities or everyone, and only from the start date.
drop policy if exists ann_select on public.announcements;
create policy ann_select on public.announcements for select to authenticated
  using (
    public.my_role() = 'admin'
    or (public.my_role() is not null
        and audience in ('ents','all')
        and (starts_on is null or starts_on <= (now() at time zone 'Asia/Kuwait')::date))
  );

-- Visitors of the guide (not signed in): only live announcements meant for visitors or everyone.
-- Returns only display fields. The table itself stays closed to anonymous users.
create or replace function public.q29_public_ann()
returns table(id uuid, text text, level text, link_url text, link_label text, created_at timestamptz)
language sql stable security definer set search_path = public as $$
  select a.id, a.text, a.level, a.link_url, a.link_label, a.created_at
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

-- Statistics: count how many times a visitor announcement was shown (annv) and its link clicked (annc).
-- Same anonymous counters table as supabase_update_4.sql (created here too if missing).
create table if not exists public.stat_counts (
  day  date    not null,
  kind text    not null,
  key  text    not null,
  n    integer not null default 0,
  primary key (day, kind, key)
);
alter table public.stat_counts enable row level security;
revoke all on public.stat_counts from anon, authenticated;

create or replace function public.q29_label_ok(k text, v text) returns boolean
language sql stable security definer set search_path = public as $$
  select case k
    when 'device'  then v in ('mobile','tablet','desktop')
    when 'os'      then v in ('ios','android','windows','mac','linux','other')
    when 'browser' then v in ('chrome','safari','edge','firefox','samsung','opera','inapp','other')
    when 'src'     then v in ('whatsapp','instagram','twitter','facebook','telegram','snapchat','tiktok','search','share','quiz','direct','other')
    when 'ret'     then v in ('new','ret')
    when 'hour'    then v ~ '^([0-9]|1[0-9]|2[0-3])$'
    when 'sec'     then v in ('home','branches','ai','shields','more','game_start','game_done','share_open','share_img')
    when 'ask'     then v in ('prizes','register','rules','branches','dates','entities','shields','results','contact','other')
    when 'annv'    then case when v ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                         then exists (select 1 from public.announcements a where a.id = v::uuid and a.audience in ('public','all'))
                         else false end
    when 'annc'    then case when v ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                         then exists (select 1 from public.announcements a where a.id = v::uuid and a.audience in ('public','all') and a.link_url is not null)
                         else false end
    else false
  end;
$$;
revoke all on function public.q29_label_ok(text, text) from public, anon, authenticated;

create or replace function public.q29_track(items jsonb) returns void
language plpgsql security definer set search_path = public as $$
declare
  it jsonb; k text; v text; c int := 0;
  d date := (now() at time zone 'Asia/Kuwait')::date;
begin
  if jsonb_typeof(items) is distinct from 'array' then return; end if;
  for it in select * from jsonb_array_elements(items) loop
    c := c + 1;
    exit when c > 20;
    k := it->>'k'; v := it->>'v';
    if k is not null and v is not null and public.q29_label_ok(k, v) then
      insert into public.stat_counts(day, kind, key, n) values (d, k, v, 1)
      on conflict (day, kind, key) do update set n = public.stat_counts.n + 1;
    end if;
  end loop;
end $$;
revoke all on function public.q29_track(jsonb) from public;
grant execute on function public.q29_track(jsonb) to anon, authenticated;

create or replace function public.q29_stats(p_days integer default 30)
returns table(day date, kind text, key text, n integer)
language sql stable security definer set search_path = public as $$
  select s.day, s.kind, s.key, s.n
  from public.stat_counts s
  where public.my_role() = 'admin'
    and s.day >= (now() at time zone 'Asia/Kuwait')::date - greatest(1, least(coalesce(p_days, 30), 365))
  order by s.day, s.kind, s.key;
$$;
revoke all on function public.q29_stats(integer) from public, anon;
grant execute on function public.q29_stats(integer) to authenticated;
