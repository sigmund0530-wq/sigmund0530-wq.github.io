from base import *
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,vp,mob in [('pc',{'width':1280,'height':860},False),('m',{'width':390,'height':800},True)]:
    ctx=b.new_context(viewport=vp,has_touch=mob);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300)
    # 글 하나
    if mob:pg.locator('[data-tab2="write"]').click()
    else:pg.locator('text=글쓰기').first.click()
    pg.wait_for_timeout(300);pg.locator('.win.editor .rte-area').first.click();pg.keyboard.type('오늘은 비가 왔다. 우산을 샀다.')
    pg.locator('.win.editor .hpub').click();pg.wait_for_timeout(250);pg.locator('.dialog input[value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
    pg.evaluate("document.querySelectorAll('.win .x,.win .back').forEach(b=>b.click())");pg.wait_for_timeout(200)
    go=lambda k:(pg.locator(f'[data-tab2="{k}"]').click() if mob else pg.locator(f'.pc-nav [data-pn="{k}"]').click(),pg.wait_for_timeout(400))
    go('me');ok(f'{name} blog: posts list visible',pg.locator('.home.sp-blog .nv-posts:visible').count()==1);ok(f'{name} blog: no widget board',pg.locator('.home .rm-canvas').count()==0)
    ok(f'{name} blog: post listed','오늘은 비가' in pg.locator('.nv-posts').inner_text() or pg.locator('.nv-posts [data-open-post]').count()>=1)
    pg.screenshot(path=f'axis_{name}_blog.png')
    go('room');ok(f'{name} room: board',pg.locator('.home.sp-room .rm-canvas').count()==1);ok(f'{name} room: no posts list',pg.locator('.nv-posts').count()==0);ok(f'{name} room: head',pg.locator('.room-head').count()==1)
    sel=f'[data-tab2="room"]' if mob else '.pc-nav [data-pn="room"]';ok(f'{name} room pressed',pg.locator(sel).get_attribute('aria-pressed')=='true')
    pg.screenshot(path=f'axis_{name}_room.png')
    # 내 방 편집 → 위젯 추가 가능
    pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(300);ok(f'{name} room edit has add',pg.locator('[data-se-add]:visible').count()==1);pg.locator('[data-se-save]').click();pg.wait_for_timeout(300)
    # 내 공간 편집 → 추가 숨김
    go('me');pg.locator('[data-se-begin]:visible').first.click() if pg.locator('[data-se-begin]:visible').count() else None;pg.wait_for_timeout(300)
    if pg.locator('.se-bar').count():ok(f'{name} blog edit hides add',pg.locator('[data-se-add]:visible').count()==0);pg.locator('[data-se-save]').click();pg.wait_for_timeout(300)
    if not mob:
      # 방문자 미리보기
      pg.locator('.pc-nav [data-pn="menu"]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem',name='내 공간 미리 보기').click()
      pg.wait_for_timeout(400)
      ok('visitor sees room entry',pg.locator('[data-go-room]').count()==1)
      if pg.locator('[data-go-room]').count():pg.locator('[data-go-room]').click();pg.wait_for_timeout(300);ok('visitor room title',"의 방" in pg.locator('.room-head h2').inner_text());pg.screenshot(path='axis_visitor_room.png')
    print(name,'ERR',errs)
  # 나만 공개 → 방문자 잠김
  ctx=b.new_context(viewport={'width':1280,'height':860});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300)
  pg.locator('.pc-nav [data-pn="room"]').click();pg.wait_for_timeout(300);pg.select_option('[data-room-vis]','private');pg.wait_for_timeout(300)
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem',name='내 공간 미리 보기').click();pg.wait_for_timeout(400)
  ok('private: no entry for visitor',pg.locator('[data-go-room]').count()==0)
  print('ERR',errs)
