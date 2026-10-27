-- v2 규칙 시험 (로컬 전용)
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant select on all tables in schema public to anon;
insert into auth.users values ('11111111-1111-1111-1111-111111111111'),('22222222-2222-2222-2222-222222222222'),('33333333-3333-3333-3333-333333333333'),('44444444-4444-4444-4444-444444444444'),('55555555-5555-5555-5555-555555555555');
create temp table result(n serial, who text, what text, got text);
grant all on result to anon, authenticated; grant usage on sequence result_n_seq to anon, authenticated;

create or replace function pg_temp.try(who text, what text, q text) returns void language plpgsql as $$
declare r text; begin
  begin execute q into r; insert into result(who,what,got) values (who,what,coalesce(r,'(ok)'));
  exception when others then insert into result(who,what,got) values (who,what,'막힘: '||sqlerrm); end; end $$;

set role authenticated;
-- 공간 만들기
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select pg_temp.try('하루','틀린 초대 코드',$q$select create_profile('haru','하루','WRONG')$q$);
select pg_temp.try('하루','맞는 초대 코드',$q$select create_profile('haru','하루','mugadang-beta')$q$);
select pg_temp.try('하루','두 번째 공간',$q$select create_profile('haru2','하루','MUGADANG-BETA')$q$);
select pg_temp.try('하루','프로필 직접 넣기',$q$insert into profiles(id,handle) values ('11111111-1111-1111-1111-111111111111','zzz') returning 'inserted'$q$);
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select pg_temp.try('민지','이미 쓰는 주소',$q$select create_profile('haru','민지','MUGADANG-BETA')$q$);
select pg_temp.try('민지','공간 만들기',$q$select create_profile('minji','민지','MUGADANG-BETA')$q$);
select pg_temp.try('민지','이웃 맺기',$q$insert into follows values ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111',now()) returning 'ok'$q$);
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select pg_temp.try('서준','공간 만들기',$q$select create_profile('seojun','서준','MUGADANG-BETA')$q$);
select pg_temp.try('서준','이웃 맺기',$q$insert into follows values ('33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111',now()) returning 'ok'$q$);
set request.jwt.claim.sub='44444444-4444-4444-4444-444444444444';
select pg_temp.try('낯선이','공간 만들기',$q$select create_profile('nobody','낯선이','MUGADANG-BETA')$q$);
select pg_temp.try('낯선이','남 대신 이웃 맺기',$q$insert into follows values ('11111111-1111-1111-1111-111111111111','44444444-4444-4444-4444-444444444444',now()) returning 'ok'$q$);

-- 하루가 글·파일·개인 문서 저장
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
insert into close_friends values ('11111111-1111-1111-1111-111111111111','33333333-3333-3333-3333-333333333333',now());
insert into posts(id,owner,status,visibility,allow,media_ids,data) values
 ('post-pub','11111111-1111-1111-1111-111111111111','published','public','{}','{asset-a}','{"title":"전체공개"}'),
 ('post-fol','11111111-1111-1111-1111-111111111111','published','followers','{}','{}','{"title":"이웃만"}'),
 ('post-clo','11111111-1111-1111-1111-111111111111','published','close','{}','{}','{"title":"가까운사람"}'),
 ('post-cus','11111111-1111-1111-1111-111111111111','published','custom',array['22222222-2222-2222-2222-222222222222']::uuid[],'{}','{"title":"지정민지"}'),
 ('post-pri','11111111-1111-1111-1111-111111111111','published','private','{}','{asset-b}','{"title":"나만"}'),
 ('post-dra','11111111-1111-1111-1111-111111111111','draft','public','{}','{}','{"title":"초안"}');
insert into media(id,owner,path,kind,mime) values ('asset-a','11111111-1111-1111-1111-111111111111','1111/a.jpg','image','image/jpeg'),('asset-b','11111111-1111-1111-1111-111111111111','1111/b.jpg','image','image/jpeg');
update private_docs set data='{"vault":{"lines":[{"text":"비밀 문장"}]}}' where owner='11111111-1111-1111-1111-111111111111';
update rooms set visibility='followers' where owner='11111111-1111-1111-1111-111111111111';
insert into feedback(body,page) values ('글쓰기가 편해요','editor');
select pg_temp.try('낯선이','남인 척 의견 남기기',$q$select 1$q$);

create or replace function pg_temp.look(who text) returns void language plpgsql as $$ begin
  insert into result(who,what,got) select who,'글',coalesce(string_agg(data->>'title',',' order by data->>'title'),'-') from posts;
  insert into result(who,what,got) select who,'파일',coalesce(string_agg(id,',' order by id),'-') from media;
  insert into result(who,what,got) select who,'개인문서',(select count(*)::text from private_docs where owner='11111111-1111-1111-1111-111111111111');
  insert into result(who,what,got) select who,'가까운사람목록',(select count(*)::text from close_friends);
  insert into result(who,what,got) select who,'하루의 방',(select count(*)::text from rooms where owner='11111111-1111-1111-1111-111111111111');
  insert into result(who,what,got) select who,'의견(남의 것)',(select count(*)::text from feedback where owner<>coalesce(auth.uid(),'00000000-0000-0000-0000-000000000000'));
  insert into result(who,what,got) select who,'초대코드 목록',(select count(*)::text from beta_invites);
end $$;
select pg_temp.look('하루(주인)');
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222'; select pg_temp.look('민지(이웃·지정)');
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333'; select pg_temp.look('서준(이웃·가까운)');
set request.jwt.claim.sub='44444444-4444-4444-4444-444444444444'; select pg_temp.look('낯선이');
select pg_temp.try('낯선이','남의 글 고치기',$q$update posts set data='{"title":"해킹"}' where id='post-pub' returning 'changed'$q$);
select pg_temp.try('낯선이','남의 이름으로 글쓰기',$q$insert into posts(id,owner,data) values ('post-x','11111111-1111-1111-1111-111111111111','{}') returning 'inserted'$q$);
select pg_temp.try('낯선이','남의 이름으로 의견',$q$insert into feedback(owner,body) values ('11111111-1111-1111-1111-111111111111','x') returning 'inserted'$q$);
set request.jwt.claim.sub='55555555-5555-5555-5555-555555555555';
select pg_temp.try('공간 없는 계정','공간 없이 글쓰기',$q$insert into posts(id,owner,data) values ('post-y','55555555-5555-5555-5555-555555555555','{}') returning 'inserted'$q$);
reset role; set role anon; set request.jwt.claim.sub='';
select pg_temp.look('로그인 안 함');
select pg_temp.try('로그인 안 함','주소 쓸 수 있나 haru',$q$select handle_available('haru')::text$q$);
select pg_temp.try('로그인 안 함','주소 쓸 수 있나 newone',$q$select handle_available('newone')::text$q$);
reset role;
select pg_temp.try('관리','초대 코드 사용 횟수',$q$select uses::text from beta_invites where code='MUGADANG-BETA'$q$);
select who, what, got from result order by n;
