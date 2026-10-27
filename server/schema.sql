-- ═══════════════════════════════════════════════════════════════════
-- 무가당 데이터베이스 v2 (Supabase / PostgreSQL)
-- Supabase → SQL Editor 에 통째로 붙여 넣고 Run. 그다음 storage.sql.
-- ⚠ 맨 위에서 예전(v1) 테이블을 지우고 새로 만들어요. 베타 시작 전이라 지워질 데이터가 없을 때만 실행하세요.
--
-- 원칙
--  · 글의 공개 범위는 화면이 아니라 여기서 지킨다 (행 단위 보안).
--  · 나만 보는 것(내 문장·단어장·이전 버전·소개 이력·계정 설정)은 주인만 읽는 개인 문서에 둔다.
--  · 가까운 사람 목록은 주인만 본다.
--  · 베타 동안은 초대 코드가 있어야 공간을 만들 수 있다.
--  · 숫자(이웃 수 등)를 세어 주는 함수는 만들지 않는다.
-- ═══════════════════════════════════════════════════════════════════
create extension if not exists pgcrypto;

drop table if exists public.feedback, public.beta_invites, public.media, public.rooms, public.vault, public.drafts,
  public.post_revisions, public.posts, public.categories, public.close_friends, public.follows,
  public.private_settings, public.private_docs, public.profiles cascade;
drop function if exists public.can_read_post(public.posts) cascade;
drop function if exists public.can_read_room(public.rooms) cascade;
drop function if exists public.can_read_media(uuid) cascade;
drop function if exists public.can_read_media(text) cascade;
drop function if exists public.is_follower(uuid,uuid) cascade;
drop function if exists public.is_close(uuid,uuid) cascade;
drop function if exists public.create_profile(text,text,text) cascade;
drop function if exists public.handle_available(text) cascade;
drop function if exists public.invite_ok(text) cascade;

-- ── 공개 프로필 (공간 주소로 누구나 찾아올 수 있음) ─────────────────────
create table public.profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  handle        text unique not null check (handle ~ '^[a-z0-9](?:[a-z0-9-]{1,18}[a-z0-9])$'),
  display_name  text not null default '' check (char_length(display_name) <= 30),
  status        text not null default '' check (char_length(status) <= 60),
  space_name    text check (char_length(space_name) <= 30),
  photo_id      text,
  look          jsonb not null default '{}'::jsonb,   -- 커버·분위기 등 남에게 보이는 꾸밈
  data          jsonb not null default '{}'::jsonb,   -- 그 밖의 공개 프로필 값
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ── 나만 보는 개인 문서 (내 문장·단어장·이전 버전·소개 이력·계정 설정·나만 아는 질문 해시) ──
create table public.private_docs (
  owner       uuid primary key references public.profiles(id) on delete cascade,
  data        jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

-- ── 관계 ───────────────────────────────────────────────────────────
create table public.follows (            -- 이웃: 한쪽에서 맺음
  follower    uuid not null references public.profiles(id) on delete cascade,
  followee    uuid not null references public.profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (follower, followee), check (follower <> followee)
);
create table public.close_friends (      -- 가까운 사람: 주인이 조용히 고름
  owner       uuid not null references public.profiles(id) on delete cascade,
  friend      uuid not null references public.profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (owner, friend), check (owner <> friend)
);

-- ── 카테고리 ────────────────────────────────────────────────────────
create table public.categories (
  id          text primary key check (char_length(id) between 3 and 64),
  owner       uuid not null references public.profiles(id) on delete cascade,
  name        text not null check (char_length(name) between 1 and 30),
  visibility  text not null default 'private' check (visibility in ('private','close','followers','custom','public')),
  sort        int not null default 0,
  data        jsonb not null default '{}'::jsonb
);

-- ── 글 ─────────────────────────────────────────────────────────────
create table public.posts (
  id                 text primary key check (char_length(id) between 3 and 64),
  owner              uuid not null references public.profiles(id) on delete cascade,
  status             text not null default 'draft' check (status in ('draft','published')),
  visibility         text not null default 'private' check (visibility in ('private','close','followers','custom','public')),
  allow              uuid[] not null default '{}',     -- '지정한 사람만'
  category_id        text,
  recorded_at        date,                             -- 내가 정한 글 날짜
  first_published_at timestamptz,
  media_ids          text[] not null default '{}',     -- 이 글에 쓰인 사진·음성
  data               jsonb not null,                   -- 제목·본문 덩어리·그림·덧붙임 등 글 전체
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  in_feed            boolean generated always as (status = 'published' and visibility = 'public') stored  -- 전체 공개 = 무작위 피드
);
create index posts_owner_idx on public.posts (owner, recorded_at desc);
create index posts_feed_idx  on public.posts (first_published_at desc) where in_feed;

-- ── 내 방 ──────────────────────────────────────────────────────────
create table public.rooms (
  owner       uuid primary key references public.profiles(id) on delete cascade,
  visibility  text not null default 'public' check (visibility in ('public','followers','private')),
  layout      jsonb not null default '{}'::jsonb,
  media_ids   text[] not null default '{}',
  updated_at  timestamptz not null default now()
);

-- ── 사진·음성 파일 정보 (파일은 Storage 'media' 버킷, 경로 = 주인id/파일id) ──
create table public.media (
  id          text primary key check (char_length(id) between 3 and 64),
  owner       uuid not null references public.profiles(id) on delete cascade,
  path        text not null unique,
  kind        text not null check (kind in ('image','audio')),
  mime        text not null,
  width       int, height int, bytes int,
  created_at  timestamptz not null default now()
);

-- ── 베타: 초대 코드 · 의견 ─────────────────────────────────────────
create table public.beta_invites (
  code       text primary key,
  max_uses   int not null default 50,
  uses       int not null default 0,
  note       text,
  created_at timestamptz not null default now()
);
create table public.feedback (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references public.profiles(id) on delete cascade,
  page       text,
  body       text not null check (char_length(body) between 1 and 4000),
  created_at timestamptz not null default now()
);
insert into public.beta_invites(code, max_uses, note) values ('MUGADANG-BETA', 100, '첫 베타 초대 코드') on conflict do nothing;

-- ═══════════════════════════════════════════════════════════════════
-- 읽기 권한 판단 (정의자 권한: 가까운 사람 목록을 드러내지 않고 판단만)
-- ═══════════════════════════════════════════════════════════════════
create function public.is_follower(viewer uuid, owner uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select viewer is not null and exists (select 1 from follows f where f.follower = viewer and f.followee = owner) $$;
create function public.is_close(owner uuid, viewer uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select viewer is not null and exists (select 1 from close_friends c where c.owner = is_close.owner and c.friend = viewer) $$;
create function public.can_read_post(p public.posts) returns boolean
language sql stable security definer set search_path = public as $$
  select p.owner = auth.uid()
    or (p.status = 'published' and (
         p.visibility = 'public'
      or (p.visibility = 'followers' and is_follower(auth.uid(), p.owner))
      or (p.visibility = 'close'     and is_close(p.owner, auth.uid()))
      or (p.visibility = 'custom'    and auth.uid() = any (p.allow)))) $$;
create function public.can_read_room(r public.rooms) returns boolean
language sql stable security definer set search_path = public as $$
  select r.owner = auth.uid() or r.visibility = 'public' or (r.visibility = 'followers' and is_follower(auth.uid(), r.owner)) $$;
create function public.can_read_media(m_id text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from media m where m.id = m_id and (
       m.owner = auth.uid()
    or exists (select 1 from profiles pr where pr.id = m.owner and (pr.photo_id = m.id or pr.look->>'coverId' = m.id))
    or exists (select 1 from posts p where p.owner = m.owner and m.id = any (p.media_ids) and can_read_post(p))
    or exists (select 1 from rooms r where r.owner = m.owner and m.id = any (r.media_ids) and can_read_room(r)))) $$;

-- 공간 주소 쓸 수 있는지
create function public.handle_available(p_handle text) returns boolean
language sql stable security definer set search_path = public as $$
  select p_handle ~ '^[a-z0-9](?:[a-z0-9-]{1,18}[a-z0-9])$'
     and p_handle not in ('admin','mugadang','help','settings','feed','login','api','www')
     and not exists (select 1 from profiles where handle = p_handle) $$;

-- 초대 코드가 맞는지만 알려 줌 (코드 목록은 안 보임)
create function public.invite_ok(p_code text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from beta_invites where code = upper(trim(p_code)) and uses < max_uses) $$;

-- 공간 만들기: 로그인한 사람만, 초대 코드가 맞을 때만, 한 사람에 하나
create function public.create_profile(p_handle text, p_name text, p_code text) returns text
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_signed_in'; end if;
  if exists (select 1 from profiles where id = uid) then raise exception 'already_exists'; end if;
  if not exists (select 1 from beta_invites where code = upper(trim(p_code)) and uses < max_uses) then raise exception 'invite_invalid'; end if;
  if not handle_available(p_handle) then raise exception 'handle_unavailable'; end if;
  insert into profiles(id, handle, display_name) values (uid, p_handle, left(coalesce(p_name,''), 30));
  insert into private_docs(owner) values (uid);
  insert into rooms(owner) values (uid);
  update beta_invites set uses = uses + 1 where code = upper(trim(p_code));
  return 'ok';
end $$;

-- ═══════════════════════════════════════════════════════════════════
-- 행 단위 보안
-- ═══════════════════════════════════════════════════════════════════
alter table public.profiles      enable row level security;
alter table public.private_docs  enable row level security;
alter table public.follows       enable row level security;
alter table public.close_friends enable row level security;
alter table public.categories    enable row level security;
alter table public.posts         enable row level security;
alter table public.rooms         enable row level security;
alter table public.media         enable row level security;
alter table public.beta_invites  enable row level security;   -- 정책 없음 = 함수로만 다룸
alter table public.feedback      enable row level security;

create policy profiles_read   on public.profiles for select using (true);
create policy profiles_update on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());
create policy profiles_delete on public.profiles for delete using (id = auth.uid());
-- (만들기는 create_profile 함수로만)

create policy own_private on public.private_docs  for all using (owner = auth.uid()) with check (owner = auth.uid());
create policy own_close   on public.close_friends for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy follows_read on public.follows for select using (follower = auth.uid() or followee = auth.uid());
create policy follows_add  on public.follows for insert with check (follower = auth.uid());
create policy follows_del  on public.follows for delete using (follower = auth.uid());

create policy cats_read  on public.categories for select using (owner = auth.uid() or visibility <> 'private');
create policy cats_write on public.categories for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy posts_read  on public.posts for select using (public.can_read_post(posts));
create policy posts_write on public.posts for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy rooms_read  on public.rooms for select using (public.can_read_room(rooms));
create policy rooms_write on public.rooms for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy media_read  on public.media for select using (public.can_read_media(id));
create policy media_write on public.media for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy feedback_add  on public.feedback for insert with check (owner = auth.uid());
create policy feedback_mine on public.feedback for select using (owner = auth.uid());

create or replace function public.touch() returns trigger language plpgsql as $$ begin new.updated_at = now(); return new; end $$;
create trigger posts_touch    before update on public.posts        for each row execute function public.touch();
create trigger profiles_touch before update on public.profiles     for each row execute function public.touch();
create trigger private_touch  before update on public.private_docs for each row execute function public.touch();
create trigger rooms_touch    before update on public.rooms        for each row execute function public.touch();

grant execute on function public.create_profile(text,text,text) to authenticated;
grant execute on function public.handle_available(text) to anon, authenticated;
grant execute on function public.invite_ok(text) to anon, authenticated;
