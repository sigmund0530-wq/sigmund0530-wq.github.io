# 위젯 피드: 글|위젯 나누기, 예시, 썸네일→재생(한 번에 하나), 격리(부모·인터넷·저장소 막힘), 올리기(코드·그림), 고치기·지우기, 새로고침 유지, 휴대폰 가운데 재생
from base import *
PROBE="""<body style="font:14px system-ui"><div id=o>…</div><script>
const r=[];try{parent.document.body;r.push('parent:open')}catch(e){r.push('parent:blocked')}
try{localStorage.setItem('x','1');r.push('storage:open')}catch(e){r.push('storage:blocked')}
try{document.cookie='a=1';r.push(document.cookie?'cookie:open':'cookie:blocked')}catch(e){r.push('cookie:blocked')}
fetch('https://example.com').then(()=>{r.push('net:open');o.textContent=r.join(' ')}).catch(()=>{r.push('net:blocked');o.textContent=r.join(' ')});
</script></body>"""
def goWidgets(pg,mob):
  if mob:pg.locator('[data-tab2="follow"]').click()
  else:pg.locator('[data-pn="feed"]').click()
  pg.wait_for_timeout(300);pg.locator('[data-feed-kind="widget"]').click();pg.wait_for_timeout(300)
with sync_playwright() as p:
  b=p.chromium.launch()
  # PC
  pg=setup(b,False);pg.set_default_timeout(8000)
  assert pg.locator('.pc-nav [data-pn="feed"]').inner_text()=='피드'
  goWidgets(pg,False)
  assert pg.locator('.wf-card').count()==5,'예시 5개'
  assert pg.locator('.wf-live').count()==0,'처음엔 썸네일만'
  c=pg.locator('.wf-card').nth(0);c.locator('.wf-frame').hover();pg.wait_for_timeout(300)
  f=pg.locator('.wf-card').nth(0).locator('iframe.wf-live')
  assert f.count()==1 and f.get_attribute('sandbox')=='allow-scripts','마우스 올리면 격리 상자로 재생'
  assert "connect-src 'none'" in f.get_attribute('srcdoc')
  pg.locator('.wf-card').nth(2).locator('.wf-frame').hover();pg.wait_for_timeout(300)
  assert pg.locator('iframe.wf-live').count()==1,'한 번에 하나만'
  pg.mouse.move(5,5);pg.wait_for_timeout(200);assert pg.locator('iframe.wf-live').count()==0,'벗어나면 멈춤'
  # 올리기: 코드 붙여 넣기 (격리 확인용)
  pg.locator('[data-wf-add]').click();pg.locator('[data-wt="paste"]').click();pg.locator('#wf-code').fill(PROBE)
  pg.locator('#wf-title').fill('격리 시험');pg.wait_for_timeout(700)
  assert pg.locator('.wf-pv-box iframe').count()==2,'휴대폰·PC 미리보기'
  pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
  assert pg.locator('[data-wf-scope="mine"][aria-pressed="true"]').count()==1 and pg.locator('.wf-card').count()==1
  pg.locator('.wf-card .wf-frame').hover();pg.wait_for_timeout(1500)
  fr=[x for x in pg.frames if x!=pg.main_frame]
  txt=fr[0].locator('#o').inner_text() if fr else ''
  print('   격리 결과:',txt)
  assert 'parent:blocked' in txt and 'storage:blocked' in txt and 'net:blocked' in txt and 'cookie:blocked' in txt,txt
  # 그림 올리기
  pg.mouse.move(5,5);pg.locator('[data-wf-add]').click();pg.locator('#wf-file').set_input_files('p1.jpg');pg.wait_for_timeout(500)
  assert pg.locator('#wf-title').input_value()=='p1'
  pg.locator('#wf-title').fill('바다 그림');pg.select_option('#wf-size','w');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
  assert pg.locator('.wf-card').count()==2 and pg.locator('.wf-card.wf-s-w img.wf-thumb').count()==1
  # 새로고침 유지
  pg.reload();pg.wait_for_timeout(700);goWidgets(pg,False);pg.locator('[data-wf-scope="mine"]').click();pg.wait_for_timeout(200)
  assert pg.locator('.wf-card').count()==2,'새로고침해도 남음'
  r=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).widgets");a=pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('mgd2.v1.assets')))")
  assert len(r)==2 and any(w['assetId'] in a for w in r if w['assetId']),'그림 파일 보관'
  # 크게 보기 → 고치기 → 지우기
  pg.locator('.wf-card').first.locator('.wf-frame').click();pg.wait_for_timeout(300)
  assert pg.locator('.win .wf-stage').count()==1
  pg.locator('.win [data-wf-edit]').click();pg.locator('#wf-title').fill('바다 그림 2');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(300)
  assert '바다 그림 2' in pg.locator('.wf-card').first.inner_text()
  pg.locator('.wf-card').first.locator('.wf-frame').click();pg.wait_for_timeout(300);pg.locator('.win [data-wf-del]').click();pg.locator('.dialog .btn.danger,.dialog [data-o]').last.click();pg.wait_for_timeout(300)
  assert pg.locator('.wf-card').count()==1,'지우기'
  # 글 피드로 돌아가기
  pg.locator('[data-feed-kind="post"]').click();pg.wait_for_timeout(300);assert pg.locator('.wf-grid').count()==0 and pg.locator('.wf-kind').count()==1
  assert not pg.errs,pg.errs;print('OK PC 위젯 피드');pg.context.close()
  # 휴대폰: 화면 가운데 오면 재생
  pg=setup(b,True);pg.set_default_timeout(8000);goWidgets(pg,True)
  assert pg.locator('.wf-live').count()<=1
  pg.locator('.wf-card').nth(3).scroll_into_view_if_needed();pg.evaluate("document.querySelectorAll('.wf-card')[3].scrollIntoView({block:'center'})");pg.wait_for_timeout(600)
  assert pg.locator('.wf-card').nth(3).locator('.wf-live').count()==1,'휴대폰: 가운데 카드 재생'
  assert pg.locator('.wf-live').count()==1
  pg.locator('.wf-card').nth(3).locator('.wf-open').click();pg.wait_for_timeout(500);print('   m win',pg.locator('.win').count(),pg.locator('.win .wf-stage').count(),pg.locator('.win .wf-stage iframe').count());assert pg.locator('.win .wf-stage iframe').count()==1
  assert not pg.errs,pg.errs;print('OK 휴대폰 위젯 피드');pg.context.close()
  b.close()
