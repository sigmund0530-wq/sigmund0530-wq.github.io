-- ═══════════════════════════════════════════════════════════════════
-- 계정 설정 추가 (2026-10-28) — 이미 쓰고 있는 데이터베이스에 덧붙이는 SQL
-- 기존 글·사람은 지우지 않아요. 여러 번 실행해도 괜찮아요.
--  · 공간 주소(@) 바꾸기: 한 사람에 한 번. 예전 주소는 30일 동안 아무도 못 씀 (사칭 방지)
--  · 탈퇴: 내 공간·글·사진 기록·계정을 지우고, 주소는 30일 동안 묶어 둠
-- ═══════════════════════════════════════════════════════════════════
create table if not exists public.released_handles (
  handle text primary key,
  until  timestamptz not null
);
alter table public.released_handles enable row level security;   -- 정책 없음: 아무도 직접 못 읽음

alter table public.profiles add column if not exists handle_changed_at timestamptz;

create or replace function public.handle_available(p_handle text) returns boolean
language sql stable security definer set search_path = public as $$
  select p_handle ~ '^[a-z0-9](?:[a-z0-9-]{1,18}[a-z0-9])$'
     and p_handle not in ('admin','mugadang','help','settings','feed','login','api','www')
     and not exists (select 1 from profiles where handle = p_handle)
     and not exists (select 1 from released_handles where handle = p_handle and until > now()) $$;

-- 주소는 change_handle 로만 바꿀 수 있게 (화면에서 직접 고쳐 보내도 막힘)
create or replace function public.guard_handle() returns trigger
language plpgsql set search_path = public as $$
begin
  if (new.handle is distinct from old.handle or new.handle_changed_at is distinct from old.handle_changed_at)
     and coalesce(current_setting('mgd.allow_handle', true), '') <> 'on' then
    raise exception 'handle_change_via_function';
  end if;
  return new;
end $$;
drop trigger if exists profiles_guard_handle on public.profiles;
create trigger profiles_guard_handle before update on public.profiles
  for each row execute function public.guard_handle();

create or replace function public.change_handle(p_handle text) returns text
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); old text; changed timestamptz;
begin
  if uid is null then raise exception 'not_signed_in'; end if;
  select handle, handle_changed_at into old, changed from profiles where id = uid;
  if old is null then raise exception 'no_profile'; end if;
  if p_handle = old then return 'same'; end if;
  if changed is not null then raise exception 'handle_changed_once'; end if;
  if not handle_available(p_handle) then raise exception 'handle_unavailable'; end if;
  perform set_config('mgd.allow_handle', 'on', true);
  update profiles set handle = p_handle, handle_changed_at = now() where id = uid;
  perform set_config('mgd.allow_handle', '', true);
  insert into released_handles values (old, now() + interval '30 days')
    on conflict (handle) do update set until = excluded.until;
  return 'ok';
end $$;

-- 탈퇴: 사진 파일은 앱이 먼저 지우고 이 함수를 부름
create or replace function public.delete_my_account() returns text
language plpgsql security definer set search_path = public, auth as $$
declare uid uuid := auth.uid(); h text;
begin
  if uid is null then raise exception 'not_signed_in'; end if;
  select handle into h from public.profiles where id = uid;
  if h is not null then
    insert into public.released_handles values (h, now() + interval '30 days')
      on conflict (handle) do update set until = excluded.until;
  end if;
  delete from public.profiles where id = uid;     -- 글·카테고리·방·파일 기록·이웃·의견이 함께 지워짐
  delete from auth.users where id = uid;          -- 로그인 계정
  return 'ok';
end $$;

revoke execute on function public.change_handle(text) from public, anon;
revoke execute on function public.delete_my_account() from public, anon;
grant execute on function public.change_handle(text) to authenticated;
grant execute on function public.delete_my_account() to authenticated;
grant execute on function public.handle_available(text) to anon, authenticated;
