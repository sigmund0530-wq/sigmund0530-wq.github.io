# 글에 정보 붙이기: 입력→제안→바로 붙음, 초성·문장 찾기, 새 이름, 되돌리기, 직접 고치기, 자주 쓰기, 복구, 비공개, 값 분리, 이스케이프 (PC/모바일)
from base import *

def rec(pg): return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records'))")
def editor(pg,mob):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
  pg.wait_for_timeout(300)
  pg.locator('input[id^="f-title-"]').fill('붙이기 테스트')
  pg.locator('.blocks .rte-area').first.fill('이야기는 그대로 남아요.')
def publish(pg):
  pg.locator('.hpub').click()
  pg.locator('input[name="pv"][value="private"]').check()
  pg.locator('.dialog [data-o]').click()
  pg.wait_for_selector('.win.editor',state='detached')
def sugs(pg): return [t.split('\n')[0] for t in pg.locator('.pf-sug .pf-sug-t b').all_inner_texts()]
def typeq(pg,q):
  pg.locator('[data-pf-q]').fill('');pg.locator('[data-pf-q]').type(q);pg.wait_for_timeout(120)
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    tag='모바일' if mob else 'PC'
    pg=setup(b,mob);pg.set_default_timeout(15000);editor(pg,mob)
    pg.locator('[data-pf-add]').click()
    assert pg.locator('[data-pf-q]').evaluate("e=>document.activeElement===e"),'입력줄에 바로 커서'
    assert len(sugs(pg))>0,'빈 입력에도 제안'
    typeq(pg,'구매');assert sugs(pg)[0]=='구매 정보',sugs(pg)
    typeq(pg,'샀');assert sugs(pg)[0]=='구매 정보',sugs(pg)
    typeq(pg,'ㄷㅅ');assert sugs(pg)[0]=='독서 기록',('초성',sugs(pg))
    typeq(pg,'책을 샀다');s=sugs(pg);assert s[:2]==['독서 기록','구매 정보'],('문장',s)
    typeq(pg,'구매');pg.keyboard.press('Enter');pg.wait_for_timeout(150)
    assert pg.locator('.pf-head strong').first.inner_text()=='구매 정보'
    assert pg.locator('[data-value="1"]').evaluate("e=>document.activeElement===e"),'붙자마자 첫 글자 칸에 커서(날짜 칸은 건너뜀)'
    assert pg.locator('[data-pf-q]').is_hidden() and pg.locator('[data-pf-add]').is_visible()
    # 되돌리기
    pg.locator('.pf-undo [data-undo]').click();assert pg.locator('.pf-card').count()==0,'되돌리기'
    # 새 이름으로 붙이기
    pg.locator('[data-pf-add]').click();typeq(pg,'반려식물');assert pg.locator('[data-sug-new]').count()==1
    pg.locator('[data-sug-new]').click();assert pg.locator('.pf-head strong').first.inner_text()=='반려식물'
    pg.locator('.pf-card').first.locator('[data-delete]').click()
    # 물건 정리 → 직접 고치기 → 값 입력(이스케이프 확인용)
    pg.locator('[data-pf-add]').click();typeq(pg,'물건');pg.keyboard.press('Enter')
    pg.locator('[data-config]').click();pg.locator('[data-pf-name]').fill('나의 물건');pg.locator('[data-pf-apply]').click()
    pg.locator('[data-value="0"]').fill('<img src=x onerror=alert(1)>');pg.locator('[data-value="1"]').fill('서랍')
    # 직접 고치기 취소는 바꾸지 않음
    pg.locator('[data-config]').click();pg.locator('[data-pf-name]').fill('취소할 이름');pg.locator('.dialog [data-c]').click()
    assert pg.locator('.pf-head strong').inner_text()=='나의 물건'
    # 자주 쓰기에 넣기: 값은 빼고 구성만
    pg.locator('[data-template]').click();pg.locator('#m-in').fill('물건 기록');pg.locator('.dialog [data-o]').click()
    assert all(f['value']=='' for f in rec(pg)['functionTemplates'][0]['fields'])
    pg.wait_for_timeout(900);pg.reload();pg.wait_for_timeout(400)
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
    assert pg.locator('[data-value="1"]').input_value()=='서랍','쓰던 글 복구'
    publish(pg)
    saved=next(x for x in rec(pg)['posts'] if x['title']=='붙이기 테스트')
    assert saved['visibility']=='private' and saved['functions'][0]['name']=='나의 물건'
    assert pg.locator('.pf-view').count()>0 and pg.locator('.pf-view img').count()==0
    pg.keyboard.press('Escape');pg.wait_for_selector('.win',state='detached');editor(pg,mob)
    # 다음 글: 자주 쓰기가 맨 위, 값은 비어 있음
    pg.locator('[data-pf-add]').click();assert sugs(pg)[0]=='물건 기록',sugs(pg)
    assert pg.locator('.pf-sug').first.locator('em').inner_text()=='자주 쓰기'
    pg.keyboard.press('Enter');assert pg.locator('[data-value="0"]').input_value()=='' and pg.locator('[data-value="1"]').input_value()==''
    pg.locator('[data-value="1"]').fill('다른 글의 값')
    pg.locator('[data-config]').click();pg.locator('[data-pf-field]').click();row=pg.locator('.pf-field').last
    row.locator('[data-name]').fill('가격');row.locator('[data-type]').select_option('number');pg.locator('[data-pf-apply]').click()
    pg.locator('[data-value="3"]').fill('0')
    publish(pg)
    old=next(x for x in rec(pg)['posts'] if x['id']==saved['id'])
    assert old['functions'][0]['fields'][0]['value']=='<img src=x onerror=alert(1)>' and len(old['functions'][0]['fields'])==3
    newer=next(x for x in rec(pg)['posts'] if x['id']!=saved['id'])
    assert newer['functions'][0]['schemaId']==old['functions'][0]['schemaId'], 'template reuse retains schema identity'
    assert newer['functions'][0]['fields'][0]['key']==old['functions'][0]['fields'][0]['key'], 'field identity survives reuse'
    assert newer['functions'][0]['fields'][1]['value']=='다른 글의 값' and newer['functions'][0]['fields'][3]['value']=='0'
    assert rec(pg)['settings']['pfRecent'][0]=='물건 기록'
    assert not pg.errs,pg.errs
    print('OK',tag,'붙이기·초성·문장·새 이름·되돌리기·직접 고치기·자주 쓰기·복구·비공개·값 분리·이스케이프')
    pg.context.close()
  b.close()
