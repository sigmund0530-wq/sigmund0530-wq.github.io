import http.server, threading, functools,sys
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8820),functools.partial(Q,directory='site'));threading.Thread(target=srv.serve_forever,daemon=True).start()
U='http://127.0.0.1:8820/app.html'
def setup(b,mob,dark=False):
  ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},color_scheme='dark' if dark else 'light',has_touch=mob)
  pg=ctx.new_page();pg.set_default_timeout(5000);pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(600);pg.locator('[data-au-social="kakao"]').click();pg.wait_for_timeout(150);pg.locator('[data-au-all]').check();pg.wait_for_timeout(100);pg.locator('[data-au-next]').click();pg.wait_for_timeout(200);pg.locator('#ob-handle').fill('haru');pg.locator('[data-au-make]').click();pg.wait_for_timeout(250);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(250);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(300)
  return pg
def closeall(pg):
  for _ in range(3):
    if pg.locator('.win .back:visible,.win .x:visible').count():pg.locator('.win .back:visible,.win .x:visible').first.click();pg.wait_for_timeout(150)
def write(pg,mob,title,txt,ph=None,vis='public'):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
  pg.locator('input[id^="f-title-"]').fill(title);pg.locator('.blocks .rte-area').first.click();pg.keyboard.type(txt)
  if ph:pg.locator('input[id^="f-ins-"]').set_input_files(ph);pg.wait_for_timeout(1000)
  pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator(f'input[name="pv"][value="{vis}"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
