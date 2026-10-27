from base import *
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':860});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300)
  for vis,txt in [('public','공개글입니다 하나'),('private','나만글입니다 둘'),('close','가까운글입니다 셋'),('followers','팔로워글입니다 넷')]:
    pg.locator('text=글쓰기').first.click();pg.wait_for_timeout(300);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type(txt)
    pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250)
    if vis=='public':ok('no feed checkbox',pg.locator('#pv-feed').count()==0);ok('note shown',pg.locator('.po-feednote').count()==1);pg.screenshot(path='feedall_dialog.png')
    pg.locator(f'.dialog input[value="{vis}"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
    pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  pg.locator('[data-pn="feed"]').click();pg.wait_for_timeout(300);pg.locator('[data-pc-feed]:not([data-pc-feed="following"])').click();pg.wait_for_timeout(400)
  for _ in range(6):
    if pg.locator('[data-act="feedMore"]').count():pg.locator('[data-act="feedMore"]').click();pg.wait_for_timeout(200)
  t=pg.locator('.fmain').inner_text()
  ok('public in random feed','공개글입니다' in t);ok('private not','나만글입니다' not in t);ok('close not','가까운글입니다' not in t);ok('followers not','팔로워글입니다' not in t)
  print('ERR',errs)
