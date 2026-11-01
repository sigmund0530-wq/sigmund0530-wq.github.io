# 내 공간 덩어리 쌓기 + 틀 고르기: 편집 막대(옮기기·넓이·휴대폰 숨김·빼기) · 덩어리 넣기(문장·위젯) · 틀 · 저장·되돌리기 · 휴대폰 제한
from base import *
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
LAY="JSON.parse(localStorage.getItem('mgd2.v1.layout.desktop'))"
def blocks(pg):return pg.evaluate(f"({LAY}.blocks||[]).map(b=>b.type+(b.w==='half'?'/h':'')+(b.mHide?'/m':''))")
def order(pg):return pg.evaluate("[...document.querySelectorAll('.hb-grid > .hb')].map(b=>b.className.split(' ')[1].slice(3))")
with sync_playwright() as p:
  b=p.chromium.launch()
  pg=setup(b,False);errs=pg.errs
  write(pg,False,'첫 글','본문');closeall(pg);pg.wait_for_timeout(300)
  pg.locator('.pc-nav [data-pn="me"]').click();pg.wait_for_timeout(400)
  ok(pg.locator('.hb-grid .hb-posts').count()==1,'내 공간 본문이 덩어리로')
  pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(400)
  ok(pg.locator('.hb-edit .hb-bar').count()>=2,'편집 중 덩어리마다 막대')
  ok(pg.locator('.hb-posts [data-hb-x]').count()==0,'글 목록은 뺄 수 없음')
  # 문장 덩어리 넣기
  pg.locator('.se-bar [data-se-add]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem',name='덩어리 · 문장').click();pg.wait_for_timeout(200)
  pg.locator('.dialog textarea,.dialog input').first.fill('오늘의 한 줄');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(300)
  ok(order(pg)[0]=='quote','문장 덩어리가 맨 위에',order(pg))
  # 아래로 옮기기
  pg.locator('.hb-quote').first.evaluate("n=>n.closest('.hb').querySelector('[data-hb-down]').click()");pg.wait_for_timeout(300)
  ok(order(pg)[1]=='quote','↓로 한 칸 내림',order(pg))
  # 끌어서 맨 아래로
  pg.locator('.hb.hb-quote [data-hb-grip]').scroll_into_view_if_needed();pg.wait_for_timeout(200)
  g=pg.locator('.hb.hb-quote [data-hb-grip]').bounding_box();lk=pg.locator('.hb.hb-lookback').bounding_box()
  pg.mouse.move(g['x']+5,g['y']+5);pg.mouse.down();pg.mouse.move(g['x']+5,lk['y']+lk['height']-3,steps=8);pg.wait_for_timeout(100);pg.mouse.up();pg.wait_for_timeout(400)
  ok(order(pg)[2]=='quote','⠿ 끌어서 지난 오늘 아래로',order(pg))
  # 반 칸 · 휴대폰 숨김
  pg.locator('.hb-quote').first.evaluate("n=>n.closest('.hb').querySelector('[data-hb-w]').click()");pg.wait_for_timeout(250)
  pg.locator('.hb-quote').first.evaluate("n=>n.closest('.hb').querySelector('[data-hb-m]').click()");pg.wait_for_timeout(250)
  # 위젯 덩어리: 내 방에 하나 담고
  # 틀 고르기
  pg.locator('[data-hb-tpl]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem').filter(has_text='잡지형').click();pg.wait_for_timeout(400)
  bl=blocks(pg);ok(bl[:2]==['lookback/h','board/h'] and 'posts' in bl and any(x.startswith('quote') for x in bl),'잡지형 틀: 두 칸 + 넣어 둔 문장은 남음',bl)
  pg.locator('.se-bar [data-se-undo]').click();pg.wait_for_timeout(300);ok(blocks(pg)!=bl,'되돌리기')
  pg.locator('[data-hb-tpl]').click();pg.wait_for_timeout(200);pg.get_by_role('menuitem').filter(has_text='사진첩형').click();pg.wait_for_timeout(300)
  pg.locator('.se-bar [data-se-save]').click();pg.wait_for_timeout(400)
  ok(pg.evaluate(f"{LAY}.homeView")=='album' and pg.locator('.nv-album').count()==1,'사진첩형: 글이 사진첩 보기로')
  ok(pg.locator('.hb-edit').count()==0 and pg.locator('.hb-q').count()==1,'저장 뒤 편집 막대 없음, 문장 보임')
  pg.reload();pg.wait_for_timeout(800);pg.locator('.pc-nav [data-pn="me"]').click();pg.wait_for_timeout(300)
  ok(pg.locator('.hb-q').count()==1 and pg.locator('.nv-album').count()==1,'새로 열어도 그대로')
  # 휴대폰: 같은 기록을 휴대폰 크기로 → 반 칸은 한 칸, 휴대폰 숨김은 안 보임
  st=pg.evaluate("Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('mgd2')).map(k=>[k,localStorage.getItem(k)]))")
  ctx=b.new_context(viewport={'width':390,'height':800},has_touch=True);ctx.add_init_script("const s="+__import__('json').dumps(st)+";for(const k in s)localStorage.setItem(k,s[k])")
  m=ctx.new_page();m.goto('http://127.0.0.1:8820/app.html');m.wait_for_timeout(900)
  if m.locator('[data-tab2="me"]').count():m.locator('[data-tab2="me"]').click();m.wait_for_timeout(400)
  ok(m.locator('.hb-q').count()==0,'휴대폰: 숨긴 덩어리 안 보임')
  ok(m.locator('.hb-grid .hb-posts').count()==1,'휴대폰: 글 목록은 보임')
  m.locator('[data-se-begin]:visible').first.click();m.wait_for_timeout(400)
  ok(m.locator('.hb-edit .hb-q').count()==1 and m.locator('.hb-edit [data-hb-w]').count()==0,'휴대폰 편집: 숨긴 것도 흐리게 보이고, 넓이 버튼은 없음')
  ok(not errs,'ERR',errs)
