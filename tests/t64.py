from base import *
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    tag='m' if mob else 'pc'
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(5000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    nav=lambda:pg.evaluate("__mgdNav()")
    pg.goto(U);pg.wait_for_timeout(600);s0=nav()
    pg.locator('[data-au-social="kakao"]').click();pg.wait_for_timeout(200);s1=nav()
    pg.go_back();pg.wait_for_timeout(300);ok(nav()==s0,tag+' 가입: 뒤로 → 처음 화면',nav())
    pg.go_forward();pg.wait_for_timeout(300);ok(nav()==s1,tag+' 가입: 앞으로',nav())
    pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200);pg.locator('#ob-handle').fill('haru');pg.locator('[data-au-make]').click();pg.wait_for_timeout(250);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(250);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(400)
    home=nav();pg.go_back();pg.wait_for_timeout(300);ok(nav()==home,tag+' 가입 끝난 뒤 뒤로 가도 가입 화면 안 나옴',nav())
    write(pg,mob,'첫 글','바다',vis='public');closeall(pg);pg.wait_for_timeout(300);home=nav()
    # 전체 글 화면
    if mob:pg.locator('[data-tab2="follow"]').click()
    else:pg.locator('[data-pn="feed"]').click()
    pg.wait_for_timeout(300);feed=nav();ok(feed!=home,tag+' 이웃새글로 이동',feed)
    pg.go_back();pg.wait_for_timeout(300);ok(nav()==home,tag+' 뒤로 → 내 공간',nav())
    pg.go_forward();pg.wait_for_timeout(300);ok(nav()==feed,tag+' 앞으로 → 이웃새글',nav())
    pg.go_back();pg.wait_for_timeout(300)
    # 창 열기 → 뒤로 → 닫힘
    pg.evaluate("document.querySelector('[data-act=\"findPosts\"]')");
    if mob:pg.locator('[data-tab2="write"]').click()
    else:pg.locator('[data-act="newPostFeed"]:visible').first.click()
    pg.wait_for_timeout(400);ok(pg.locator('.win').count()==1,tag+' 글쓰기 창 열림')
    pg.go_back();pg.wait_for_timeout(500);ok(pg.locator('.win').count()==0,tag+' 뒤로 → 빈 글쓰기 창 닫힘',nav())
    # 내용 쓴 뒤 뒤로
    if mob:pg.locator('[data-tab2="write"]').click()
    else:pg.locator('[data-act="newPostFeed"]:visible').first.click()
    pg.wait_for_timeout(400);pg.locator('input[id^="f-title-"]').fill('쓰는 중');pg.wait_for_timeout(300)
    pg.go_back();pg.wait_for_timeout(500);print('   after back with text: wins',pg.locator('.win').count(),'scrim',pg.locator('.scrim').count(),nav())
    if pg.locator('.scrim').count():pg.go_back();pg.wait_for_timeout(400);print('   2nd back: wins',pg.locator('.win').count(),'scrim',pg.locator('.scrim').count())
    pg.locator('.win .back:visible,.win .x:visible').first.click();pg.wait_for_timeout(300)
    print('   dialog buttons',pg.locator('.scrim .btn').all_text_contents())
    for _ in range(3):
      if pg.locator('.scrim').count():pg.locator('.scrim .btn').last.click();pg.wait_for_timeout(300)
    print('   wins after',pg.locator('.win').count())
    # X로 닫은 다음 뒤로: 헛돌지 않음
    if mob:pg.locator('[data-tab2="follow"]').click()
    else:pg.locator('[data-pn="feed"]').click()
    pg.wait_for_timeout(300);feed=nav()
    if mob:pg.locator('[data-tab2="write"]').click()
    else:pg.locator('[data-act="newPostFeed"]:visible').first.click()
    pg.wait_for_timeout(400);closeall(pg);pg.wait_for_timeout(400);ok(pg.locator('.win').count()==0,tag+' X로 닫음')
    pg.go_back();pg.wait_for_timeout(400);ok(nav()!=feed,tag+' X로 닫은 뒤 뒤로 한 번에 이전 화면',nav())
    # 대화상자 열고 뒤로
    pg.go_forward();pg.wait_for_timeout(300)
    ok(not errs,tag+' ERR',errs);ctx.close()
  b.close()
