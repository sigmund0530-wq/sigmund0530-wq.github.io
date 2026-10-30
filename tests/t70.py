# 글 속 단어에 붙이기: 드래그 → 문장에 맞는 제안 → 단어가 대상, 같은 문장 값 미리 채움 → 읽는 화면 점선·카드 → 모아 보기
from base import *
SEL="""(t)=>{const a=document.querySelector('.win .rte-area');const w=document.createTreeWalker(a,4);let n;while(n=w.nextNode()){const i=n.data.indexOf(t);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+t.length);const s=getSelection();s.removeAllRanges();s.addRange(r);return true}}return false}"""
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob)
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
    pg.locator('input[id^="f-title-"]').fill('책상 정리');pg.locator('.blocks .rte-area').first.click()
    pg.keyboard.type('이사 가면서 원목 책상을 5만 원에 팔아요, 아직 판매 중이에요.')
    assert pg.locator('.pfw-tip').is_visible()
    assert pg.evaluate(SEL,'원목 책상');pg.wait_for_timeout(450)
    assert pg.locator('.pfw-pop').count()==1
    first=pg.locator('.pfw-pop .pfw-sg').first.locator('b').inner_text()
    assert first=='중고 판매',first
    pg.locator('.pfw-pop .pfw-sg').first.click();pg.wait_for_timeout(250)
    assert pg.locator('.win .rte-area mark[data-pf]').inner_text()=='원목 책상'
    card=pg.locator('.pf-card.pf-anch')
    assert card.count()==1 and '‘원목 책상’' in card.locator('.pf-name').inner_text()
    assert card.locator('[data-value="1"]').input_value()=='50000','price from sentence'
    assert card.locator('[data-value="2"]').input_value()=='판매 중','select from sentence'
    # 본문에서 단어를 고치면 값도 바뀜
    pg.locator('.win .rte-area mark[data-pf]').click();pg.wait_for_timeout(200)
    assert pg.locator('.pfw-pop.mini').count()==1;pg.keyboard.press('Escape')
    pg.evaluate("()=>{const m=document.querySelector('.win .rte-area mark[data-pf]');m.textContent='원목 책상 세트';m.closest('.rte-area').dispatchEvent(new Event('input',{bubbles:true}))}");pg.wait_for_timeout(450)
    assert '원목 책상 세트' in card.locator('.pf-name').inner_text()
    # 다른 이름으로 붙이기
    assert pg.evaluate(SEL,'이사');pg.wait_for_timeout(450)
    pg.locator('.pfw-own input').fill('이사 준비');pg.locator('.pfw-own .btn').click();pg.wait_for_timeout(200)
    assert pg.locator('.win .rte-area mark[data-pf]').count()==2
    # 발행
    pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
    r=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(p=>p.title==='책상 정리')")
    html=' '.join(b_['html'] for b_ in r['bodyJson']['blocks'] if b_['type']=='text')
    assert html.count('data-pf=')==2 and '<script' not in html,html
    assert any(f['value']=='원목 책상 세트' for g in r['functions'] for f in g['fields'])
    # 읽는 화면: 표 대신 점선 단어와 한 줄
    pg.evaluate("id=>window.__open&&0",None)
    pid=r['id'];pg.evaluate(f"document.querySelector('[data-open-post=\"{pid}\"]')?.click()");pg.wait_for_timeout(400)
    if pg.locator('.win .txt mark[data-pf]').count()==0:
      if mob: pg.locator('[data-tab2="me"]').click();pg.wait_for_timeout(250)
      pg.locator(f'[data-open-post="{pid}"]').first.click();pg.wait_for_timeout(400)
    assert pg.locator('.txt mark[data-pf]:visible').count()==2
    assert pg.locator('.pf-view:visible').count()==0,'no table for anchored info'
    assert '‘원목 책상 세트’ · 중고 판매' in pg.locator('.pfw-list:visible').inner_text()
    pg.locator('.txt mark[data-pf]:visible',has_text='원목').first.click();pg.wait_for_timeout(200)
    c=pg.locator('.pfw-card').inner_text();assert '50,000원' in c and '판매 중' in c,c
    pg.locator('.pfw-card [data-pf-go]').click();pg.wait_for_timeout(300)
    assert pg.locator('.pfc-tabs [aria-selected=true]').inner_text()=='내놓은 물건'
    assert '원목 책상 세트' in pg.locator('.pfc-g.hl h2').inner_text()
    # 이스케이프: 이상한 단어도 글자로만
    assert not pg.errs,pg.errs
    print('OK','mobile' if mob else 'PC','drag word → suggestion by sentence, prefill, sync, read view mark+card, collect')
    pg.context.close()
  b.close()
