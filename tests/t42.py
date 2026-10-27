from base import *
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
with sync_playwright() as p:
  b=p.chromium.launch()
  for mac in [False,True]:
    ctx=b.new_context(viewport={'width':1280,'height':800});
    if mac:ctx.add_init_script("Object.defineProperty(navigator,'platform',{get:()=>'MacIntel'})")
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));M='Meta' if mac else 'Control';tag='mac' if mac else 'win'
    pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300)
    pg.locator('[data-pn="room"]').click();pg.wait_for_timeout(300);pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(200)
    n=lambda:pg.locator('.rm-it').count()
    n0=n();pg.locator('[data-se-add]').click();pg.get_by_role('menuitem',name='전광판').click();pg.wait_for_timeout(300);n1=n()
    pg.locator('[data-se-add]').click();pg.get_by_role('menuitem',name='누르지 마시오 버튼').click();pg.wait_for_timeout(300);n2=n()
    # 글자 칸 안에서는 기본 되돌리기
    inp=pg.locator('[data-se-label]');inp.click();inp.type('가나');pg.keyboard.press(f'{M}+z');pg.wait_for_timeout(300);ok(f'{tag} undo inside input keeps widgets',n()==n2)
    pg.mouse.click(640,780);pg.wait_for_timeout(300)
    pg.keyboard.press(f'{M}+z');pg.wait_for_timeout(300);a=n();pg.keyboard.press(f'{M}+z');pg.wait_for_timeout(300);c=n()
    ok(f'{tag} undo twice {n0},{n1},{n2} -> {a},{c}',c<n2)
    pg.keyboard.press(f'{M}+Shift+z');pg.wait_for_timeout(300);d=n();ok(f'{tag} redo (shift) -> {d}',d>c)
    if not mac:pg.keyboard.press('Control+y');pg.wait_for_timeout(300);e2=n();ok(f'win redo ctrl+y -> {e2}',e2>=d)
    ok(f'{tag} tooltip',('⌘Z' if mac else 'Ctrl+Z') in (pg.locator('[data-se-undo]').get_attribute('title') or ''))
    print(tag,'ERR',errs)
