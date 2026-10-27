from base import *
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,mob,vp in [('pc',False,None),('m',True,None),('tab',False,{'width':820,'height':1180})]:
    if vp:
      ctx=b.new_context(viewport=vp);pg=ctx.new_page();pg.set_default_timeout(5000);pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
      pg.goto(U);pg.wait_for_timeout(500);pg.locator('[data-au-social="kakao"]').click();pg.wait_for_timeout(100);pg.locator('[data-au-all]').check();pg.wait_for_timeout(100);pg.locator('[data-au-next]').click();pg.wait_for_timeout(200);pg.locator('#ob-handle').fill('haru');pg.locator('[data-au-make]').click();pg.wait_for_timeout(250);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(250);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(300)
    else: pg=setup(b,mob)
    write(pg,mob,'바다','아침 일찍 바다에 갔다. 바람이 많이 불었다. 그래도 좋았다. 파도 소리가 컸다.',['p1.jpg'],vis='public');closeall(pg)
    write(pg,mob,'퇴근길','오늘은 그냥 걸어서 왔다. 하늘이 예뻤다. 나쁜 하루도 끝은 난다.',None,vis='public')
    pg.get_by_role('button',name='내 공간에 놓기').click();pg.wait_for_timeout(200);pg.locator('[data-sk="quote"]').first.click();pg.wait_for_timeout(200);closeall(pg)
    if mob:pg.locator('[data-tab2="room"]').click()
    else:pg.locator('[data-pn="room"]').click()
    pg.wait_for_timeout(300);pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(200)
    for w in ['뜯어 가는 전단지','영수증 운세','누르지 마시오 버튼','전광판']:
      pg.locator('[data-se-add]').click();pg.get_by_role('menuitem',name=w).click();pg.wait_for_timeout(200)
    # quote -> note
    q=pg.locator('.rm-quote').first;q.scroll_into_view_if_needed();bb=q.bounding_box()
    if pg.locator('[data-se-close]').count():pg.locator('[data-se-close]').click();pg.wait_for_timeout(150)
    q=pg.locator('.rm-quote').first;q.scroll_into_view_if_needed();bb=q.bounding_box();pg.mouse.click(bb['x']+bb['width']/2,bb['y']+10);pg.wait_for_timeout(200)
    if pg.locator('[data-se-prop="bare"][data-v="note"]').count():pg.locator('[data-se-prop="bare"][data-v="note"]').click();pg.wait_for_timeout(150)
    pg.locator('[data-se-save]').click();pg.wait_for_timeout(500)
    print(name,'위젯:',{c:pg.locator(c).count() for c in ['.rw-flyer','.rw-receipt','.rw-btnwrap','.rw-led','[data-bare="note"]']})
    fl=pg.locator('.rw-flyer').first;fl.scroll_into_view_if_needed();pg.wait_for_timeout(300);pg.screenshot(path=f'real_{name}_1.png')
    t=pg.locator('[data-flyer]').first;t.click();pg.wait_for_timeout(700);print(name,'데려간 문장:',pg.locator('.rw-took p').inner_text() if pg.locator('.rw-took').count() else '-');pg.screenshot(path=f'real_{name}_took.png');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(200)
    print(name,'뜯긴 띠:',pg.locator('.rw-tab.torn').count())
    r=pg.locator('.rw-receipt').first;r.scroll_into_view_if_needed();pg.wait_for_timeout(200);pg.screenshot(path=f'real_{name}_2.png')
    pg.locator('[data-receipt]').first.click();pg.wait_for_timeout(1000)
    pg.locator('.rw-led').first.scroll_into_view_if_needed();pg.wait_for_timeout(300);pg.screenshot(path=f'real_{name}_3.png')
    pg.locator('[data-bigbtn]').first.click();pg.wait_for_timeout(600);print(name,'버튼 → 글:',pg.locator('.win').count())
    print(name,'ERR',pg.errs)
