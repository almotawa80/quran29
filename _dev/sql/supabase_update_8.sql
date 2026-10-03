-- update 8: «هل أفادتك الإجابة؟» under the assistant's answers.
-- Lets the anonymous counter accept two new kinds: fbup / fbdn, keyed by the question topic only (no text, no identifier).
-- Run once in Supabase → SQL Editor. Safe to re-run.

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
    when 'fbup'    then v in ('prizes','register','rules','branches','dates','entities','shields','results','contact','other')
    when 'fbdn'    then v in ('prizes','register','rules','branches','dates','entities','shields','results','contact','other')
    else false
  end;
$$;
revoke all on function public.q29_label_ok(text, text) from public, anon, authenticated;
