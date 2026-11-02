# 글쓰는 중에 다른 화면으로 (2026-11-02, 주인 버그 신고): 위쪽 막대를 누르면 쓰던 글은 옆으로 치워 두고 그 화면이 보임 → '쓰던 글 이어 쓰기'로 그대로 돌아옴
from base import *
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
with sync_playwright() as p:
  b=p.chromium.launch()
  pg=setup(b,False);errs=pg.errs
  pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(500);pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('쓰는 중인 글')
  for k,want in (('feed','무작위'),('me','하루의 공간'),('room','내 방')):
    pg.locator(f'.pc-nav [data-pn="{k}"]').click();pg.wait_for_timeout(500)
    ok(pg.locator('.win.editor:visible').count()==0 and want in pg.locator('#canvas').inner_text() and pg.locator('#ed-park').count()==1,f'{k}: 그 화면이 보이고 쓰던 글은 치워 둠')
  pg.locator('.pc-nav [data-pn="menu"]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem',name='전체 글').click();pg.wait_for_timeout(500)
  ok(pg.locator('.win.editor:visible').count()==0,'내 메뉴 → 전체 글도')
  pg.locator('#ed-park').click();pg.wait_for_timeout(400)
  ok(pg.locator('.win.editor:visible').count()==1 and '쓰는 중인 글' in pg.locator('.blocks .rte-area').first.inner_text() and pg.locator('#ed-park').count()==0,'쓰던 글 이어 쓰기: 내용 그대로')
  pg.locator('.pc-nav [data-pn="feed"]').click();pg.wait_for_timeout(300);pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(500)
  ok(pg.locator('.win.editor:visible').count()>=1,'치워 둔 채 글쓰기를 누르면 글쓰기 창이 다시 보임')
  ok(not errs,'ERR',errs);pg.context.close()
  # 휴대폰: 글꼴 목록 → 내 방 길, 아래 탭이 다시 보이고 이어 쓰기 단추
  pg=setup(b,True);errs=pg.errs
  pg.locator('[data-tab2="write"]').click();pg.wait_for_timeout(500);pg.locator('.blocks .rte-area').last.click();pg.keyboard.type('휴대폰 글');pg.locator('.t-btn').tap();pg.wait_for_timeout(200)
  ok(not pg.locator('#tabbar').is_visible(),'M 글쓰는 중엔 아래 탭 숨김')
  pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(300);pg.locator('[data-uf-room]').click();pg.wait_for_timeout(700)
  ok(pg.locator('.mr-fonts').count()==1 and pg.locator('#tabbar').is_visible() and pg.locator('#ed-park').is_visible(),'M 내 방 내 글꼴로, 아래 탭과 이어 쓰기 단추')
  pg.locator('#ed-park').click();pg.wait_for_timeout(400)
  ok(pg.locator('.win.editor:visible').count()==1 and '휴대폰 글' in pg.locator('.blocks .rte-area').last.inner_text(),'M 이어 쓰기')
  ok(not errs,'M ERR',errs)
print('fails',fails)
