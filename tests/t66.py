# 글 기능: PC/모바일 작성·재사용·복구·취소·비공개·값 분리
from base import *

def rec(pg): return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records'))")
def editor(pg,mob):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
  pg.wait_for_timeout(300)
  pg.locator('input[id^="f-title-"]').fill('기능 테스트')
  pg.locator('.blocks .rte-area').first.fill('이야기는 그대로 남아요.')
def publish(pg):
  pg.locator('.hpub').click()
  pg.locator('input[name="pv"][value="private"]').check()
  pg.locator('.dialog [data-o]').click()
  pg.wait_for_selector('.win.editor',state='detached')
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob);pg.set_default_timeout(15000);editor(pg,mob)
    pg.locator('[data-pf-add]').click();pg.locator('[data-preset="0"]').click()
    assert pg.locator('[data-choices]:visible').count()==0
    pg.locator('[data-pf-name]').fill('나의 물건')
    pg.locator('[data-pf-apply]').click()
    pg.locator('[data-value="0"]').fill('2024-01-02')
    pg.locator('[data-value="1"]').fill('<img src=x onerror=alert(1)>')
    pg.locator('[data-template]').click();pg.locator('#m-in').fill('물건 기록');pg.locator('.dialog [data-o]').click()
    assert all(f['value']=='' for f in rec(pg)['functionTemplates'][0]['fields'])
    # 구성 취소는 현재 항목과 입력값을 변경하지 않음
    pg.locator('[data-config]').click();pg.locator('[data-pf-name]').fill('취소할 이름');pg.locator('.dialog [data-c]').click()
    assert pg.locator('.pf-head strong').inner_text()=='나의 물건'
    pg.wait_for_timeout(900);pg.reload();pg.wait_for_timeout(400)
    # 쓰던 글 복구
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
    assert pg.locator('[data-value="0"]').input_value()=='2024-01-02'
    publish(pg)
    saved=next(x for x in rec(pg)['posts'] if x['title']=='기능 테스트')
    assert saved['visibility']=='private' and saved['functions'][0]['name']=='나의 물건'
    assert pg.locator('.pf-view').count()>0
    assert pg.locator('.pf-view img').count()==0
    pg.keyboard.press('Escape');pg.wait_for_selector('.win',state='detached');editor(pg,mob)
    pg.locator('[data-pf-add]').click();pg.locator('[data-saved="0"]').click();pg.locator('[data-pf-apply]').click()
    assert pg.locator('[data-value="0"]').input_value()==''
    assert pg.locator('[data-value="1"]').input_value()==''
    pg.locator('[data-value="1"]').fill('다른 글의 값')
    # 구성 변경으로 숫자·선택 항목 추가, 기존 글의 구성은 독립적으로 유지
    pg.locator('[data-config]').click()
    pg.locator('[data-pf-field]').click()
    row=pg.locator('.pf-field').last
    row.locator('[data-name]').fill('가격')
    row.locator('[data-type]').select_option('number')
    pg.locator('[data-pf-field]').click()
    row=pg.locator('.pf-field').last
    row.locator('[data-name]').fill('상태')
    row.locator('[data-type]').select_option('select')
    row.locator('[data-options]').fill('보관, 정리 중')
    pg.locator('[data-pf-apply]').click()
    pg.locator('[data-value="2"]').fill('0')
    pg.locator('[data-value="3"]').select_option('정리 중')

    pg.screenshot(path='/tmp/post-functions-'+('mobile' if mob else 'pc')+'.png',full_page=True)
    publish(pg)
    assert next(x for x in rec(pg)['posts'] if x['id']==saved['id'])['functions'][0]['fields'][1]['value']=='<img src=x onerror=alert(1)>'
    assert len(next(x for x in rec(pg)['posts'] if x['id']==saved['id'])['functions'][0]['fields'])==2
    newer=next(x for x in rec(pg)['posts'] if x['id']!=saved['id'])
    assert newer['functions'][0]['fields'][2]['value']=='0'
    assert newer['functions'][0]['fields'][3]['value']=='정리 중'
    assert not pg.errs,pg.errs
    print('OK', 'mobile' if mob else 'PC','properties, template isolation, restore, cancel, private save, escaped output')
    pg.context.close()
  b.close()
