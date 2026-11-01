# 짤: 붙여넣기 → 사진(움직이는 GIF 그대로) · 내 짤 모음 · 짤 칸(내 짤/GIF/한국 짤) · 서버 거쳐 찾기 · 키 없을 때 · 로그인 전
from base import *
import json,base64
U2='http://127.0.0.1:8820/app_sb.html'
W='https://mugadang-ai.sigmund0530.workers.dev/**'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
GIF=open('zz.gif','rb').read();PNG=open('zz.png','rb').read()
calls=[];keyless=[False]
def fake(route):
  r=route.request;path=r.url.split('workers.dev',1)[1];body=json.loads(r.post_data or '{}');calls.append((path,body,r.headers.get('authorization','')))
  H={'Access-Control-Allow-Origin':'*'}
  if path=='/zzal/search':
    if keyless[0]:return route.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'items':[],'need':'key'}))
    its=[{'id':f'{body["src"]}{i}','thumb':f'https://img.example/t{i}.png','full':f'https://img.example/f{i}.gif','w':60,'h':40,'title':f'헐 {i}'} for i in range(5)]
    return route.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'items':its,'more':False}))
  if path=='/zzal/img':
    g=body['u'].endswith('.gif');return route.fulfill(status=200,headers=H,content_type='image/gif' if g else 'image/png',body=GIF if g else PNG)
  route.fulfill(status=404,body='')
PASTE="""async([b64,type])=>{const bin=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const f=new File([bin],'x.'+type.split('/')[1],{type});
  const dt=new DataTransfer();dt.items.add(f);const a=document.querySelector('.blocks .rte-area');a.focus();
  a.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}"""
def photos(pg):return pg.evaluate("[...document.querySelectorAll('.blocks img')].map(i=>i.getAttribute('src')||'').filter(s=>s).length")
def openw(pg,mob):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400)
  pg.locator('input[id^="f-title-"]').fill('짤 글');pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('오늘 퇴근길 ')
def signup(pg,h):
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',h+'@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle',h);pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
with sync_playwright() as p:
  b=p.chromium.launch()
  # 1) 브라우저 저장(서버 없음): 붙여넣기 · 내 짤
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs;openw(pg,mob)
    ok(pg.locator('[data-x-zzal]').count()==1,tag+' 도구줄에 짤 버튼')
    n0=photos(pg);pg.evaluate(PASTE,[base64.b64encode(GIF).decode(),'image/gif']);pg.wait_for_timeout(700)
    ok(photos(pg)==n0+1,tag+' 그림 붙여넣기 → 사진으로 들어감')
    ok('오늘 퇴근길' in pg.locator('.blocks').inner_text(),tag+' 쓰던 글은 그대로')
    a=pg.evaluate("(()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));const as=JSON.parse(localStorage.getItem('mgd2.v1.assets'));const z=(r.zzal||[])[0];return z?{mime:as[z.id]&&as[z.id].mime,n:r.zzal.length}:null})()")
    ok(a and a['mime']=='image/gif' and a['n']==1,tag+' 내 짤에 모이고 GIF는 움직이는 그대로',a)
    pg.locator('[data-x-zzal]').click();pg.wait_for_timeout(300)
    ok(pg.locator('.zz-pan').count()==1 and pg.locator('[data-zt="mine"][aria-selected="true"]').count()==1,tag+' 짤 칸: 내 짤이 먼저')
    ok(pg.locator('.zz-it[data-mine]').count()==1,tag+' 내 짤 1개')
    pg.locator('[data-zt="gif"]').click();pg.wait_for_timeout(200);ok('로그인' in pg.locator('.zz-grid').inner_text(),tag+' 서버 없으면 검색 대신 안내')
    pg.locator('[data-zt="mine"]').click();pg.wait_for_timeout(200);pg.locator('.zz-it[data-mine]').click();pg.wait_for_timeout(500)
    ok(photos(pg)==n0+2 and pg.locator('.zz-pan').count()==0,tag+' 내 짤 누르면 들어가고 칸 닫힘')
    ok(len(pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('mgd2.v1.assets')))"))==1,tag+' 같은 짤은 파일을 새로 안 만듦')
    pg.keyboard.press('Control+v') if False else None
    pg.locator('[data-x-zzal]').click();pg.wait_for_timeout(200);pg.mouse.click(5,5) if not mob else pg.touchscreen.tap(380,120);pg.wait_for_timeout(200)
    ok(pg.locator('.zz-pan').count()==0,tag+' 바깥 누르면 닫힘')
    ok(not errs,tag+' ERR',errs);pg.context.close()
  # 2) 가짜 서버 + 가짜 Worker: GIF·한국 짤 검색
  for mob in (False,True):
    tag='M' if mob else 'PC';calls.clear();keyless[0]=False
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    ctx.route(W,fake);signup(pg,'zz'+tag.lower());openw(pg,mob)
    pg.locator('[data-x-zzal]').click();pg.wait_for_timeout(800)
    ok(pg.locator('[data-zt="gif"][aria-selected="true"]').count()==1,tag+' 모은 짤이 없으면 GIF부터')
    ok(any(c[0]=='/zzal/search' and c[1]['src']=='gif' and c[1]['q']=='' for c in calls),tag+' 처음엔 요즘 GIF')
    ok(all(c[2]=='Bearer mock-token' for c in calls),tag+' 로그인 토큰으로')
    pg.fill('.zz-q','헐');pg.wait_for_timeout(900)
    ok(any(c[0]=='/zzal/search' and c[1]['q']=='헐' for c in calls),tag+' 검색어로 찾음')
    ok(pg.locator('.zz-it img').count()==5,tag+' 썸네일 5개(서버가 대신 받아 옴)',pg.locator('.zz-it img').count())
    ok(all(c[1]['u'].startswith('https://img.example/t') for c in calls if c[0]=='/zzal/img'),tag+' 썸네일도 서버를 거침')
    n0=photos(pg);pg.locator('.zz-it').first.click();pg.wait_for_timeout(800)
    ok(photos(pg)==n0+1,tag+' GIF 골라 넣음');z=rec(pg).get('zzal') or [];ok(len(z)==1 and z[0]['q']=='헐',tag+' 찾은 말로 내 짤에 이름',z)
    pg.locator('[data-x-zzal]').click();pg.wait_for_timeout(300);pg.locator('[data-zt="kr"]').click();pg.wait_for_timeout(300)
    ok('찾을 말' in pg.locator('.zz-grid').inner_text(),tag+' 한국 짤은 말부터')
    pg.fill('.zz-q','킹받네');pg.wait_for_timeout(900);ok(any(c[1].get('src')=='kr' and c[1].get('q')=='킹받네' for c in calls),tag+' 한국 짤 검색')
    pg.locator('[data-zt="mine"]').click();pg.fill('.zz-q','헐');pg.wait_for_timeout(300);ok(pg.locator('.zz-it[data-mine]').count()==1,tag+' 내 짤도 이름으로 찾음')
    pg.locator('.zz-x').click();keyless[0]=True
    pg.locator('[data-x-zzal]').click();pg.wait_for_timeout(200);pg.locator('[data-zt="gif"]').click();pg.wait_for_timeout(600)
    ok('준비' in pg.locator('.zz-grid').inner_text(),tag+' 키가 없으면 준비 중');pg.locator('.zz-x').click()
    pg.locator('.hpub').click();pg.wait_for_timeout(300);pg.locator('input[name="pv"][value="private"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(2500)
    db=pg.evaluate("window.__mock.db");ok(any(m['mime']=='image/gif' for m in db['tables']['media']),tag+' 서버에 GIF로 올라감')
    ok(not errs,tag+' ERR',errs);ctx.close()
