-- Passwords: coordinators and reviewers choose their own password.
--   * pw_set = false means the account still uses a password chosen by the admin,
--     so the portal asks the user to choose a new one at the next sign-in.
--   * When the admin sets a new password (reset), pw_set goes back to false.
-- Run once in the Supabase SQL Editor. Safe to re-run. No data is deleted.

alter table public.members add column if not exists pw_set boolean not null default false;

-- does the signed-in user still need to choose a password?
create or replace function public.q29_my_pw() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select m.pw_set or m.role = 'admin' from public.members m where m.user_id = auth.uid()), true);
$$;
revoke all on function public.q29_my_pw() from public, anon;
grant execute on function public.q29_my_pw() to authenticated;

-- the signed-in user changes their own password (the current password is required)
create or replace function public.q29_change_password(p_old text, p_new text)
returns void language plpgsql security definer set search_path = public, extensions, auth as $$
declare h text;
begin
  if auth.uid() is null then raise exception 'not_allowed'; end if;
  if length(coalesce(p_new, '')) < 8 then raise exception 'password_too_short'; end if;
  if p_new = p_old then raise exception 'password_same'; end if;
  select encrypted_password into h from auth.users where id = auth.uid();
  if h is null or h <> extensions.crypt(coalesce(p_old, ''), h) then raise exception 'wrong_password'; end if;
  update auth.users set encrypted_password = extensions.crypt(p_new, extensions.gen_salt('bf')), updated_at = now()
   where id = auth.uid();
  update public.members set pw_set = true where user_id = auth.uid();
end $$;
revoke all on function public.q29_change_password(text, text) from public, anon;
grant execute on function public.q29_change_password(text, text) to authenticated;

-- admin reset: same as before, and the user must choose a new password at the next sign-in
create or replace function public.admin_set_password(p_ent uuid, p_role text, p_password text)
returns void language plpgsql security definer set search_path = public, extensions, auth as $$
begin
  if public.my_role() is distinct from 'admin' then raise exception 'not_allowed'; end if;
  if length(coalesce(p_password, '')) < 6 then raise exception 'password_too_short'; end if;
  update auth.users set encrypted_password = extensions.crypt(p_password, extensions.gen_salt('bf')), updated_at = now()
   where id = (select user_id from public.members where ent_id = p_ent and role = p_role);
  if not found then raise exception 'account_not_found'; end if;
  update public.members set pw_set = false where ent_id = p_ent and role = p_role;
end $$;
revoke all on function public.admin_set_password(uuid, text, text) from public, anon;
grant execute on function public.admin_set_password(uuid, text, text) to authenticated;
