-- ═══════════════════════════════════════════════════════════════════
-- 무가당 데이터베이스 (Supabase / PostgreSQL)
-- Supabase 대시보드 → SQL Editor 에 이 파일 전체를 붙여 넣고 실행.
--
-- 원칙
--  · 글의 공개 범위는 화면이 아니라 여기(데이터베이스 규칙)에서 지킨다.
--  · 나만 보는 것(이전 버전, 내 문장·단어장, 쓰다 만 글)은 주인만 읽고 쓴다.
--  · 가까운 사람 목록은 주인만 본다(상대는 자기가 들어 있는지 알 수 없음).
--  · 숫자(이웃 수 등)를 보여 주는 함수는 만들지 않는다.
-- ═══════════════════════════════════════════════════════════════════

create extension if not exists pgcrypto;

-- ── 프로필 · 내 공간 설정 ──────────────────────────────────────────
create table if not exists public.profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  handle        text unique not null check (handle ~ '^[a-z0-9](?:[a-z0-9-]{1,18}[a-z0-9])$'),
  display_name  text not null default '',
  status        text not null default '' check (char_length(status) <= 60),   -- 소개 한 줄
  space_name    text,                                                        -- 비우면 '별명의 공간'
  photo_id      uuid,                                                        -- media.id
  cover_id      uuid,
  look          jsonb not null default '{}'::jsonb,   -- 분위기(글꼴·색·바탕), 공간 CSS 등 공개되는 꾸밈
  settings      jsonb not null default '{}'::jsonb,   -- 기본 공개 범위 등 (주인만 의미 있음, 민감한 것은 넣지 않음)
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- 나만 보는 개인 설정·보관함 (소개 이력, 나만 아는 질문 답 해시 등)
create table if not exists public.private_settings (
  owner        uuid primary key references public.profiles(id) on delete cascade,
  data         jsonb not null default '{}'::jsonb,
  updated_at   timestamptz not null default now()
);

-- ── 관계: 이웃(한쪽 맺기) · 가까운 사람(주인이 조용히 고름) ─────────────
create table if not exists public.follows (
  follower    uuid not null references public.profiles(id) on delete cascade,
  followee    uuid not null references public.profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (follower, followee),
  check (follower <> followee)
);
create table if not exists public.close_friends (
  owner       uuid not null references public.profiles(id) on delete cascade,
  friend      uuid not null references public.profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (owner, friend),
  check (owner <> friend)
);

-- ── 카테고리 (글마다 하나, 기본 공개 범위) ─────────────────────────
create table if not exists public.categories (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null references public.profiles(id) on delete cascade,
  name        text not null check (char_length(name) between 1 and 30),
  visibility  text not null default 'private' check (visibility in ('private','close','followers','custom','public')),
  sort        int not null default 0,
  created_at  timestamptz not null default now()
);

-- ── 글 ─────────────────────────────────────────────────────────────
create table if not exists public.posts (
  id                 uuid primary key default gen_random_uuid(),
  owner              uuid not null references public.profiles(id) on delete cascade,
  status             text not null default 'draft' check (status in ('draft','published')),
  visibility         text not null default 'private' check (visibility in ('private','close','followers','custom','public')),
  allow              uuid[] not null default '{}',            -- '지정한 사람만'일 때 볼 수 있는 사람
  category_id        uuid references public.categories(id) on delete set null,
  title              text not null default '',
  body               jsonb not null default '{"version":2,"blocks":[]}'::jsonb,  -- 문단·사진·음성 덩어리
  ink                jsonb not null default '[]'::jsonb,       -- 글 위에 그린 선
  addenda            jsonb not null default '[]'::jsonb,       -- 날짜 있는 덧붙임
  media_ids          uuid[] not null default '{}',             -- 이 글에 쓰인 사진·음성 (파일 읽기 권한에 씀)
  cover_id           uuid,
  recorded_at        date not null default current_date,       -- 내가 정한 글 날짜
  show_date          boolean not null default true,
  created_at         timestamptz not null default now(),       -- 실제로 만든 시각 (바뀌지 않음)
  updated_at         timestamptz not null default now(),
  first_published_at timestamptz,
  revision           int not null default 0,
  -- 전체 공개 + 발행 = 무작위 피드에 실림 (따로 고르는 칸 없음)
  in_feed            boolean generated always as (status = 'published' and visibility = 'public') stored
);
create index if not exists posts_owner_idx on public.posts (owner, recorded_at desc);
create index if not exists posts_feed_idx  on public.posts (first_published_at desc) where in_feed;

-- 이전 버전 (주인만)
create table if not exists public.post_revisions (
  id        uuid primary key default gen_random_uuid(),
  post_id   uuid not null references public.posts(id) on delete cascade,
  owner     uuid not null references public.profiles(id) on delete cascade,
  title     text not null default '',
  body      jsonb not null,
  ink       jsonb not null default '[]'::jsonb,
  saved_at  timestamptz not null default now()
);
create index if not exists post_revisions_post_idx on public.post_revisions (post_id, saved_at desc);

-- 쓰다 만 글 (기기 간 이어 쓰기, 주인만)
create table if not exists public.drafts (
  owner      uuid not null references public.profiles(id) on delete cascade,
  slot       text not null,                 -- 'new' 또는 고치는 글의 id
  data       jsonb not null,
  saved_at   timestamptz not null default now(),
  primary key (owner, slot)
);

-- 내 문장 · 단어장 (주인만)
create table if not exists public.vault (
  owner      uuid primary key references public.profiles(id) on delete cascade,
  lines      jsonb not null default '[]'::jsonb,
  words      jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

-- ── 내 방 (배치·위젯·모음) ─────────────────────────────────────────
create table if not exists public.rooms (
  owner       uuid primary key references public.profiles(id) on delete cascade,
  visibility  text not null default 'public' check (visibility in ('public','followers','private')),
  layout      jsonb not null default '{}'::jsonb,   -- 위젯·배치·모음(글 id 목록). 글 내용은 넣지 않음
  media_ids   uuid[] not null default '{}',
  updated_at  timestamptz not null default now()
);

-- ── 사진·음성 파일 정보 (파일 자체는 Storage 'media' 버킷, 경로 = 주인id/파일id) ──
create table if not exists public.media (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null references public.profiles(id) on delete cascade,
  path        text not null unique,
  kind        text not null check (kind in ('image','audio')),
  mime        text not null,
  width       int,
  height      int,
  bytes       int,
  created_at  timestamptz not null default now()
);

-- ═══════════════════════════════════════════════════════════════════
-- 읽기 권한 판단 (정의자 권한으로 실행 → 가까운 사람 목록을 노출하지 않고 판단만 함)
-- ═══════════════════════════════════════════════════════════════════
create or replace function public.is_follower(viewer uuid, owner uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select viewer is not null and exists (select 1 from follows f where f.follower = viewer and f.followee = owner)
$$;

create or replace function public.is_close(owner uuid, viewer uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select viewer is not null and exists (select 1 from close_friends c where c.owner = is_close.owner and c.friend = viewer)
$$;

create or replace function public.can_read_post(p public.posts) returns boolean
language sql stable security definer set search_path = public as $$
  select
    p.owner = auth.uid()
    or (p.status = 'published' and (
         p.visibility = 'public'
      or (p.visibility = 'followers' and is_follower(auth.uid(), p.owner))
      or (p.visibility = 'close'     and is_close(p.owner, auth.uid()))
      or (p.visibility = 'custom'    and auth.uid() = any (p.allow))
    ))
$$;

create or replace function public.can_read_room(r public.rooms) returns boolean
language sql stable security definer set search_path = public as $$
  select r.owner = auth.uid()
      or r.visibility = 'public'
      or (r.visibility = 'followers' and is_follower(auth.uid(), r.owner))
$$;

-- 파일: 주인이거나, 프로필 사진·커버이거나, 읽을 수 있는 글/방에 쓰인 파일이면 읽기 가능
create or replace function public.can_read_media(m_id uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from media m where m.id = m_id and (
         m.owner = auth.uid()
      or exists (select 1 from profiles pr where pr.id = m.owner and (pr.photo_id = m.id or pr.cover_id = m.id))
      or exists (select 1 from posts p where p.owner = m.owner and m.id = any (p.media_ids) and can_read_post(p))
      or exists (select 1 from rooms r where r.owner = m.owner and m.id = any (r.media_ids) and can_read_room(r))
    ))
$$;

-- ═══════════════════════════════════════════════════════════════════
-- 행 단위 보안 (RLS)
-- ═══════════════════════════════════════════════════════════════════
alter table public.profiles          enable row level security;
alter table public.private_settings  enable row level security;
alter table public.follows           enable row level security;
alter table public.close_friends     enable row level security;
alter table public.categories        enable row level security;
alter table public.posts             enable row level security;
alter table public.post_revisions    enable row level security;
alter table public.drafts            enable row level security;
alter table public.vault             enable row level security;
alter table public.rooms             enable row level security;
alter table public.media             enable row level security;

-- 프로필: 누구나 읽음(공간 주소로 찾아오기), 고치기는 본인만
drop policy if exists profiles_read on public.profiles;
create policy profiles_read  on public.profiles for select using (true);
drop policy if exists profiles_write on public.profiles;
create policy profiles_write on public.profiles for all using (id = auth.uid()) with check (id = auth.uid());

-- 주인만
drop policy if exists own_private on public.private_settings;
create policy own_private on public.private_settings for all using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists own_revisions on public.post_revisions;
create policy own_revisions on public.post_revisions for all using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists own_drafts on public.drafts;
create policy own_drafts on public.drafts for all using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists own_vault on public.vault;
create policy own_vault on public.vault for all using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists own_close on public.close_friends;
create policy own_close on public.close_friends for all using (owner = auth.uid()) with check (owner = auth.uid());

-- 이웃: 내가 맺은 것과 나를 맺은 것만 보임. 맺기·끊기는 내 쪽만
drop policy if exists follows_read on public.follows;
create policy follows_read on public.follows for select using (follower = auth.uid() or followee = auth.uid());
drop policy if exists follows_add on public.follows;
create policy follows_add on public.follows for insert with check (follower = auth.uid());
drop policy if exists follows_del on public.follows;
create policy follows_del on public.follows for delete using (follower = auth.uid());

-- 카테고리: 주인은 전부, 남에게는 '나만'이 아닌 것만(이름이 보임)
drop policy if exists cats_read on public.categories;
create policy cats_read on public.categories for select using (owner = auth.uid() or visibility <> 'private');
drop policy if exists cats_write on public.categories;
create policy cats_write on public.categories for all using (owner = auth.uid()) with check (owner = auth.uid());

-- 글: 읽기는 공개 범위 규칙, 쓰기는 주인만
drop policy if exists posts_read on public.posts;
create policy posts_read on public.posts for select using (public.can_read_post(posts));
drop policy if exists posts_write on public.posts;
create policy posts_write on public.posts for all using (owner = auth.uid()) with check (owner = auth.uid());

-- 내 방
drop policy if exists rooms_read on public.rooms;
create policy rooms_read on public.rooms for select using (public.can_read_room(rooms));
drop policy if exists rooms_write on public.rooms;
create policy rooms_write on public.rooms for all using (owner = auth.uid()) with check (owner = auth.uid());

-- 파일 정보
drop policy if exists media_read on public.media;
create policy media_read on public.media for select using (public.can_read_media(id));
drop policy if exists media_write on public.media;
create policy media_write on public.media for all using (owner = auth.uid()) with check (owner = auth.uid());

-- '지정한 사람만'에 남의 글 목록이 새지 않게: allow 는 주인에게만 의미. (읽는 사람은 자기 id 포함 여부로만 판단됨)

-- updated_at 자동
create or replace function public.touch() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
drop trigger if exists posts_touch on public.posts;
create trigger posts_touch before update on public.posts for each row execute function public.touch();
drop trigger if exists profiles_touch on public.profiles;
create trigger profiles_touch before update on public.profiles for each row execute function public.touch();
