# 내 방 = 위젯 만들고 보관하는 곳(2026-11-02): 내 방 탭 → 내가 만든 위젯 + 담아 온 위젯 · 위젯 만들기 · 피드 예시를 '내 방에 담기' · 배치는 내 공간 편집(꺼낸 조각은 내 공간 글 위에)
from base import *
def ok(k,v,x=''):print(('OK  ' if v else 'FAIL'),k,x)
HTML='<!doctype html><html><body style="margin:0;display:grid;place-items:center;height:100vh;font:24px sans-serif">안녕</body></html>'
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,mob in [('pc',False),('m',True)]:
    pg=setup(b,mob);errs=pg.errs
    room=lambda:(pg.locator('[data-tab2="room"]').click() if mob else pg.locator('.pc-nav [data-pn="room"]').click(),pg.wait_for_timeout(400))
    me=lambda:(pg.locator('[data-tab2="me"]').click() if mob else pg.locator('.pc-nav [data-pn="me"]').click(),pg.wait_for_timeout(400))
    room()
    ok(f'{name} 내 방 = 위젯 보관함',pg.locator('.myroom').count()==1 and pg.locator('.myroom h3').all_text_contents()==['내가 만든 위젯','담아 온 위젯'])
    ok(f'{name} 자유 배치 판은 내 방에 없음',pg.locator('.myroom section.room,.myroom .rm-it').count()==0)
    # 위젯 만들기(코드 붙여 넣기)
    pg.locator('.myroom [data-wf-add]').click();pg.wait_for_timeout(300)
    pg.locator('[data-wt="paste"]').click();pg.fill('#wf-code',HTML);pg.fill('#wf-title','인사 위젯') if pg.locator('#wf-title').count() else None
    pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
    ok(f'{name} 만든 위젯이 내 방에',pg.locator('.myroom .mr-sec').first.locator('.wf-card').count()==1)
    # 피드 예시를 내 방에 담기
    pg.locator('[data-mr-feed]').click();pg.wait_for_timeout(500)
    ok(f'{name} 담아 온 게 없으면 위젯 둘러보기 → 위젯 피드',pg.locator('.wfeed:not(.myroom) .wf-card').count()>0)
    pg.locator('.wf-card:not([data-wf^="w"]) [data-wf-open]').first.click() if False else pg.locator('.wf-card [data-wf-open]').filter(has_text='무가당 예시').first.click();pg.wait_for_timeout(500)
    ok(f'{name} 남의(예시) 위젯 크게 보기에 내 방에 담기',pg.locator('[data-ws-toggle]').count()==1 and '담기' in pg.locator('[data-ws-toggle]').inner_text())
    pg.locator('[data-ws-toggle]').click();pg.wait_for_timeout(300);ok(f'{name} 담으면 빼기로 바뀜','빼기' in pg.locator('[data-ws-toggle]').inner_text())
    closeall(pg);room()
    ok(f'{name} 담아 온 위젯이 내 방에',pg.locator('.myroom .mr-sec').nth(1).locator('.wf-card').count()==1)
    ok(f'{name} 저장',len(pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).wsaved||[]"))==1)
    # 배치는 내 공간 편집: 편집에 ＋ 추가가 보이고, 꺼낸 조각은 내 공간 글 위에
    me();pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(400)
    ok(f'{name} 내 공간 편집에 ＋ 추가',pg.locator('.se-bar [data-se-add]').is_visible())
    ok(f'{name} ERR',not errs,errs);pg.context.close()
