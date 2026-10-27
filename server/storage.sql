-- ═══════════════════════════════════════════════════════════════════
-- 무가당 파일 저장소 v2 (schema.sql v2와 짝)
-- 무가당 파일 저장소 (사진·음성) — schema.sql 다음에 실행
-- 버킷 'media' 는 비공개. 파일 경로는 '주인id/파일id.확장자'.
-- 읽기: 주인이거나, 그 파일이 쓰인 글·방·프로필을 읽을 수 있는 사람만.
-- ═══════════════════════════════════════════════════════════════════
insert into storage.buckets (id, name, public, file_size_limit)
values ('media', 'media', false, 10485760)     -- 파일 하나 10MB까지
on conflict (id) do nothing;

drop policy if exists media_upload on storage.objects;
create policy media_upload on storage.objects for insert to authenticated
  with check (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists media_owner_change on storage.objects;
create policy media_owner_change on storage.objects for update to authenticated
  using (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists media_owner_delete on storage.objects;
create policy media_owner_delete on storage.objects for delete to authenticated
  using (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists media_read on storage.objects;
create policy media_read on storage.objects for select
  using (bucket_id = 'media' and (
    (storage.foldername(name))[1] = auth.uid()::text      -- 내 파일은 언제나
    or exists (select 1 from public.media m where m.path = storage.objects.name and public.can_read_media(m.id))));
