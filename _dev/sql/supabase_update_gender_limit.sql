-- =====================================================================
--  تحديث: حد الشريحة 5 ذكور و5 إناث (بدلاً من 5 متسابقين مجتمعين)
--  شغّله مرة واحدة في SQL Editor. لا يمسح أي بيانات.
-- =====================================================================

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
