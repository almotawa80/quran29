-- =====================================================================
--  تحديث: حالة «ملغى» للمرشح، وعدّاد زيارات الدليل
--  شغّله مرة واحدة في SQL Editor. لا يمسح أي بيانات، ويمكن تشغيله أكثر من مرة.
--  يتضمن أيضاً حد الشريحة 5 ذكور و5 إناث.
-- =====================================================================

alter table public.candidates drop constraint if exists candidates_status_check;
alter table public.candidates add constraint candidates_status_check
  check (status in ('draft','pending','approved','corrected','cancelled'));

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

-- المنسق يحذف المسودات والترشيحات الملغاة فقط، والمشرف يحذف أي مرشح
drop policy if exists cand_delete on public.candidates;
create policy cand_delete on public.candidates for delete to authenticated
  using (public.my_role() = 'admin' or (public.my_role() = 'entry' and ent_id = public.my_ent() and status in ('draft','cancelled')));

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
