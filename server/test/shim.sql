-- 로컬 시험용: Supabase가 제공하는 auth 스키마·역할을 흉내 냄 (실서버에는 실행하지 않음)
create role anon nologin;
create role authenticated nologin;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated;
grant execute on function auth.uid() to anon, authenticated;
