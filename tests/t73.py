# 알아서 모으기 AI(쓰는 중에 찾아 주기): 설정 켜기 → 문장을 마치고 2초 → 점선 제안(본문엔 안 섞임) → 눌러 붙이기 / 아니에요 → 발행엔 기다림 없음
from base import *
import json
U2='http://127.0.0.1:8820/app_sb.html'
AI='https://mugadang-ai.sigmund0530.workers.dev/**'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
calls=[];mode=['ok']
ITEMS=[{'word':'소년이 온다','kind':'책'},{'word':'망원시장','kind':'장소'},{'word':'고로케','kind':'음식'},{'word':'없는말','kind':'물건'}]
def fake(route):
  r=route.request;calls.append({'auth':r.headers.get('authorization',''),'text':json.loads(r.post_data or '{}').get('text','')})
  if mode[0]=='fail':return route.fulfill(status=500,body='x')
  route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'items':[i for i in ITEMS if i['word'] in json.loads(r.post_data)['text']]}))
def opensettings(pg,mob):
  if mob:pg.locator('[data-m-settings]').first.click();pg.wait_for_timeout(200);pg.get_by_text('설정',exact=True).first.click()
  else:pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click()
  pg.wait_for_timeout(300)
def signup(pg,h):
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',h+'@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle',h);pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
def openw(pg,mob,title):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400)
  pg.locator('input[id^="f-title-"]').fill(title);pg.locator('.blocks .rte-area').first.click()
def pub(pg,vis='private'):
  pg.locator('.hpub').click();pg.wait_for_timeout(300);pg.locator(f'input[name="pv"][value="{vis}"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
HL="(()=>{const h=CSS.highlights.get('mgd-ai');return h?[...h].map(r=>r.toString()):[]})()"
def tap(pg,word,mob):
  box=pg.evaluate("w=>{const h=CSS.highlights.get('mgd-ai');const r=[...h].find(r=>r.toString()===w);const b=r.getClientRects()[0];return {x:b.left+b.width/2,y:b.top+b.height/2}}",word)
  if mob:pg.touchscreen.tap(box['x'],box['y'])
  else:pg.mouse.click(box['x'],box['y'])
  pg.wait_for_timeout(300)
with sync_playwright() as p:
  b=p.chromium.launch()
  pg=setup(b,False);opensettings(pg,False)
  ok(pg.locator('.set-ai').count()==1 and pg.locator('[data-ai-toggle]').count()==0,'서버 없으면 안내만');pg.context.close()
  for mob in (False,True):
    tag='M' if mob else 'PC';calls.clear();mode[0]='ok'
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    ctx.route(AI,fake);signup(pg,'ai'+tag.lower())
    openw(pg,mob,'꺼둔 글');pg.keyboard.type('오늘 소년이 온다를 읽었다. ');pg.wait_for_timeout(2600);ok(len(calls)==0,tag+' 꺼 두면 AI 안 부름');pub(pg);closeall(pg)
    opensettings(pg,mob);t=pg.locator('[data-ai-toggle]');ok(t.count()==1 and '꺼짐' in t.inner_text(),tag+' 처음엔 꺼짐')
    ok('학습에 쓰지 않' in pg.locator('.set-ai').inner_text() and '쓰는 중' in pg.locator('.set-ai').inner_text(),tag+' 안내 문구')
    t.click();pg.wait_for_timeout(300);ok(rec(pg)['settings'].get('aiCollect') is True,tag+' 켜기 저장')
    closeall(pg);pg.go_back();pg.wait_for_timeout(300)
    openw(pg,mob,'켠 글');pg.keyboard.type('오늘 소년이 온다를 다시 읽었')
    pg.wait_for_timeout(2600);ok(len(calls)==0,tag+' 문장을 마치기 전엔 안 부름')
    pg.keyboard.type('다. 오후엔 망원시장에서 고로케를 샀다. 그리고');pg.wait_for_timeout(1200);ok(len(calls)==0,tag+' 2초 전엔 안 부름')
    pg.wait_for_timeout(1500);ok(len(calls)==1 and calls[0]['auth']=='Bearer mock-token',tag+' 2초 쉬면 로그인 토큰으로 부름')
    ok(len(calls)==1 and '망원시장' in calls[0]['text'] and '그리고' not in calls[0]['text'],tag+' 다 쓴 문장만 보냄',calls[:1])
    pg.wait_for_timeout(300);hl=pg.evaluate(HL);ok(sorted(hl)==sorted(['소년이 온다','망원시장','고로케']),tag+' 점선 제안 3개(글에 없는 말 버림)',hl)
    ok(pg.locator('.rte-area mark').count()==0,tag+' 제안은 본문에 안 섞임')
    pg.keyboard.type(' 잤다.');pg.wait_for_timeout(2600);ok(len(calls)==2 and '소년' not in calls[1]['text'],tag+' 보낸 문장은 다시 안 보냄',calls[1:])
    tap(pg,'소년이 온다',mob);ok(pg.locator('.ai-pop').count()==1 and '읽은 책에 붙이기' in pg.locator('.ai-pop').inner_text(),tag+' 누르면 붙이기 메뉴')
    pg.locator('.ai-pop [data-k=yes]').click();pg.wait_for_timeout(300)
    ok(pg.locator('.rte-area mark[data-pf]').all_text_contents()==['소년이 온다'],tag+' 붙음');ok(sorted(pg.evaluate(HL))==['고로케','망원시장'],tag+' 붙인 건 제안에서 빠짐')
    tap(pg,'고로케',mob);pg.locator('.ai-pop [data-k=no]').click();pg.wait_for_timeout(300);ok(pg.evaluate(HL)==['망원시장'],tag+' 아니에요 → 사라짐')
    n=len(calls);pub(pg);ok(len(calls)==n,tag+' 발행 땐 안 부름')
    post=[x for x in rec(pg)['posts'] if x.get('title')=='켠 글'][0];ok([g['name'] for g in post.get('functions') or []]==['독서 기록'],tag+' 고른 것만 저장',[g['name'] for g in post.get('functions') or []])
    ok(json.dumps(post.get('bodyJson'),ensure_ascii=False).count('data-pf')==1 and post.get('status')=='published',tag+' 발행됨·표시 1개')
    closeall(pg);pg.wait_for_timeout(200);ok(pg.evaluate(HL)==[],tag+' 창 닫으면 점선 없음')
    mode[0]='fail';openw(pg,mob,'실패 글');pg.keyboard.type('책방에서 소년이 온다를 샀다.');pg.wait_for_timeout(2700)
    ok(pg.evaluate(HL)==[],tag+' AI 실패면 조용히');pub(pg);post=[x for x in rec(pg)['posts'] if x.get('title')=='실패 글'];ok(post and post[0].get('status')=='published',tag+' 실패해도 발행')
    ok(not errs,tag+' ERR',errs);ctx.close()
