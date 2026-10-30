# 그림 단위로 고르고 옮기기: 묶음, 고르기·옮기기·크기·복제·지우기·순서, 그림 고치기(다른 그림 안 바뀜), 저장 후 유지, 예전 그림 보존
from base import *
G="JSON.stringify((()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.autosave.edit:new')||'null');return 0})())"
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob)
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
    pg.locator('input[id^="f-title-"]').fill('그림 두 개')
    a=pg.locator('.win .rte-area').first;a.click();pg.keyboard.type('첫 줄입니다.');
    for _ in range(6):pg.keyboard.press('Enter')
    pg.keyboard.type('마지막 줄.')
    def draw_mode():
      if mob:pg.locator('.rte-bar [aria-label="더 보기"]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem',name='그리기').click()
      else:pg.click('[data-x-draw]')
      pg.wait_for_timeout(250)
    bb=a.bounding_box()
    def stroke(x1,y1,x2,y2):pg.mouse.move(bb['x']+x1,bb['y']+y1);pg.mouse.down();pg.mouse.move(bb['x']+x2,bb['y']+y2,steps=8);pg.mouse.up();pg.wait_for_timeout(80)
    draw_mode();stroke(30,60,120,60);stroke(30,80,120,80);pg.click('.ink-bar [data-idone]');pg.wait_for_timeout(250)
    assert pg.locator('.ink-sel').count()==1,'finished drawing is selected as one picture'
    draw_mode();stroke(200,100,280,140);pg.click('.ink-bar [data-idone]');pg.wait_for_timeout(250)
    ink=lambda:pg.evaluate("(()=>{const w=[...document.querySelectorAll('.win')].pop();let n=w;while(n&&!n._pfwCtx)n=n.querySelector('form')?.parentElement||null;return null})()")
    getink=lambda:pg.evaluate("(()=>{for(const el of document.querySelectorAll('.win *')){if(el._pfwCtx)return el._pfwCtx.draft.ink}return null})()")
    d=getink();gs=[];[gs.append(s['g']) for s in d if s['g'] not in gs]
    assert len(d)==3 and len(gs)==2,(len(d),gs)
    # 바깥을 누르면 선택이 풀리고 글쓰기
    pg.mouse.click(bb['x']+bb['width']-20,bb['y']+10);pg.wait_for_timeout(150);assert pg.locator('.ink-sel').count()==0
    # 첫 그림 고르기 → 옮기기
    pg.mouse.click(bb['x']+75,bb['y']+60);pg.wait_for_timeout(150);assert pg.locator('.ink-sel').count()==1
    before=getink();sel=pg.locator('.ink-sel').bounding_box()
    pg.mouse.move(sel['x']+sel['width']/2,sel['y']+sel['height']/2);pg.mouse.down();pg.mouse.move(sel['x']+sel['width']/2+40,sel['y']+sel['height']/2+30,steps=6);pg.mouse.up();pg.wait_for_timeout(150)
    after=getink()
    g1=before[0]['g']
    assert all(x['p']!=y['p'] for x,y in zip(before,after) if x['g']==g1),'group1 moved'
    assert [x for x in before if x['g']!=g1]==[x for x in after if x['g']!=g1],'other picture unchanged'
    # 크기: 오른쪽 아래 손잡이
    h=pg.locator('.ink-sel .ink-h.se').bounding_box();w0=pg.locator('.ink-sel').bounding_box()['width']
    pg.mouse.move(h['x']+h['width']/2,h['y']+h['height']/2);pg.mouse.down();pg.mouse.move(h['x']+60,h['y']+30,steps=6);pg.mouse.up();pg.wait_for_timeout(150)
    w1=pg.locator('.ink-sel').bounding_box()['width'];assert w1>w0+30,(w0,w1)
    s0=[x['s'] for x in after if x['g']==g1][0];s1=[x['s'] for x in getink() if x['g']==g1][0];assert s1>s0,'stroke width scales'
    # 복제 → 지우기 → 되돌리기
    pg.locator('.ink-sel-bar [data-a="dup"]').click();pg.wait_for_timeout(150)
    n=lambda:len({s['g'] for s in getink()});assert n()==3
    pg.locator('.ink-sel-bar [data-a="del"]').click();pg.wait_for_timeout(150);assert n()==2 and pg.locator('.ink-undo').count()==1
    pg.locator('.ink-undo button').click();pg.wait_for_timeout(150);assert n()==3
    # 순서: 뒤로 → 맨 앞 선은 이 그림 것
    pg.mouse.click(bb['x']+bb['width']-20,bb['y']+10);pg.mouse.click(bb['x']+240,bb['y']+120);pg.wait_for_timeout(150)
    g2=[s['g'] for s in getink() if s['p'][0][0]*0+1][2] if False else None
    selg=pg.evaluate("(()=>{for(const el of document.querySelectorAll('.win *')){if(el._pfwCtx)return el._pfwCtx._sel}return null})()")
    assert selg and selg!=g1
    pg.locator('.ink-sel-bar [data-a="down"]').click();pg.wait_for_timeout(100);assert getink()[0]['g']==selg
    pg.locator('.ink-sel-bar [data-a="up"]').click();pg.wait_for_timeout(100);assert getink()[-1]['g']==selg
    # 그림 고치기: 지우개가 다른 그림을 지우지 않음
    pg.locator('.ink-sel-bar [data-a="edit"]').click();pg.wait_for_timeout(200);assert pg.locator('.ink-bar').count()==1 and '이 그림만' in pg.locator('.ink-bar').inner_text()
    pre=getink();cnt=len(pre);pg.click('.ink-bar [data-it="er"]')
    # 첫 그림(다른 그림) 위를 지우개로
    pth=pg.locator('.win svg.ink-ed path').first.bounding_box();pg.mouse.move(pth['x']+5,pth['y']+pth['height']/2);pg.mouse.down();pg.mouse.move(pth['x']+pth['width']-5,pth['y']+pth['height']/2,steps=6);pg.mouse.up();pg.wait_for_timeout(100)
    others=lambda:[x for x in getink() if x['g']!=selg]
    assert len(others())==len([x for x in pre if x['g']!=selg]),'eraser keeps other pictures'
    pg.click('.ink-bar [data-it="pen"]');stroke(220,160,260,170);assert getink()[-1]['g']==selg and len([x for x in getink() if x['g']==selg])>=1,'new line joins this picture'
    pg.click('.ink-bar [data-idone]');pg.wait_for_timeout(200)
    # 글쓰기 계속
    pg.mouse.click(bb['x']+bb['width']-20,bb['y']+10);a.click();pg.keyboard.press('Control+End');pg.keyboard.type(' 덧붙임');pg.wait_for_timeout(150)
    assert '덧붙임' in a.inner_text()
    final=getink();ng=len({x['g'] for x in final})
    pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
    r=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(p=>p.title==='그림 두 개')")
    assert len({s['g'] for s in r['ink']})==ng and len(r['ink'])==len(final),'saved with groups'
    # 예전 그림(묶음 없음)은 통째로 하나
    pg.evaluate("(()=>{const k='mgd2.v1.records',R=JSON.parse(localStorage.getItem(k));const p=R.posts.find(p=>p.title==='그림 두 개');p.ink.forEach(s=>delete s.g);localStorage.setItem(k,JSON.stringify(R))})()")
    pg.reload();pg.wait_for_timeout(500)
    pid=r['id'];pg.evaluate(f"(()=>{{const b=document.querySelector('[data-open-post=\"{pid}\"]');b&&b.click()}})()");pg.wait_for_timeout(300)
    if pg.locator('.txt:visible').count()==0:
      if mob:pg.locator('[data-tab2="me"]').click();pg.wait_for_timeout(250)
      pg.locator(f'[data-open-post="{pid}"]').first.click();pg.wait_for_timeout(400)
    pg.locator('button:has-text("수정"):visible').last.click();pg.wait_for_timeout(500)
    d2=getink();assert len(d2)==len(final) and len({s['g'] for s in d2})==1,'legacy lines kept as one picture'
    assert not pg.errs,pg.errs
    print('OK','mobile' if mob else 'PC','group, select, move, resize, dup/del/undo, order, edit-only-this, save, legacy')
    pg.context.close()
  b.close()
