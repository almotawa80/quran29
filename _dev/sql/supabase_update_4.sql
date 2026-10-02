-- Usage statistics for the guide (anonymous aggregate counters only).
-- No IP address, no identifier, no free text is stored. Only fixed labels are accepted.
-- Run once in Supabase SQL editor. Safe to run again.

create table if not exists public.stat_counts (
  day  date    not null,
  kind text    not null,
  key  text    not null,
  n    integer not null default 0,
  primary key (day, kind, key)
);
alter table public.stat_counts enable row level security;
revoke all on public.stat_counts from anon, authenticated;

-- Fixed list of accepted labels per kind (keeps the table small and blocks junk input)
create or replace function public.q29_label_ok(k text, v text) returns boolean
language sql immutable as $$
  select case k
    when 'device'  then v in ('mobile','tablet','desktop')
    when 'os'      then v in ('ios','android','windows','mac','linux','other')
    when 'browser' then v in ('chrome','safari','edge','firefox','samsung','opera','inapp','other')
    when 'src'     then v in ('whatsapp','instagram','twitter','facebook','telegram','snapchat','tiktok','search','share','quiz','direct','other')
    when 'ret'     then v in ('new','ret')
    when 'hour'    then v ~ '^([0-9]|1[0-9]|2[0-3])$'
    when 'sec'     then v in ('home','branches','ai','shields','more','game_start','game_done','share_open','share_img')
    when 'ask'     then v in ('prizes','register','rules','branches','dates','entities','shields','results','contact','other')
    else false
  end;
$$;

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
