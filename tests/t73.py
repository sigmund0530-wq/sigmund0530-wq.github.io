# 알아서 모으기 AI: 설정에서 켜기 → 발행할 때 AI가 글 속 단어에 붙임 → 모아 보기 · 빼기 · 꺼 두면 안 부름 · 실패해도 발행
from base import *
import json
U2='http://127.0.0.1:8820/app_sb.html'
AI='https://mugadang-ai.sigmund0530.workers.dev/**'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
calls=[]
def fake(route):
  r=route.request;calls.append({'auth':r.headers.get('authorization',''),'body':r.post_data})
  if mode[0]=='fail':return route.fulfill(status=500,body='x')
  route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'items':[{'word':'소년이 온다','kind':'책'},{'word':'망원시장','kind':'장소'},{'word':'고로케','kind':'음식'},{'word':'없는말','kind':'물건'}]}))
mode=['ok']
def opensettings(pg,mob):
  if mob:pg.locator('[data-m-settings]').first.click();pg.wait_for_timeout(200);pg.get_by_text('설정',exact=True).first.click()
  else:pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click()
  pg.wait_for_timeout(300)
def signup(pg,h):
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',h+'@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle',h);pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
TXT='오늘 소년이 온다를 다시 읽었다. 오후엔 망원시장에서 고로케를 샀다.'
with sync_playwright() as p:
  b=p.chromium.launch()
  # 0) 브라우저 저장(서버 없음): 설정에 켜기 버튼 없음
  pg=setup(b,False);opensettings(pg,False)
  ok(pg.locator('.set-ai').count()==1 and pg.locator('[data-ai-toggle]').count()==0,'서버 없으면 안내만')
  pg.context.close()
  for mob in (False,True):
    tag='M' if mob else 'PC';calls.clear();mode[0]='ok'
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    ctx.route(AI,fake);signup(pg,'ai'+tag.lower())
    # 꺼져 있으면 부르지 않음
    write(pg,mob,'꺼둔 글',TXT);pg.wait_for_timeout(500);closeall(pg)
    ok(len(calls)==0,tag+' 꺼 두면 AI 안 부름')
    opensettings(pg,mob);t=pg.locator('[data-ai-toggle]');ok(t.count()==1 and '꺼짐' in t.inner_text(),tag+' 처음엔 꺼짐')
    ok('학습에 쓰지 않' in pg.locator('.set-ai').inner_text(),tag+' 안내 문구')
    t.click();pg.wait_for_timeout(300);ok(rec(pg)['settings'].get('aiCollect') is True,tag+' 켜기 저장');ok('켜짐' in pg.locator('[data-ai-toggle]').inner_text(),tag+' 켜짐 표시')
    closeall(pg);pg.go_back();pg.wait_for_timeout(300)
    write(pg,mob,'켠 글',TXT);pg.wait_for_timeout(600)
    ok(len(calls)==1 and calls[0]['auth']=='Bearer mock-token',tag+' 로그인 토큰으로 부름',calls[:1])
    ok(len(calls)==1 and '망원시장' in json.loads(calls[0]['body'])['text'],tag+' 본문을 보냄')
    post=[x for x in rec(pg)['posts'] if x.get('title')=='켠 글'][0];fs=post.get('functions') or []
    names=sorted(g['name'] for g in fs);ok(names==sorted(['독서 기록','맛집·카페','먹은 것']),tag+' 세 개 붙음(글에 없는 말은 버림)',names)
    html=json.dumps(post.get('bodyJson'),ensure_ascii=False);ok(html.count('data-pf')==3,tag+' 단어 표시 3개')
    ok(post.get('status')=='published',tag+' 발행됨')
    closeall(pg)
    # 실패해도 발행
    mode[0]='fail';n=len(calls);write(pg,mob,'실패 글','책방에서 아몬드를 샀다.');pg.wait_for_timeout(600)
    post=[x for x in rec(pg)['posts'] if x.get('title')=='실패 글'];ok(post and post[0].get('status')=='published' and not post[0].get('functions'),tag+' AI 실패해도 그냥 발행')
    ok(len(calls)==n+1,tag+' 실패 때도 한 번만 부름')
    ok(not errs,tag+' ERR',errs);ctx.close()
