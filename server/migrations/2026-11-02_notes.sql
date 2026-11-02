-- ═══════════════════════════════════════════════════════════════════
-- 쪽지 (2026-11-02) — 이미 쓰고 있는 데이터베이스에 덧붙이는 SQL
-- 기존 글·사람은 지우지 않아요. 여러 번 실행해도 괜찮아요.
--  · 쪽지: 한 사람에게 보내는 편지. 어디서(글·공간) 보고 보냈는지 함께 남김
--  · 읽음 표시 없음: 보낸 사람은 상대가 읽었는지 알 수 없어요 (읽은 시각을 저장하지 않음)
--  · 스팸 막기: 받는 사람이 고른 범위(전체 / 내 이웃만 / 가까운 사람만 / 받지 않기),
--    처음 보내는 사람은 답장을 받기 전까지 한 통만, 한 시간에 30통까지, 그만 받기(차단)
--  · 숫자를 세어 남에게 보여 주는 함수는 만들지 않아요
-- ═══════════════════════════════════════════════════════════════════

-- 받는 범위: all 전체 · followers 내가 이웃으로 맺은 사람만 · close 가까운 사람만 · none 받지 않기
alter table public.profiles add column if not exists note_from text not null default 'all';
do $$ begin
  alter table public.profiles add constraint profiles_note_from_chk check (note_from in ('all','followers','close','none'));
exception when duplicate_object then null; end $$;

create table if not exists public.notes (
  id             uuid primary key default gen_random_uuid(),
  sender         uuid not null default auth.uid() references public.profiles(id) on delete cascade,
  recipient      uuid not null references public.profiles(id) on delete cascade,
  body           text not null check (char_length(body) between 1 and 2000),
  ctx            jsonb not null default '{}'::jsonb check (pg_column_size(ctx) < 2048),   -- {kind:'post'|'space', id, title, quote}
  media_id       text,                                                                       -- 붙인 그림 (보낸 사람의 파일)
  created_at     timestamptz not null default now(),
  sender_hidden    boolean not null default false,
  recipient_hidden boolean not null default false,
  check (sender <> recipient)
);
create index if not exists notes_recipient_idx on public.notes (recipient, created_at desc);
create index if not exists notes_sender_idx    on public.notes (sender, created_at desc);

create table if not exists public.note_blocks (          -- 이 사람 쪽지 그만 받기
  owner      uuid not null references public.profiles(id) on delete cascade,
  blocked    uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (owner, blocked), check (owner <> blocked)
);

-- 보낼 수 있는지 (받는 사람 쪽 규칙을 서버에서 지킴)
create or replace function public.note_ok(p_to uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and p_to is not null and p_to <> auth.uid()
    and exists (select 1 from profiles where id = p_to)
    and not exists (select 1 from note_blocks b where b.owner = p_to and b.blocked = auth.uid())
    and (select count(*) from notes n where n.sender = auth.uid() and n.created_at > now() - interval '1 hour') < 30
    and case coalesce((select note_from from profiles where id = p_to), 'all')
          when 'none'      then false
          when 'close'     then is_close(p_to, auth.uid())
          when 'followers' then is_follower(p_to, auth.uid())
          else true end
    and ( exists (select 1 from notes n where n.sender = p_to and n.recipient = auth.uid())      -- 이미 답장을 받음
       or is_follower(p_to, auth.uid())                                                         -- 받는 사람이 나를 이웃으로
       or is_close(p_to, auth.uid())
       or not exists (select 1 from notes n where n.sender = auth.uid() and n.recipient = p_to) ) -- 아니면 첫 한 통만
$$;

-- 지우기(내 쪽에서만 안 보이게). 상대 쪽에는 그대로 남아요
create or replace function public.hide_note(p_id uuid) returns text
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_signed_in'; end if;
  update notes set sender_hidden = true    where id = p_id and sender = uid;
  update notes set recipient_hidden = true where id = p_id and recipient = uid;
  return 'ok';
end $$;

alter table public.notes       enable row level security;
alter table public.note_blocks enable row level security;

drop policy if exists notes_read on public.notes;
create policy notes_read on public.notes for select
  using ((sender = auth.uid() and not sender_hidden) or (recipient = auth.uid() and not recipient_hidden));
drop policy if exists notes_send on public.notes;
create policy notes_send on public.notes for insert
  with check (sender = auth.uid() and not sender_hidden and not recipient_hidden and public.note_ok(recipient)
              and (media_id is null or exists (select 1 from public.media m where m.id = media_id and m.owner = auth.uid())));
-- 고치기·지우기 정책 없음: 보낸 쪽지는 고칠 수 없고, 지우기는 hide_note 로만

drop policy if exists own_blocks on public.note_blocks;
create policy own_blocks on public.note_blocks for all using (owner = auth.uid()) with check (owner = auth.uid());

-- 쪽지에 붙인 그림은 받는 사람도 볼 수 있게
create or replace function public.can_read_media(m_id text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from media m where m.id = m_id and (
       m.owner = auth.uid()
    or exists (select 1 from profiles pr where pr.id = m.owner and (pr.photo_id = m.id or pr.look->>'coverId' = m.id))
    or exists (select 1 from posts p where p.owner = m.owner and m.id = any (p.media_ids) and can_read_post(p))
    or exists (select 1 from rooms r where r.owner = m.owner and m.id = any (r.media_ids) and can_read_room(r))
    or exists (select 1 from notes n where n.media_id = m.id and n.sender = m.owner and n.recipient = auth.uid() and not n.recipient_hidden))) $$;

revoke execute on function public.note_ok(uuid) from public, anon;
revoke execute on function public.hide_note(uuid) from public, anon;
grant execute on function public.note_ok(uuid) to authenticated;
grant execute on function public.hide_note(uuid) to authenticated;
