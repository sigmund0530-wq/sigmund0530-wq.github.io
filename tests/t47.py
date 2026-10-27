from base import *
import json
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':860},accept_downloads=True);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200)
  ok('signup copy unified','자동으로 보내지 않아요' not in pg.content());pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-write]');pg.wait_for_timeout(400)
  pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type('비밀 문장이 있다. 바다가 좋았다.')
  pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog input[value="private"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  pg.evaluate("""(()=>{const t=document.querySelector('article.post .pbody .txt');const w=document.createTreeWalker(t,NodeFilter.SHOW_TEXT);let n=w.nextNode();const r=document.createRange();r.setStart(n,0);r.setEnd(n,9);getSelection().removeAllRanges();getSelection().addRange(r)})()""")
  pg.wait_for_timeout(600);pg.click('.selbar [data-sl="line"]');pg.wait_for_timeout(200)
  pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  # 방문자: 돌아보기 탭 없음
  pg.locator('.pc-nav [data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('[data-pc="preview"]').click();pg.wait_for_timeout(400)
  pg.evaluate("1");
  r=pg.evaluate("(()=>{return 1})()")
  # 방문자로 전체 글 화면 열기
  btn=pg.locator('[data-act="findPosts"]:visible')
  if btn.count():btn.first.click()
  else:pg.evaluate("document.querySelector('[data-pn=\"me\"]').click()")
  pg.wait_for_timeout(300)
  ok('visitor: no lines/words/look tabs',pg.locator('[data-pv="lines"],[data-pv="words"],[data-pv="look"]').count()==0)
  ok('visitor: private sentence not shown','비밀 문장' not in pg.locator('#desk').inner_text())
  # 주인으로 돌아오기
  pg.evaluate("document.querySelector('[data-exit-visitor],[data-act=\"exitVisitor\"]')&&document.querySelector('[data-exit-visitor],[data-act=\"exitVisitor\"]').click()")
  pg.wait_for_timeout(300)
  if pg.locator('text=미리 보기 끝내기').count():pg.locator('text=미리 보기 끝내기').first.click();pg.wait_for_timeout(300)
  # 원자 저장: assets 쓰기가 실패하면 records도 그대로
  before=pg.evaluate("localStorage.getItem('mgd2.v1.records')")
  pg.evaluate("""(()=>{const o=Storage.prototype.setItem;window.__o=o;Storage.prototype.setItem=function(k,v){if(k==='mgd2.v1.assets'){const e=new Error('q');e.name='QuotaExceededError';throw e}return o.call(this,k,v)}})()""")
  pg.locator('text=글쓰기').first.click();pg.wait_for_timeout(300);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type('실패할 글')
  pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  after=pg.evaluate("localStorage.getItem('mgd2.v1.records')")
  ok('atomic: records unchanged when assets write fails',before==after)
  pg.evaluate("(()=>{Storage.prototype.setItem=window.__o})()");pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  for _ in range(2):
    if pg.locator('.dialog [data-d]').count():pg.locator('.dialog [data-d]').click();pg.wait_for_timeout(200)
  # 편집: 패널 '적용' 후 위 '취소' → 편집 전으로
  pg.locator('.pc-nav [data-pn="room"]').click();pg.wait_for_timeout(300);pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(200)
  n0=pg.locator('.rm-it').count();pg.locator('[data-se-add]').click();pg.wait_for_timeout(150)
  ok('code box under 고급 at bottom',pg.get_by_role('menuitem',name='고급 · 코드 상자').count()==1)
  pg.get_by_role('menuitem',name='전광판').click();pg.wait_for_timeout(300)
  ok('panel button says 적용',pg.locator('[data-se-pok]').inner_text().strip()=='적용')
  pg.click('[data-se-pok]');pg.wait_for_timeout(300);pg.click('.se-bar [data-se-cancel]');pg.wait_for_timeout(400)
  ok(f'top cancel returns to edit start ({n0} -> {pg.locator(".rm-it").count()})',pg.locator('.rm-it').count()==n0)
  # 글 · 사진 · 문장 놓기 (원래 고르기 창)
  pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(200);pg.locator('[data-se-add]').click();pg.get_by_role('menuitem',name='글 · 사진 · 문장 놓기').click();pg.wait_for_timeout(300)
  ok('place picker is original (not 함께 읽기 picker)',pg.locator('#pk-q').count()==0 and pg.locator('.dialog,.scrim').count()>=1)
  pg.keyboard.press('Escape');pg.wait_for_timeout(200);pg.click('.se-bar [data-se-cancel]');pg.wait_for_timeout(300)
  # 단어장 뜻 보기 없음
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='전체 글').click();pg.wait_for_timeout(300);pg.click('[data-pv="words"]');pg.wait_for_timeout(200)
  ok('no 뜻 보기 / dev text',('뜻 보기' not in pg.locator('#desk').inner_text()) and ('이용 조건' not in pg.locator('#desk').inner_text()))
  # 백업
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='백업 · 내보내기').click();pg.wait_for_timeout(300)
  with pg.expect_download() as dl:pg.click('.dialog [data-ex]')
  path=dl.value.path();data=json.load(open(path));ok('export has posts+assets',data['app']=='mugadang' and len(data['records']['posts'])>=1 and 'assets' in data)
  pg.click('.dialog [data-c]');pg.wait_for_timeout(200)
  # 글 하나 더 쓰고, 백업으로 되살리면 사라져야
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='글쓰기').click();pg.wait_for_timeout(300);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type('백업 뒤에 쓴 글');pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
  pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  n_before=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.length")
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='백업 · 내보내기').click();pg.wait_for_timeout(300)
  pg.set_input_files('.dialog [data-im]',path);pg.wait_for_timeout(400);pg.locator('[data-bk-go]').click();pg.wait_for_timeout(500)
  n_after=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.length")
  ok(f'restore from backup ({n_before} -> {n_after})',n_after==n_before-1)
  print('ERR',errs)
