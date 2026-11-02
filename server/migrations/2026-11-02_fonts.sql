-- ═══════════════════════════════════════════════════════════════════
-- 2026-11-02 · 내 글꼴 (올린 글꼴 · 직접 만든 글꼴)
-- 이미 쓰는 데이터베이스에 덧붙이는 SQL. 여러 번 실행해도 안전하고, 데이터를 지우지 않아요.
--
-- - media 표가 'font'(글꼴 파일)도 받게 함.
--   · 올린 글꼴 원본: 주인만 읽음(어떤 글에도 media_ids로 걸리지 않으므로 can_read_media가 남에게 안 열어 줌).
--   · 글에 쓰인 글자만 잘라 낸 작은 글꼴: 그 글의 media_ids에 들어가서, 그 글을 읽을 수 있는 사람만 읽음(사진과 같은 규칙).
-- - 저장소(media 버킷)는 이미 파일 하나 10MB까지라 그대로 둠.
-- ═══════════════════════════════════════════════════════════════════
alter table public.media drop constraint if exists media_kind_check;
alter table public.media add constraint media_kind_check check (kind in ('image','audio','font'));
