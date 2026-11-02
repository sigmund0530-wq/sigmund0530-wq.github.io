-- 쪽지 규칙 시험 (로컬 전용): shim.sql → schema.sql → 이 파일
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant select on all tables in schema public to anon;
insert into auth.users values ('11111111-1111-1111-1111-111111111111'),('22222222-2222-2222-2222-222222222222'),('33333333-3333-3333-3333-333333333333'),('44444444-4444-4444-4444-444444444444');
create temp table result(n serial, who text, what text, got text);
grant all on result to anon, authenticated; grant usage on sequence result_n_seq to anon, authenticated;
create or replace function pg_temp.try(who text, what text, q text) returns void language plpgsql as $$
declare r text; begin
  begin execute q into r; insert into result(who,what,got) values (who,what,coalesce(r,'(ok)'));
  exception when others then insert into result(who,what,got) values (who,what,'막힘: '||sqlerrm); end; end $$;

set role authenticated;
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111'; select create_profile('haru','하루','MUGADANG-BETA');
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222'; select create_profile('minji','민지','MUGADANG-BETA');
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333'; select create_profile('seojun','서준','MUGADANG-BETA');
set request.jwt.claim.sub='44444444-4444-4444-4444-444444444444'; select create_profile('nobody','낯선이','MUGADANG-BETA');

-- 민지 → 하루: 첫 한 통은 됨, 답장 전 두 번째는 막힘
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select pg_temp.try('민지','첫 쪽지',$q$insert into notes(recipient,body,ctx) values ('11111111-1111-1111-1111-111111111111','글 잘 읽었어요','{"kind":"post","title":"망원시장"}') returning 'sent'$q$);
select pg_temp.try('민지','답장 전 두 번째',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','또 보내요') returning 'sent'$q$);
select pg_temp.try('민지','남 이름으로 보내기',$q$insert into notes(sender,recipient,body) values ('33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111','가짜') returning 'sent'$q$);
select pg_temp.try('민지','나에게 보내기',$q$insert into notes(recipient,body) values ('22222222-2222-2222-2222-222222222222','나') returning 'sent'$q$);
-- 하루가 답장하면 계속 주고받음
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','받은 쪽지 보기',$q$select count(*)::text from notes where recipient = auth.uid()$q$);
select pg_temp.try('하루','답장',$q$insert into notes(recipient,body) values ('22222222-2222-2222-2222-222222222222','고마워요') returning 'sent'$q$);
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select pg_temp.try('민지','답장 받은 뒤 두 번째',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','또 보내요') returning 'sent'$q$);
-- 남의 쪽지는 안 보임
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select pg_temp.try('서준','남의 쪽지 엿보기',$q$select count(*)::text from notes$q$);
select pg_temp.try('서준','남의 쪽지 고치기',$q$update notes set body='바꿈' returning 'changed'$q$);
-- 받는 범위: 하루가 '내 이웃만'으로 바꾸면 서준은 못 보냄, 하루가 서준을 이웃으로 맺으면 됨
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','이웃만 받기로',$q$update profiles set note_from='followers' where id=auth.uid() returning note_from$q$);
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select pg_temp.try('서준','이웃 아닌데 보내기',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','안녕') returning 'sent'$q$);
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
insert into follows values ('11111111-1111-1111-1111-111111111111','33333333-3333-3333-3333-333333333333',now());
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select pg_temp.try('서준','하루가 이웃으로 맺은 뒤',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','안녕') returning 'sent'$q$);
select pg_temp.try('서준','이웃이면 여러 통',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','또 안녕') returning 'sent'$q$);
-- 그만 받기
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','다시 전체 받기',$q$update profiles set note_from='all' where id=auth.uid() returning note_from$q$);
select pg_temp.try('하루','낯선이 그만 받기',$q$insert into note_blocks values (auth.uid(),'44444444-4444-4444-4444-444444444444',now()) returning 'blocked'$q$);
set request.jwt.claim.sub='44444444-4444-4444-4444-444444444444';
select pg_temp.try('낯선이','그만 받기 당한 뒤',$q$insert into notes(recipient,body) values ('11111111-1111-1111-1111-111111111111','광고') returning 'sent'$q$);
select pg_temp.try('낯선이','남의 차단 목록 보기',$q$select count(*)::text from note_blocks$q$);
-- 지우기: 내 쪽에서만
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','받은 쪽지 하나 지우기',$q$select hide_note((select id from notes where sender='22222222-2222-2222-2222-222222222222' order by created_at limit 1))$q$);
select pg_temp.try('하루','지운 뒤 받은 쪽지',$q$select count(*)::text from notes where recipient = auth.uid()$q$);
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select pg_temp.try('민지','상대가 지워도 내 보낸 쪽지',$q$select count(*)::text from notes where sender = auth.uid()$q$);
-- 쪽지 그림: 받는 사람만 볼 수 있음
insert into media(id,owner,path,kind,mime) values ('img-note','22222222-2222-2222-2222-222222222222','22222222-2222-2222-2222-222222222222/img-note.jpg','image','image/jpeg');
select pg_temp.try('민지','남의 그림을 붙여 보내기',$q$insert into notes(recipient,body,media_id) values ('11111111-1111-1111-1111-111111111111','x','img-not-mine') returning 'sent'$q$);
select pg_temp.try('민지','내 그림 붙여 보내기',$q$insert into notes(recipient,body,media_id) values ('11111111-1111-1111-1111-111111111111','사진','img-note') returning 'sent'$q$);
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','받은 쪽지 그림 보기',$q$select can_read_media('img-note')::text$q$);
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select pg_temp.try('서준','남의 쪽지 그림 보기',$q$select can_read_media('img-note')::text$q$);

reset role;
select who, what, got from result order by n;
