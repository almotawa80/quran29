-- =====================================================================
--  بوابة الجهات المشاركة — مسابقة الكويت الكبرى (29)
--  إعداد قاعدة البيانات (Supabase) — نسخة التجربة
--  شغّل هذا الملف مرة واحدة كاملاً من: SQL Editor ← New query ← Run
--  قبل التشغيل: غيّر كلمة مرور المشرف في آخر سطر من الملف.
-- =====================================================================

create extension if not exists pgcrypto with schema extensions;

-- ---------- الجداول ----------
create table if not exists public.entities (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  type         text not null default '',
  coord        text not null default '',
  phone        text not null default '',
  email        text not null default '',
  username     text not null unique,
  active       boolean not null default true,
  rev_name     text not null default '',
  rev_phone    text not null default '',
  rev_username text unique,
  created_at   timestamptz not null default now()
);

create table if not exists public.members (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role    text not null check (role in ('admin','entry','reviewer')),
  ent_id  uuid references public.entities(id) on delete cascade,
  check ((role = 'admin') = (ent_id is null))
);
create unique index if not exists members_ent_role on public.members(ent_id, role) where ent_id is not null;

create table if not exists public.candidates (
  id          uuid primary key default gen_random_uuid(),
  ent_id      uuid not null references public.entities(id) on delete cascade,
  cid         text not null unique,
  status      text not null default 'draft' check (status in ('draft','pending','approved','corrected','cancelled')),
  review_note text not null default '',
  data        jsonb not null default '{}'::jsonb,
  docs        jsonb not null default '{}'::jsonb,
  log         jsonb not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);
create index if not exists candidates_ent on public.candidates(ent_id);
-- حالة «ملغى» (للقواعد المنشأة قبل إضافتها)
alter table public.candidates drop constraint if exists candidates_status_check;
alter table public.candidates add constraint candidates_status_check
  check (status in ('draft','pending','approved','corrected','cancelled'));

-- ---------- من المستخدم الحالي؟ ----------
create or replace function public.my_role() returns text
language sql stable security definer set search_path = public as $$
  select m.role from public.members m left join public.entities e on e.id = m.ent_id
  where m.user_id = auth.uid() and (m.role = 'admin' or e.active)
$$;

create or replace function public.my_ent() returns uuid
language sql stable security definer set search_path = public as $$
  select m.ent_id from public.members m join public.entities e on e.id = m.ent_id
  where m.user_id = auth.uid() and e.active
$$;

-- ---------- الصلاحيات على مستوى الصف ----------
alter table public.entities   enable row level security;
alter table public.members    enable row level security;
alter table public.candidates enable row level security;

revoke all on public.entities, public.members, public.candidates from anon;
grant select, insert, update, delete on public.entities, public.members, public.candidates to authenticated;

drop policy if exists ent_select on public.entities;
drop policy if exists ent_admin  on public.entities;
create policy ent_select on public.entities for select to authenticated
  using (public.my_role() = 'admin' or id = public.my_ent());
create policy ent_admin on public.entities for all to authenticated
  using (public.my_role() = 'admin') with check (public.my_role() = 'admin');

drop policy if exists mem_select on public.members;
drop policy if exists mem_admin  on public.members;
create policy mem_select on public.members for select to authenticated
  using (user_id = auth.uid() or public.my_role() = 'admin');
create policy mem_admin on public.members for all to authenticated
  using (public.my_role() = 'admin') with check (public.my_role() = 'admin');

drop policy if exists cand_select on public.candidates;
drop policy if exists cand_insert on public.candidates;
drop policy if exists cand_update on public.candidates;
drop policy if exists cand_delete on public.candidates;
create policy cand_select on public.candidates for select to authenticated
  using (public.my_role() = 'admin' or ent_id = public.my_ent());
create policy cand_insert on public.candidates for insert to authenticated
  with check (public.my_role() = 'entry' and ent_id = public.my_ent());
create policy cand_update on public.candidates for update to authenticated
  using (public.my_role() = 'admin' or ent_id = public.my_ent())
  with check (public.my_role() = 'admin' or ent_id = public.my_ent());
create policy cand_delete on public.candidates for delete to authenticated
  using (public.my_role() = 'admin' or (public.my_role() = 'entry' and ent_id = public.my_ent() and status in ('draft','cancelled')));

-- ---------- قواعد العمل على الخادم (لا يمكن تجاوزها من المتصفح) ----------
create or replace function public.cand_guard() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  r text := public.my_role();
  has_rev boolean;
  n int;
begin
  if r is null then raise exception 'not_allowed'; end if;
  if r <> 'admin' then
    if new.ent_id is distinct from public.my_ent() then raise exception 'not_allowed'; end if;
    select coalesce(rev_username, '') <> '' into has_rev from public.entities where id = new.ent_id;
    -- الترشيح الملغى: لا يُعدَّل، ويُرجَع كمسودة فقط
    if tg_op = 'INSERT' and new.status = 'cancelled' then raise exception 'bad_status'; end if;
    if tg_op = 'UPDATE' and old.status = 'cancelled' then
      if r = 'reviewer' or new.status not in ('cancelled','draft')
         or new.data is distinct from old.data or new.docs is distinct from old.docs then
        raise exception 'bad_status';
      end if;
    end if;
    if r = 'reviewer' then
      if tg_op = 'INSERT' or new.data is distinct from old.data or new.docs is distinct from old.docs
         or new.cid is distinct from old.cid then
        raise exception 'reviewer_cannot_edit';
      end if;
      if new.status not in ('pending','approved','corrected') then raise exception 'bad_status'; end if;
    else -- entry
      if has_rev and new.status = 'approved' and (tg_op = 'INSERT' or old.status <> 'approved'
         or new.data is distinct from old.data or new.docs is distinct from old.docs) then
        raise exception 'reviewer_must_approve';
      end if;
      if new.status = 'corrected' and (tg_op = 'INSERT' or old.status <> 'corrected') then
        raise exception 'bad_status';
      end if;
    end if;
  end if;
  -- حد الشريحة: 5 ذكور و5 إناث معتمدين لكل جهة في كل شريحة
  if new.status = 'approved' and (tg_op = 'INSERT' or old.status <> 'approved'
     or new.data->>'br' is distinct from old.data->>'br' or new.data->>'sl' is distinct from old.data->>'sl'
     or new.data->>'gender' is distinct from old.data->>'gender') then
    select count(*) into n from public.candidates
     where ent_id = new.ent_id and status = 'approved' and id <> new.id
       and data->>'br' = new.data->>'br' and data->>'sl' = new.data->>'sl'
       and data->>'gender' is not distinct from new.data->>'gender';
    if n >= 5 then raise exception 'slice_full'; end if;
  end if;
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists cand_guard on public.candidates;
create trigger cand_guard before insert or update on public.candidates
  for each row execute function public.cand_guard();

-- ---------- الحسابات (ينشئها المشرف فقط؛ لا تسجيل ذاتي) ----------
create or replace function public._q29_email(p_username text) returns text
language sql immutable as $$ select lower(trim(p_username)) || '@quran29.local' $$;

create or replace function public._create_account(p_username text, p_password text) returns uuid
language plpgsql security definer set search_path = public, extensions, auth as $$
declare uid uuid := gen_random_uuid(); em text := public._q29_email(p_username);
begin
  if length(coalesce(p_password, '')) < 6 then raise exception 'password_too_short'; end if;
  if exists (select 1 from auth.users where email = em) then raise exception 'username_taken'; end if;
  insert into auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
      raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
      confirmation_token, recovery_token, email_change_token_new, email_change,
      email_change_token_current, phone_change, phone_change_token, reauthentication_token)
  values ('00000000-0000-0000-0000-000000000000', uid, 'authenticated', 'authenticated', em,
      extensions.crypt(p_password, extensions.gen_salt('bf')), now(),
      '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb, now(), now(),
      '', '', '', '', '', '', '', '');
  insert into auth.identities (id, provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at)
  values (gen_random_uuid(), uid::text, uid,
      jsonb_build_object('sub', uid::text, 'email', em, 'email_verified', true), 'email', now(), now(), now());
  return uid;
end $$;
revoke all on function public._create_account(text, text) from public, anon, authenticated;

create or replace function public.admin_create_account(p_ent uuid, p_role text, p_username text, p_password text)
returns void language plpgsql security definer set search_path = public, extensions, auth as $$
declare uid uuid;
begin
  if public.my_role() is distinct from 'admin' then raise exception 'not_allowed'; end if;
  if p_role not in ('entry','reviewer') then raise exception 'bad_role'; end if;
  delete from auth.users where id = (select user_id from public.members where ent_id = p_ent and role = p_role);
  uid := public._create_account(p_username, p_password);
  insert into public.members (user_id, role, ent_id) values (uid, p_role, p_ent);
end $$;

create or replace function public.admin_set_password(p_ent uuid, p_role text, p_password text)
returns void language plpgsql security definer set search_path = public, extensions, auth as $$
begin
  if public.my_role() is distinct from 'admin' then raise exception 'not_allowed'; end if;
  if length(coalesce(p_password, '')) < 6 then raise exception 'password_too_short'; end if;
  update auth.users set encrypted_password = extensions.crypt(p_password, extensions.gen_salt('bf')), updated_at = now()
   where id = (select user_id from public.members where ent_id = p_ent and role = p_role);
  if not found then raise exception 'account_not_found'; end if;
end $$;

create or replace function public.admin_remove_account(p_ent uuid, p_role text)
returns void language plpgsql security definer set search_path = public, auth as $$
begin
  if public.my_role() is distinct from 'admin' then raise exception 'not_allowed'; end if;
  delete from auth.users where id = (select user_id from public.members where ent_id = p_ent and role = p_role);
end $$;

revoke all on function public.admin_create_account(uuid, text, text, text) from public, anon;
revoke all on function public.admin_set_password(uuid, text, text) from public, anon;
revoke all on function public.admin_remove_account(uuid, text) from public, anon;
grant execute on function public.admin_create_account(uuid, text, text, text) to authenticated;
grant execute on function public.admin_set_password(uuid, text, text) to authenticated;
grant execute on function public.admin_remove_account(uuid, text) to authenticated;

-- ---------- تخزين المستندات (خاص، لكل جهة مجلدها) ----------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('docs', 'docs', false, 8388608, array['image/jpeg','image/png','image/webp','application/pdf'])
on conflict (id) do update set public = false, file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists q29_docs_select on storage.objects;
drop policy if exists q29_docs_insert on storage.objects;
drop policy if exists q29_docs_delete on storage.objects;
create policy q29_docs_select on storage.objects for select to authenticated
  using (bucket_id = 'docs' and (public.my_role() = 'admin' or (storage.foldername(name))[1] = public.my_ent()::text));
create policy q29_docs_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'docs' and public.my_role() = 'entry' and (storage.foldername(name))[1] = public.my_ent()::text);
create policy q29_docs_delete on storage.objects for delete to authenticated
  using (bucket_id = 'docs' and (public.my_role() = 'admin'
         or (public.my_role() = 'entry' and (storage.foldername(name))[1] = public.my_ent()::text)));

-- ---------- عدّاد زيارات الدليل (بلا أي بيانات شخصية) ----------
create table if not exists public.page_views (
  day date primary key,
  n   integer not null default 0
);
alter table public.page_views enable row level security;
revoke all on public.page_views from anon, authenticated;

create or replace function public.q29_hit() returns void
language sql security definer set search_path = public as $$
  insert into public.page_views(day, n) values ((now() at time zone 'Asia/Kuwait')::date, 1)
  on conflict (day) do update set n = public.page_views.n + 1;
$$;
revoke all on function public.q29_hit() from public;
grant execute on function public.q29_hit() to anon, authenticated;

create or replace function public.q29_views() returns table(day date, n integer)
language sql stable security definer set search_path = public as $$
  select v.day, v.n from public.page_views v where public.my_role() = 'admin' order by v.day;
$$;
revoke all on function public.q29_views() from public, anon;
grant execute on function public.q29_views() to authenticated;

-- ---------- حساب المشرف ----------
-- اسم المستخدم: admin — غيّر كلمة المرور أدناه (6 أحرف على الأقل) قبل التشغيل:
do $$
declare uid uuid;
begin
  if not exists (select 1 from auth.users where email = public._q29_email('admin')) then
    uid := public._create_account('admin', 'CHANGE-THIS-PASSWORD');
    insert into public.members (user_id, role) values (uid, 'admin');
  end if;
end $$;
