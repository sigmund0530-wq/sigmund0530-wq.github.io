from base import *
def ok(k,v):print(('OK  ' if v else 'FAIL'),k)
LAY="JSON.stringify(JSON.parse(localStorage.getItem('mgd2.v1.layout.desktop')).shelf)"
PRO="JSON.stringify((({displayName,status,bioHistory})=>({displayName,status,bioHistory}))(JSON.parse(localStorage.getItem('mgd2.v1.records')).profile))"
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,vp,mob in [('pc',{'width':1280,'height':860},False),('m',{'width':390,'height':800},True)]:
    ctx=b.new_context(viewport=vp,has_touch=mob);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.wait_for_timeout(500);pg.click('[data-au-social="kakao"]');pg.check('[data-au-all]');pg.click('[data-au-next]');pg.fill('#ob-handle','haru');pg.click('[data-au-make]');pg.wait_for_timeout(200);pg.click('[data-aup-skip]');pg.wait_for_timeout(200);pg.click('[data-au-enter]');pg.wait_for_timeout(300)
    room=lambda:(pg.locator('[data-tab2="me"]').click() if mob else pg.locator('.pc-nav [data-pn="me"]').click(),pg.wait_for_timeout(300))
    begin=lambda:(pg.locator('[data-se-begin]:visible').first.click(),pg.wait_for_timeout(300))
    def add(w):pg.locator('[data-se-add]').click();pg.get_by_role('menuitem',name=w).click();pg.wait_for_timeout(300)
    apply=lambda:(pg.locator('[data-se-pok]').click(),pg.wait_for_timeout(300))
    room();begin();pg.locator('.se-bar [data-se-save]').click();pg.wait_for_timeout(300)   # 기본 상자 자리 잡고 저장
    L0=pg.evaluate(LAY)
    # 1) 적용 → 전체 취소 → 처음 상태
    begin();add('전광판');apply();pg.locator('.se-bar [data-se-cancel]').click();pg.wait_for_timeout(400)
    ok(f'{name} 1. 적용 후 전체 취소 → 저장된 배치 그대로',pg.evaluate(LAY)==L0)
    # 2) 여러 개 연속 적용(추가·크기·문구) → 전체 취소 → 모두 복원
    begin();add('전광판');apply();add('누르지 마시오 버튼');pg.locator('[data-se-size]').fill('300');pg.locator('[data-se-size]').dispatch_event('change');pg.wait_for_timeout(300)
    pg.locator('[data-se-label]').fill('바꾼 문구');pg.wait_for_timeout(700);apply()
    n_mid=pg.locator('.rm-it').count();pg.locator('.se-bar [data-se-cancel]').click();pg.wait_for_timeout(400)
    ok(f'{name} 2. 여러 개 적용({n_mid}칸) 후 전체 취소 → 모두 복원 ({pg.locator(".rm-it").count()}칸)',pg.evaluate(LAY)==L0)
    # 3) 전체 저장 → 새로고침 → 유지
    begin();add('전광판');apply();pg.locator('.se-bar [data-se-save]').click();pg.wait_for_timeout(400);n_saved=pg.locator('.rm-it').count()
    pg.reload();pg.wait_for_timeout(700);room()
    ok(f'{name} 3. 저장 후 새로고침해도 유지 ({n_saved} → {pg.locator(".rm-it").count()}칸)',pg.locator('.rm-it').count()==n_saved and pg.evaluate(LAY)!=L0)
    # 4) 전체 취소 → 소개 이력에도 안 남음 (이력 켜 둔 상태에서)
    me=lambda:(pg.locator('[data-tab2="me"]').click() if mob else pg.locator('.pc-nav [data-pn="me"]').click(),pg.wait_for_timeout(300))
    # 프로필은 이제 '프로필 편집' 화면에서 따로 저장(2026-11-02). 그 화면의 취소 → 소개·이력 그대로, 완료 → 이전 소개가 이력에
    def pe(status,keep=False,ok_=True):
      begin();pg.locator('[data-se="profile"]').first.click();pg.wait_for_timeout(400)
      if keep:pg.locator('[data-pe-keep]').check()
      pg.locator('[data-pe-status]').fill(status);pg.locator('[data-pe-ok]' if ok_ else '[data-pe-x]').click();pg.wait_for_timeout(300)
      pg.locator('.se-bar [data-se-save]').click();pg.wait_for_timeout(400)
    me();pe('처음 소개',keep=True);P0=pg.evaluate(PRO)
    pe('바꿨다 취소할 소개',ok_=False);P1=pg.evaluate(PRO)
    ok(f'{name} 4. 프로필 편집에서 취소 → 소개·소개 이력 그대로 {P1}',P1==P0)
    pe('두 번째 소개')
    ok(f'{name} +. 완료하면 이전 소개가 이력에 남음 {pg.evaluate(PRO)}','처음 소개' in pg.evaluate(PRO).split('bioHistory')[1])
    print(name,'ERR',errs)
