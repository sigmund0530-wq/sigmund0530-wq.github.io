# 위젯 인터넷(2026-11-02): 무가당 중계 mugadang.fetch · 적은 주소만 직접 연결 · 안 적은 주소는 막힘 · 로그인 전엔 안 됨
import json
from base import *
U2='http://127.0.0.1:8820/app_sb.html'
W='https://mugadang-ai.sigmund0530.workers.dev/**'
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
calls=[];direct=[]
def fake(route):
  r=route.request;path=r.url.split('workers.dev',1)[1];body=json.loads(r.post_data or '{}');calls.append((path,body,r.headers.get('authorization','')))
  H={'Access-Control-Allow-Origin':'*'}
  if path=='/relay':return route.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'status':200,'type':'application/json','body':json.dumps({'temp':'맑음 21도','u':body['u']})}))
  route.fulfill(status=404,body='')
def site(route):
  direct.append(route.request.url);route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body='{"room":"놀이방"}')
WIDGET="""<body style="font:14px system-ui"><div id=a>…</div><div id=b>…</div><div id=c>…</div><script>
mugadang.fetch('https://weather.example/today').then(r=>{a.textContent='relay:'+JSON.parse(r.body).temp}).catch(e=>{a.textContent='relay-err:'+e.message});
fetch('https://api.mygame.example/room').then(r=>r.json()).then(j=>{b.textContent='direct:'+j.room}).catch(()=>{b.textContent='direct:blocked'});
fetch('https://evil.example/steal').then(()=>{c.textContent='other:open'}).catch(()=>{c.textContent='other:blocked'});
</script></body>"""
def signup(pg,h):
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',h+'@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle',h);pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
def upload(pg,net):
  pg.locator('[data-pn="feed"]').click();pg.wait_for_timeout(300);pg.locator('[data-feed-kind="widget"]').click();pg.wait_for_timeout(300)
  pg.locator('[data-wf-add]').click();pg.locator('[data-wt="paste"]').click();pg.locator('#wf-code').fill(WIDGET);pg.locator('#wf-title').fill('날씨와 놀이방')
  pg.locator('#wf-net').fill(net);pg.wait_for_timeout(300)
def frame_text(pg,sel):
  fr=pg.frame_locator(sel);return {k:fr.locator('#'+k).inner_text() for k in 'abc'}
with sync_playwright() as p:
  b=p.chromium.launch()
  # 1) 서버에 로그인한 사람
  ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  ctx.route(W,fake);ctx.route('https://api.mygame.example/**',site);ctx.route('https://evil.example/**',site)
  pg.goto(U2);pg.evaluate("localStorage.clear()");signup(pg,'netuser')
  upload(pg,'https://api.mygame.example/room, 이상한 주소, 127.0.0.1')
  ok('보는 사람에게 처음 실행할 때 물어봐요' in pg.locator('.wf-modal').inner_text(),'올리기: 직접 연결 칸과 안내')
  ok('mugadang.fetch' in pg.locator('.wf-help').inner_text(),'AI에게 부탁하는 문구에 mugadang.fetch')
  pg.locator('.wf-modal [data-o]').click();pg.wait_for_timeout(800)
  w=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).widgets[0]")
  ok(w.get('net')==['api.mygame.example'],'적은 주소 중 올바른 것만 저장(IP·이상한 말은 버림)',w.get('net'))
  ok('인터넷 연결' in pg.locator('.wf-card').first.inner_text(),'카드에 인터넷 연결 표시')
  pg.locator('.wf-card').first.locator('.wf-frame').hover();pg.wait_for_timeout(2500)
  t=frame_text(pg,'.wf-card >> nth=0 >> iframe.wf-live');print(t)
  ok(t['a']=='relay:맑음 21도','무가당 중계로 가져오기')
  ok(any(c[0]=='/relay' and c[1]['u']=='https://weather.example/today' and c[2].startswith('Bearer ') for c in calls),'중계는 로그인 토큰과 함께 무가당 서버로')
  ok(t['b']=='direct:놀이방','적은 주소는 직접 연결')
  ok(t['c']=='other:blocked' and not any('evil.example' in u for u in direct),'안 적은 주소는 막힘')
  src=pg.locator('iframe.wf-live').first.get_attribute('srcdoc');ok("connect-src https://api.mygame.example wss://api.mygame.example" in src and pg.locator('iframe.wf-live').first.get_attribute('sandbox')=='allow-scripts','격리 상자는 그대로, 적은 주소만 열림')
  ok(not errs,'ERR',errs);ctx.close()
  # 2) 서버 없는 미리보기: 중계는 안 되고 안내
  pg=setup(b,False);errs=pg.errs
  pg.locator('[data-pn="feed"]').click();pg.wait_for_timeout(300);pg.locator('[data-feed-kind="widget"]').click();pg.wait_for_timeout(300)
  pg.locator('[data-wf-add]').click();pg.locator('[data-wt="paste"]').click();pg.locator('#wf-code').fill(WIDGET);pg.locator('#wf-title').fill('미리보기');pg.wait_for_timeout(1500)
  t=frame_text(pg,'.wf-pv-box[data-pv="p"] iframe');print(t)
  ok(t['a'].startswith('relay-err:') and '가입' in t['a'],'미리보기: 중계는 가입한 사람에게만(안내)')
  ok(t['b']=='direct:blocked','주소를 안 적으면 직접 연결도 막힘')
  ok(not errs,'ERR2',errs)
print('fails',fails)
