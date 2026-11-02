# 다른 사람 불러오기 + 쪽지 (2026-11-02): 가짜 서버(mocksb.js)로 두 사람이 번갈아 들어옴
import json
from base import *
U2='http://127.0.0.1:8820/app_sb.html'
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
def db(pg):return pg.evaluate("window.__mock.db")
def signup(pg,mail,handle,name):
  pg.goto(U2);pg.wait_for_timeout(700);pg.locator('[data-au-method="email"]').click();pg.wait_for_timeout(150)
  pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',mail);pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','바다');pg.fill('#ob-name',name);pg.fill('#ob-handle',handle)
  pg.fill('#au-invite','MUGADANG-BETA');pg.locator('[data-au-make]').click();pg.wait_for_timeout(600)
  pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(600);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(2000)
def logout(pg):
  pg.evaluate("localStorage.removeItem('mocksess');Object.keys(localStorage).filter(k=>k.startsWith('mgd2.')).forEach(k=>localStorage.removeItem(k))")
def login(pg,mail):
  pg.goto(U2);pg.wait_for_timeout(700)
  if pg.locator('#au-lmail').count()==0:
    b=pg.locator('[data-au-go="login"]')
    if b.count():b.first.click();pg.wait_for_timeout(200)
  pg.fill('#au-lmail',mail);pg.fill('#au-lpw','password123');pg.locator('[data-au-login]').click();pg.wait_for_timeout(1800)
def post(pg,title,txt,vis,ph=None):
  pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
  pg.locator('input[id^="f-title-"]').fill(title);pg.locator('.blocks .rte-area').first.click();pg.keyboard.type(txt)
  if ph:pg.locator('input[id^="f-ins-"]').set_input_files(ph);pg.wait_for_timeout(900)
  pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator(f'input[name="pv"][value="{vis}"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  closeall(pg)
with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  # ── 하루: 전체 공개 글 + 이웃 공개 글 ──
  pg.goto(U2);pg.wait_for_timeout(300);pg.evaluate("localStorage.clear()")
  signup(pg,'haru@x.com','haru','하루')
  post(pg,'망원시장 산책','오늘은 고로케를 샀다','public','p1.jpg')
  post(pg,'이웃에게만','가까운 이야기','followers')
  pg.wait_for_timeout(2500)
  d=db(pg);ok(len([x for x in d['tables']['posts'] if x['status']=='published'])==2,'하루 글 둘이 서버에')
  haru=d['tables']['profiles'][0]['id']
  # 나쁜 마음을 먹은 사람이 서버에 직접 넣은 글·배치(화면에서 걸러져야 함)
  pg.evaluate("""()=>{const d=window.__mock.db;const p=d.tables.posts.find(x=>x.data.title==='망원시장 산책');
    p.data.bodyJson.blocks.unshift({id:'bx',type:'text',html:'<img src=x onerror="window.__xss=1"><p>나쁜 글</p>'});p.data.title='망원시장 산책';
    p.data.functions=[{id:'f\\"x',name:'\\"><img src=x onerror=window.__xss=2>',fields:[]}];
    const r=d.tables.rooms[0];r.layout=r.layout||{};if(r.layout.pages)r.layout.pages[0].background={type:'color',value:'red;background:url(https://evil.example/t)'};r.layout.spaceCss='body{display:none}';
    localStorage.setItem('mockdb',JSON.stringify(d))}""")
  logout(pg)
  # ── 민지: 가입 → 피드에서 하루 글 → 쪽지 ──
  signup(pg,'minji@x.com','minji','민지')
  pg.locator('.pc-nav [data-pn="feed"]').click();pg.wait_for_timeout(1500)
  ok('망원시장 산책' not in pg.locator('#canvas').inner_text(),'이웃새글: 아직 이웃이 없으니 안 보임')
  pg.get_by_role('tab',name='무작위').first.click();pg.wait_for_timeout(1500)
  body=pg.locator('#canvas').inner_text()
  ok('망원시장 산책' in body,'피드에 다른 사람의 전체 공개 글');ok('이웃에게만' not in body,'이웃 공개 글은 아직 안 보임');ok('소금빵' not in body,'실제 사이트에선 예시 사용자 없음')
  pg.get_by_text('망원시장 산책').first.click();pg.wait_for_timeout(1200)
  ok(pg.locator('.win .pbody, .win article.post').count()>=1 and '고로케' in pg.locator('.win').last.inner_text(),'남의 글이 열림')
  ok(pg.locator('.win img[src^="data:"]').count()>=1,'남의 글 사진도 보임')
  ok(pg.evaluate("!window.__xss&&!document.querySelector('[onerror]')"),'남이 넣은 위험한 코드는 실행되지 않음')
  pg.screenshot(path='/tmp/claude-0/-home-claude/fe12ee13-bf85-5576-8b7d-bee9a6244b11/scratchpad/peerpost.png');print(pg.evaluate("(()=>{const b=document.querySelector('.win [data-note-kind=post]');if(!b)return 'none';const r=b.getBoundingClientRect();return [r.x,r.y,r.width,r.height,getComputedStyle(b).display,b.closest('.win').className, document.querySelectorAll('.win').length]})()"))
  pg.locator('.win [data-note-kind="post"]').click();pg.wait_for_timeout(800)
  ok(pg.locator('.nt-page').count()==1 and '망원시장 산책' in pg.locator('.nt-ctx-chip').inner_text(),'글에서 쪽지 쓰기 → 맥락이 붙음')
  pg.fill('#nt-text','고로케 어디서 샀어요?');pg.locator('.nt-write [type=submit]').click();pg.wait_for_timeout(300);pg.wait_for_timeout(600)
  n=db(pg)['tables']['notes'];ok(len(n)==1 and n[0]['ctx'].get('title')=='망원시장 산책' and n[0]['recipient']==haru,'쪽지가 서버에(맥락 포함)')
  ok(pg.locator('.nt-letter.mine').count()==1,'편지첩에 내 쪽지');pg.screenshot(path='nt_pc_sent.png')
  ok(pg.locator('.nt-gate').count()==1 and pg.locator('.nt-write').count()==0,'답장 전엔 두 번째를 못 씀(안내)')
  ok('읽' not in (pg.locator('.nt-letter.mine').inner_text()),'읽음 표시 없음')
  # 하루 공간 → 이웃 맺기 → 이웃 공개 글이 보임
  pg.locator('.nt-th-h [data-act="authorSpace"]').click();pg.wait_for_timeout(1500)
  w=pg.locator('.win').last;ok('하루' in w.inner_text() and w.locator('.fl-canvas').count()==1,'남의 공간: 자유 배치 그대로')
  ok(w.locator('.fl-h,.fl-tb').count()==0 and pg.locator('.se-bar').count()==0,'남의 공간엔 편집 손잡이 없음')
  ok(pg.evaluate("!window.__xss&&!document.querySelector('[onerror]')&&!document.documentElement.innerHTML.includes('evil.example')&&getComputedStyle(document.body).display!=='none'"),'남의 배경·공간 CSS로 화면을 건드릴 수 없음')
  pg.screenshot(path='peer_space.png');w.locator('[data-act="follow"]').click();pg.wait_for_timeout(1500)
  ok(any(f['followee']==haru for f in db(pg)['tables']['follows']),'이웃 맺기 → 서버 follows')
  w=pg.locator('.win').last;ok('이웃에게만' in w.inner_text(),'이웃이 되면 이웃 공개 글이 보임')
  ok(json.loads(pg.evaluate("localStorage.getItem('mgd2.v1.records')"))['profile']['displayName']=='민지','남의 공간을 봐도 내 기록은 그대로')
  minji=[x for x in db(pg)['tables']['profiles'] if x['handle']=='minji'][0]['id']
  closeall(pg);logout(pg)
  # ── 하루: 새 쪽지 점 → 처음 온 쪽지 → 답장 ──
  login(pg,'haru@x.com');pg.wait_for_timeout(800)
  ok(pg.locator('.pn-note.has-new').count()==1,'새 쪽지는 점 하나(숫자 없음)')
  pg.locator('.pn-note').click();pg.wait_for_timeout(900)
  ok('처음 온 쪽지' in pg.locator('.nt-page').inner_text(),'이웃 아닌 사람의 첫 쪽지는 따로')
  pg.locator(f'.nt-row[data-nt-with="{minji}"]').click();pg.wait_for_timeout(500)
  ok('망원시장 산책' in pg.locator('.nt-letter').first.inner_text(),'어디서 보고 보냈는지 보임')
  pg.fill('#nt-text','시장 입구 두 번째 집이요');pg.locator('.nt-write [type=submit]').click();pg.wait_for_timeout(900)
  ok(len(db(pg)['tables']['notes'])==2,'답장')
  ok(pg.locator('.pn-note.has-new').count()==0,'열어 보면 점이 사라짐');pg.screenshot(path='nt_pc_thread.png')
  # 받기 범위: 쪽지함의 '쪽지 받기 설정' → 설정 화면
  pg.locator('[data-set-notes]').click();pg.wait_for_timeout(500)
  ok(pg.locator('.set-page [data-note-from]').count()==1,'쪽지함 → 설정의 쪽지 받기')
  pg.locator('[data-note-from]').select_option('none');pg.wait_for_timeout(600)
  ok([x for x in db(pg)['tables']['profiles'] if x['id']==haru][0].get('note_from')=='none','설정: 쪽지 받지 않기 → 서버')
  logout(pg)
  # ── 민지: 답장을 받았지만 하루가 받지 않기로 → 안내 ──
  login(pg,'minji@x.com');pg.wait_for_timeout(800)
  pg.locator('.pn-note').click();pg.wait_for_timeout(900);pg.locator(f'.nt-row[data-nt-with="{haru}"]').click();pg.wait_for_timeout(500)
  ok(pg.locator('.nt-letter').count()==2,'편지첩에 두 통이 날짜순')
  ok('받지 않아요' in pg.locator('.nt-thread').inner_text(),'받지 않기로 한 사람에겐 못 씀(안내)')
  # 검색으로 사람 찾기
  pg.locator('.pc-nav [data-fsrch]').click();pg.wait_for_timeout(300);pg.fill('#srch-q','har');pg.wait_for_timeout(800)
  ok('하루' in pg.locator('.srch-res').inner_text(),'검색: 서버에서 사람 찾기')
  ok(not errs,'ERR',errs)
  st=pg.evaluate("Object.fromEntries(Object.keys(localStorage).map(k=>[k,localStorage.getItem(k)]))")
  m=b.new_context(viewport={'width':390,'height':800},has_touch=True).new_page();m.set_default_timeout(6000);m.on('pageerror',lambda e:errs.append(str(e)))
  m.goto(U2);m.evaluate("s=>{for(const k in s)localStorage.setItem(k,s[k])}",st);m.goto(U2);m.wait_for_timeout(1800)
  m.locator('#tabbar [data-tab2="notice"]').tap();m.wait_for_timeout(500);ok(m.locator('.nt-inbox-row').count()==1,'휴대폰: 알림 화면 맨 위 쪽지함')
  m.locator('.nt-inbox-row').tap();m.wait_for_timeout(900);m.locator(f'.nt-row[data-nt-with="{haru}"]').tap();m.wait_for_timeout(500)
  ok(m.locator('.nt-letter').count()==2 and m.locator('.nt-back').count()==1,'휴대폰: 편지첩 한 화면 + 쪽지함으로 돌아가기');m.screenshot(path='nt_m_thread.png')
  ok(not errs,'M ERR',errs)
print('fails',fails)
