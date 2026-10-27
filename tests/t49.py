import shutil,sys
from base import *
APP=sys.argv[1] if len(sys.argv)>1 else '../src/app.html'
shutil.copy(APP,'site/app.html')
CHECK="""(()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));const a=JSON.parse(localStorage.getItem('mgd2.v1.assets')||'{}');
 const ref=[];r.posts.forEach(p=>(p.bodyJson?.blocks||[]).forEach(b=>{if(b.type==='photos')b.items.forEach(x=>ref.push(x.assetId))}));
 const missing=ref.filter(id=>!a[id]);return {posts:r.posts.length,refs:ref.length,missing:missing.length}})()"""
def fresh(b):
  ctx=b.new_context(viewport={'width':1280,'height':860});pg=ctx.new_page();pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300);return pg
def write(pg,txt):
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='글쓰기').click();pg.wait_for_timeout(300)
  pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type(txt);pg.set_input_files('.win.editor input[id^="f-ins"]','p1.jpg');pg.wait_for_timeout(500)
  pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
with sync_playwright() as p:
  b=p.chromium.launch()
  for step in [0,1,2]:
    pg=fresh(b);pg.evaluate(f"window.__mgdCrashAt={step}");write(pg,'사진 글');pg.evaluate("delete window.__mgdCrashAt")
    pg.reload();pg.wait_for_timeout(700);r=pg.evaluate(CHECK);print(f'추가 중 {step+1}번째 쓰기에서 꺼짐 →',r,'깨진 참조 없음' if r['missing']==0 else '❌ 사진 없는 글','ERR',pg.errs);pg.context.close()
  for step in [0,1,2]:
    pg=fresh(b);write(pg,'지울 글');pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
    pg.evaluate(f"window.__mgdCrashAt={step}")
    pid=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts[0].id")
    pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='전체 글').click();pg.wait_for_timeout(300);pg.locator(f'[data-open-post="{pid}"]').first.click();pg.wait_for_timeout(300)
    pg.locator(f'[data-act="deletePost"][data-post="{pid}"]').click();pg.wait_for_timeout(250)
    if pg.locator('.dialog .btn.danger, .dialog [data-o]').count():pg.locator('.dialog .btn.danger, .dialog [data-o]').last.click();pg.wait_for_timeout(400)
    pg.evaluate("delete window.__mgdCrashAt");pg.reload();pg.wait_for_timeout(700);r=pg.evaluate(CHECK)
    print(f'삭제 중 {step+1}번째 쓰기에서 꺼짐 →',r,'깨진 참조 없음' if r['missing']==0 else '❌ 사진 없는 글','ERR',pg.errs);pg.context.close()
