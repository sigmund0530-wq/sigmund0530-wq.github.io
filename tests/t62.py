from base import *
exec(open('t60.py').read().split('with sync_playwright')[0].split('from base import *')[1])
with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U2);pg.wait_for_timeout(600);pg.screenshot(path='sb_start.png')
  signup(pg,'a@x.com','haru','MUGADANG-BETA');write(pg,False,'첫','하나');pg.wait_for_timeout(2000)
  # 설정 메뉴: 의견 보내기
  g=pg.locator('[data-pn="menu"]')
  print('gear',g.count())
  if g.count():
    g.click();pg.wait_for_timeout(200);pg.screenshot(path='sb_menu.png');
    pg.get_by_role('menuitem',name='설정').click();pg.wait_for_timeout(300);pg.locator('[data-set="feedback"]').click();pg.wait_for_timeout(200);pg.fill('#fb-t','사진 옮기기 좋아요');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
    ok(len(db(pg)['tables']['feedback'])==1,'의견 저장')
  pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200)
  pg.locator('[data-pc="logout"]').click();pg.wait_for_timeout(800)
  keys=pg.evaluate("Object.keys(localStorage)");ok(pg.locator('#au-lmail').count()==1,'로그아웃 → 로그인 화면');ok(not any(k.startswith('mgd2.v1.') and 'feedRead' not in k for k in keys),'이 기기 사본 지움',keys)
  pg.screenshot(path='sb_login.png')
  pg.fill('#au-lmail','a@x.com');pg.fill('#au-lpw','password123');pg.locator('[data-au-login]').click();pg.wait_for_timeout(1500)
  ok(pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.length")==1,'다시 로그인하면 글 돌아옴')
  ok(not errs,'ERR',errs);b.close()
