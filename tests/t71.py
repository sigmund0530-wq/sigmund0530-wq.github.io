# 사진에 붙이기: 사진 메뉴 → 제안 → 사진 속 위치 → 읽는 화면 점·카드 → 모아 보기 썸네일
from base import *
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob)
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
    pg.locator('input[id^="f-title-"]').fill('책상 사진');pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('5만 원에 팔아요.')
    pg.locator('input[id^="f-ins-"]').set_input_files('cv.jpg');pg.wait_for_timeout(1000)
    pg.locator('.ph-item [data-phm]').first.click();pg.wait_for_timeout(200)
    labels=pg.locator('.menu [role=menuitem], .menu button').all_inner_texts()
    assert any('이 사진에 정보 붙이기' in x for x in labels),labels
    pg.locator('.menu').get_by_text('이 사진에 정보 붙이기').click();pg.wait_for_timeout(200)
    assert pg.locator('.pfw-pop .pfw-sg').first.locator('b').inner_text()=='중고 판매'
    pg.locator('.pfw-pop .pfw-sg').first.click();pg.wait_for_timeout(250)
    assert pg.locator('.ph-item.pfp-pinning').count()==1 and pg.locator('.pfp-hint').count()==1
    box=pg.locator('.ph-item [data-phm] img').first.bounding_box()
    pg.mouse.click(box['x']+box['width']*0.25,box['y']+box['height']*0.75);pg.wait_for_timeout(250)
    assert pg.locator('.menu').count()==0,'pin click does not open photo menu'
    assert pg.locator('.ph-item .pfp-dot').count()==1 and pg.locator('.pfp-hint').count()==0
    card=pg.locator('.pf-card.pf-anch');assert '사진' in card.locator('.pf-name').inner_text()
    assert card.locator('[data-value="1"]').input_value()=='50000'
    card.locator('[data-value="0"]').fill('원목 책상')
    pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
    r=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(p=>p.title==='책상 사진')")
    a=r['functions'][0]['anchor'];assert 20<a['x']<30 and 70<a['y']<80,a
    if pg.locator('.txt:visible').count()==0:
      if mob: pg.locator('[data-tab2="me"]').click();pg.wait_for_timeout(250)
      pg.locator(f'[data-open-post="{r["id"]}"]').first.click();pg.wait_for_timeout(400)
    assert pg.locator('.pfig .pfp-dot:visible').count()==1
    assert pg.locator('.pf-view:visible').count()==0
    assert '사진 ‘원목 책상’ · 중고 판매' in pg.locator('.pfw-list:visible').inner_text()
    pg.locator('.pfig .pfp-dot:visible').click();pg.wait_for_timeout(200)
    assert '50,000원' in pg.locator('.pfw-card').inner_text()
    pg.locator('.pfw-card [data-pf-go]').click();pg.wait_for_timeout(300)
    assert pg.locator('.pfc-row.has-th .pfc-th').count()==1
    assert not pg.errs,pg.errs
    print('OK','mobile' if mob else 'PC','photo menu → suggestion → pin → dot + card → collect thumbnail')
    pg.context.close()
  b.close()
