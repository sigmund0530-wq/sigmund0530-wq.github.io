# 게스트로 써 보기: 첫 화면 → 가입 없이 바로 내 공간 · 서버 안 씀 · 새로 열어도 유지 · 가입하고 이어 쓰기 → 가입 → 게스트 글이 새 계정으로 올라감
from base import *
U2='http://127.0.0.1:8820/app_sb.html'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in (False,True):
    tag='M' if mob else 'PC'
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U2);pg.wait_for_timeout(700)
    ok(pg.locator('[data-au-guest]').count()==1,tag+' 첫 화면에 가입 없이 써 보기')
    pg.locator('[data-au-guest]').click();pg.wait_for_timeout(600)
    ok(pg.locator('.guest-bar').count()==1 and pg.locator('[data-au-guest]').count()==0,tag+' 바로 내 공간 + 게스트 줄')
    write(pg,mob,'게스트 글','가입 없이 써 봤다');closeall(pg);pg.wait_for_timeout(1800)
    calls=pg.evaluate("window.__mock.calls.length");ok(calls==0,tag+' 서버를 전혀 안 부름',calls)
    pg.reload();pg.wait_for_timeout(900);ok(pg.locator('.guest-bar').count()==1 and any(x.get('title')=='게스트 글' for x in rec(pg)['posts']),tag+' 다시 열어도 게스트 그대로')
    pg.locator('[data-guest-up]').first.click();pg.wait_for_timeout(1200)
    ok(pg.locator('[data-au-method="email"]').count()==1,tag+' 가입하고 이어 쓰기 → 가입 첫 화면')
    pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
    h='gst'+tag.lower();pg.fill('#au-mail',h+'@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle',h);pg.fill('#au-invite','MUGADANG-BETA')
    pg.locator('[data-au-make]').click();pg.wait_for_timeout(700)
    if pg.locator('[data-aup-skip]').count():pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500)
    if pg.locator('[data-au-enter]').count():pg.locator('[data-au-enter]').click();pg.wait_for_timeout(2500)
    db=pg.evaluate("window.__mock.db");titles=[(r.get('data') or {}).get('title') for r in db['tables']['posts']]
    ok('게스트 글' in titles,tag+' 게스트로 쓴 글이 새 계정으로 올라감',titles)
    ok(pg.locator('.guest-bar').count()==0,tag+' 가입 뒤엔 게스트 줄 없음')
    ok(rec(pg)['profile'].get('handle')==h,tag+' 주소는 가입 때 정한 것',rec(pg)['profile'].get('handle'))
    ok(not errs,tag+' ERR',errs);ctx.close()
