# 설정 화면: 들어가는 길 · 공개 범위 · 주소 한 번 바꾸기 · 탈퇴 (브라우저 저장 / 가짜 서버)
from base import *
import json
U2='http://127.0.0.1:8820/app_sb.html'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
with sync_playwright() as p:
  b=p.chromium.launch()
  # 1) PC, 브라우저 저장
  pg=setup(b,False);errs=pg.errs
  pg.locator('[data-pn="menu"]').click();pg.wait_for_timeout(200);labels=pg.locator('.menu button,[role=menuitem]').all_text_contents()
  ok(any('설정' in t for t in labels) and not any('백업' in t for t in labels),'내 메뉴: 흩어진 항목 대신 설정',labels)
  pg.keyboard.press('Escape');pg.wait_for_timeout(100)
  pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200)
  ok(pg.locator('.pn-card [data-pc="acctset"]').count()==1 and pg.locator('.pn-card .pn-links').count()==0,'내 이름 팝업: 설정·로그아웃만')
  pg.locator('.pn-card [data-pc="acctset"]').click();pg.wait_for_timeout(300)
  ok(pg.locator('.set-page').count()==1,'설정 화면 열림');pg.screenshot(path='set_pc.png',full_page=True)
  pg.select_option('[data-set-sel="defaultVis"]','public');pg.wait_for_timeout(200);ok(rec(pg)['settings'].get('defaultVis')=='public','기본 공개 범위 저장')
  pg.locator('[data-set="handle"]').click();pg.wait_for_timeout(200);pg.fill('#s-h','haru-new');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(300)
  ok(rec(pg)['profile']['handle']=='haru-new','주소 바꿈');ok(pg.locator('[data-set="handle"]').count()==0,'두 번째는 버튼 없음')
  pg.go_back();pg.wait_for_timeout(300);ok(pg.locator('.set-page').count()==0,'뒤로 가기로 설정에서 나감')
  pg.go_forward();pg.wait_for_timeout(300)
  if pg.locator('.set-page').count()==0:
    pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click();pg.wait_for_timeout(300)
  pg.locator('[data-set="leave"]').click();pg.wait_for_timeout(200);ok(pg.locator('.dialog [data-bk]').count()==1,'탈퇴: 백업 권함')
  pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  ok(pg.locator('[data-au-method="email"],[data-au-social]').count()>0,'탈퇴 → 처음 화면');ok(not rec(pg) or len(rec(pg)['posts'])==0,'탈퇴 → 이 브라우저 기록 지움')
  ok(not errs,'PC ERR',errs);pg.context.close()
  # 2) 휴대폰: 톱니 → 설정
  pg=setup(b,True);errs=pg.errs
  pg.locator('[data-m-settings]').first.click();pg.wait_for_timeout(200);labels=pg.locator('.menu button,[role=menuitem]').all_text_contents();ok(any('설정' in t for t in labels),'휴대폰 톱니 메뉴에 설정',labels)
  pg.get_by_text('설정',exact=True).first.click();pg.wait_for_timeout(300);ok(pg.locator('.set-page').count()==1,'휴대폰 설정 화면');pg.screenshot(path='set_m.png',full_page=True)
  ok(not errs,'M ERR',errs);pg.context.close()
  # 3) 가짜 서버: 비밀번호 · 주소 · 탈퇴
  ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail','s@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle','harus');pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
  write(pg,False,'서버 글','하나','p1.jpg');closeall(pg);pg.wait_for_timeout(2500)
  db=lambda:pg.evaluate("window.__mock.db")
  ok(len(db()['files'])==1,'서버: 글·사진 올라감')
  pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click();pg.wait_for_timeout(300)
  ok('s@x.com' in pg.locator('.set-page').inner_text(),'서버: 이메일 보임')
  pg.locator('[data-set="pw"]').click();pg.wait_for_timeout(200);pg.fill('#s-pw0','wrong');pg.fill('#s-pw1','newpass123');pg.fill('#s-pw2','newpass123');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  ok(db()['users'][0]['password']=='password123','서버: 틀린 지금 비밀번호는 막힘')
  pg.locator('[data-set="pw"]').click();pg.wait_for_timeout(200);pg.fill('#s-pw0','password123');pg.fill('#s-pw1','newpass123');pg.fill('#s-pw2','newpass123');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  ok(db()['users'][0]['password']=='newpass123','서버: 비밀번호 바뀜')
  pg.locator('[data-set="handle"]').click();pg.wait_for_timeout(200);pg.fill('#s-h','harus2');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
  ok(db()['tables']['profiles'][0]['handle']=='harus2' and rec(pg)['profile']['handle']=='harus2','서버: 주소 바뀜')
  pg.locator('[data-set="leave"]').click();pg.wait_for_timeout(200);pg.fill('#s-lpw','wrong');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500);ok(len(db()['users'])==1,'서버: 틀린 비밀번호면 탈퇴 안 됨')
  pg.locator('[data-set="leave"]').click();pg.wait_for_timeout(200);pg.fill('#s-lpw','newpass123');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(1500)
  d=db();ok(len(d['users'])==0 and len(d['tables']['posts'])==0 and len(d['files'])==0 and len(d['tables']['profiles'])==0,'서버: 계정·글·사진 모두 지워짐',(len(d['users']),len(d['tables']['posts']),len(d['files'])))
  ok(pg.locator('[data-au-method="email"]').count()==1,'서버: 탈퇴 → 처음 화면');ok(len(rec(pg)['posts'])==0 and pg.evaluate("localStorage.getItem('mgd2.v1.assets')") in (None,'{}') and not pg.evaluate("localStorage.getItem('mgd2.v1.sbuser')"),'서버: 이 기기 사본 지움(빈 처음 상태만 남음)')
  ok(not errs,'SB ERR',errs);b.close()
