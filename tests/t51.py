import json,copy
from base import *
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
STATE="JSON.stringify([localStorage.getItem('mgd2.v1.records'),localStorage.getItem('mgd2.v1.layout.desktop'),localStorage.getItem('mgd2.v1.assets')])"
with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':860},accept_downloads=True);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-write]');pg.wait_for_timeout(400)
  # 글: 사진 + 음성 + 그림 + 나만 보기
  a=pg.locator('.win.editor .rte-area').first;a.click();pg.keyboard.type('바다에 갔다. 바람이 불었다.')
  pg.set_input_files('.win.editor input[id^="f-ins"]','p1.jpg');pg.wait_for_timeout(500)
  pg.click('[data-x-audio]');pg.wait_for_timeout(200);pg.set_input_files('.dialog [data-af]','beep.wav');pg.wait_for_timeout(200);pg.click('.dialog [data-o]');pg.wait_for_timeout(400)
  pg.click('[data-x-draw]');a.scroll_into_view_if_needed();pg.wait_for_timeout(200);bb=a.bounding_box();pg.mouse.move(bb['x']+10,bb['y']+20);pg.mouse.down();pg.mouse.move(bb['x']+150,bb['y']+22,steps=6);pg.mouse.up();pg.click('.ink-bar [data-idone]')
  pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog input[value="close"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  pid=pg.locator('article.post[data-pid]').first.get_attribute('data-pid')
  # 덧붙임 + 이전 버전
  pg.click(f'[data-x-more="{pid}"]');pg.get_by_role('menuitem',name='덧붙이기').click();pg.fill('#adn-t','다시 읽은 생각');pg.click('.dialog [data-o]');pg.wait_for_timeout(300)
  pg.click(f'[data-act="editPost"][data-post="{pid}"]');pg.wait_for_timeout(400);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.press('Control+End');pg.keyboard.type(' 고침.');pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
  pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  S0=pg.evaluate(STATE);r0=json.loads(json.loads(S0)[0]);post0=r0['posts'][0]
  print('   담긴 것: 공개범위',post0['visibility'],'| 그림',len(post0.get('ink') or []),'| 덧붙임',len(post0.get('addenda') or []),'| 이전버전',len(r0['vault']['revs'].get(pid,[])),'| 음성블록',sum(1 for b in post0['bodyJson']['blocks'] if b['type']=='audio'),'| 파일',len(json.loads(json.loads(S0)[2])))
  # 내보내기
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='백업 · 내보내기').click();pg.wait_for_timeout(300)
  with pg.expect_download() as dl:pg.click('.dialog [data-ex]')
  good=dl.value.path();G=json.load(open(good));pg.click('.dialog [data-c]');pg.wait_for_timeout(200)
  # 상태 바꾸기
  pg.evaluate("(()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));})()")
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='글쓰기').click();pg.wait_for_timeout(300);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type('백업 뒤 글');pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
  pg.evaluate("document.querySelectorAll('.win .x').forEach(b=>b.click())");pg.wait_for_timeout(200)
  S1=pg.evaluate(STATE)
  # 깨진 파일들: 하나도 건드리면 안 됨
  open('bk_trunc.json','w').write(open(good).read()[:5000])
  bad1=copy.deepcopy(G);bad1['app']='other';json.dump(bad1,open('bk_app.json','w'))
  bad2=copy.deepcopy(G);bad2['records']['posts']={'x':1};json.dump(bad2,open('bk_posts.json','w'))
  bad3=copy.deepcopy(G);k=list(bad3['assets'])[0];bad3['assets'][k]['dataUrl']='javascript:alert(1)';json.dump(bad3,open('bk_asset.json','w'))
  bad4=copy.deepcopy(G);bad4['version']=9;json.dump(bad4,open('bk_ver.json','w'))
  for f in ['bk_trunc.json','bk_app.json','bk_posts.json','bk_asset.json','bk_ver.json']:
    pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='백업 · 내보내기').click();pg.wait_for_timeout(300)
    pg.set_input_files('.dialog [data-im]',f);pg.wait_for_timeout(400);msg=pg.locator('.toast').last.inner_text() if pg.locator('.toast').count() else ''
    if pg.locator('.dialog [data-c]').count():pg.locator('.dialog [data-c]').click();pg.wait_for_timeout(150)
    ok(f'손상 파일 {f}: 지금 내용 그대로 · 안내 "{msg[:38]}…"',pg.evaluate(STATE)==S1 and pg.locator('[data-bk-go]').count()==0)
  # 정상 파일: '지금 내용도 먼저 내보내고' 선택 → 내려받기 생기고 → 백업 내용과 똑같이
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='백업 · 내보내기').click();pg.wait_for_timeout(300)
  pg.set_input_files('.dialog [data-im]',good);pg.wait_for_timeout(400)
  ok('덮어쓴다는 안내',"합치지 않고 덮어써서" in pg.locator('.dialog').inner_text())
  with pg.expect_download() as dl2:pg.click('[data-bk-safe]')
  pre=json.load(open(dl2.value.path()));ok('되살리기 전 지금 내용 파일 받음 (백업 뒤 글 포함)',any('백업 뒤 글' in json.dumps(p,ensure_ascii=False) for p in pre['records']['posts']))
  pg.wait_for_timeout(600);S2=json.loads(pg.evaluate(STATE))
  same=[json.loads(S2[0])==G['records'],json.loads(S2[1])==G['layout'],json.loads(S2[2])==G['assets']]
  ok(f'되살린 뒤 백업과 똑같음 (글·공간·파일) {same}',all(same))
  r2=json.loads(S2[0]);p2=[x for x in r2['posts'] if x['id']==pid][0]
  ok('사진·음성·그림·덧붙임·이전버전·공개범위 보존',p2['visibility']=='close' and len(p2.get('ink') or [])==1 and len(p2.get('addenda') or [])==1 and len(r2['vault']['revs'][pid])>=1 and any(b['type']=='audio' for b in p2['bodyJson']['blocks']))
  pg.reload();pg.wait_for_timeout(700);pg.locator('.pc-nav [data-pn="menu"]').click();pg.get_by_role('menuitem',name='전체 글').click();pg.wait_for_timeout(300)
  pg.locator(f'[data-open-post="{pid}"]').first.click();pg.wait_for_timeout(600)
  ok('새로고침 후 글 열기: 사진·음성·그림 표시',pg.locator('article.post .pfig img').count()==1 and pg.locator('article.post audio').count()==1 and pg.locator('article.post svg.ink path').count()==1)
  print('ERR',errs)
