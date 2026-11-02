# 내 공간 자유 배치(2026-11-02): 끌기·자석 안내선·크기·돌리기·여럿 맞춤·틀·PC/휴대폰 따로·빼기·저장
import json
from base import *
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
FL="JSON.parse(localStorage.getItem('mgd2.v1.layout.desktop')).fl"
def it(pg,dev,id):return pg.evaluate(f"(()=>{{const f={FL};return (f.{dev}&&f.{dev}.items.find(i=>i.id===%s))||null}})()"%json.dumps(id))
def ids(pg,dev):return pg.evaluate(f"{FL}.{dev}.items.map(i=>i.id)")
def drag(pg,x,y,dx,dy,mid=None,alt=False):
  pg.mouse.move(x,y);
  if alt:pg.keyboard.down('Alt')
  pg.mouse.down();pg.mouse.move(x+dx,y+dy,steps=10)
  if mid:mid()
  pg.mouse.up()
  if alt:pg.keyboard.up('Alt')
  pg.wait_for_timeout(300)
with sync_playwright() as p:
  b=p.chromium.launch();pg=setup(b,False);errs=pg.errs
  write(pg,False,'망원시장 산책','오늘은 고로케를 샀다','p1.jpg');closeall(pg)
  pg.locator('.pc-nav [data-pn="me"]').click();pg.wait_for_timeout(400)
  ok(pg.locator('.fl-canvas').count()==1,'내 공간이 한 장의 판')
  ok(all(pg.locator(f'.fl-box[data-id="{k}"]').count()==1 for k in ['cover','title','profile','menu','posts']),'커버·이름·프로필·메뉴·글 목록이 모두 조각')
  pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(400)
  # 문장 넣기 → 바로 골라짐
  pg.locator('.se-bar [data-se-add]').click();pg.get_by_role('menuitem',name='문장').click();pg.locator('.dialog textarea,.dialog input').first.fill('천천히, 날것 그대로');pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(400)
  qid=pg.evaluate("document.querySelector('.fl-box.sel')?.dataset.id")
  ok(qid and pg.locator('.fl-tb').count()==1,'넣은 문장이 골라지고 막대가 보임',qid)
  # 끌기: 가운데 근처로 → 안내선 보이고 판 가운데에 착 붙음
  cv=pg.locator('.fl-canvas').bounding_box();s=pg.evaluate("+document.querySelector('.fl-canvas').dataset.s")
  q=it(pg,'pc',qid);bb=pg.locator(f'.fl-box[data-id="{qid}"]').bounding_box()
  target=cv['x']+540*s-(q['x']+q['w']/2)*s+3  # 가운데에서 3px 비킨 곳
  seen={}
  drag(pg,bb['x']+20,bb['y']+bb['height']/2,target,140,mid=lambda:seen.update(g=pg.locator('.fl-guides .fl-g').count()))
  q=it(pg,'pc',qid);ok(seen.get('g',0)>0,'끄는 동안 안내선이 보임',seen);ok(abs(q['x']+q['w']/2-540)<=1,'판 가운데에 착 붙음',q['x']+q['w']/2)
  # Alt: 자석 끔
  bb=pg.locator(f'.fl-box[data-id="{qid}"]').bounding_box();x0=q['x']
  drag(pg,bb['x']+20,bb['y']+bb['height']/2,3,0,alt=True);q=it(pg,'pc',qid)
  ok(q['x']!=x0 and abs(q['x']+q['w']/2-540)>1,'Alt를 누르면 자석 없이 그대로',q['x']-x0)
  # 글 목록 왼쪽 변에 맞추기(다른 조각 가장자리)
  pr=it(pg,'pc','posts');bb=pg.locator(f'.fl-box[data-id="{qid}"]').bounding_box()
  drag(pg,bb['x']+20,bb['y']+bb['height']/2,(pr['x']-q['x'])*s+4,0);q=it(pg,'pc',qid)
  ok(q['x']==pr['x'],'다른 조각의 왼쪽 변에 착 붙음',q['x'],pr['x'])
  # 크기: 오른쪽 손잡이
  w0=q['w'];h=pg.locator(f'.fl-box[data-id="{qid}"] .fl-h-e');hb=h.bounding_box()
  seen={}
  drag(pg,hb['x']+hb['width']/2,hb['y']+hb['height']/2,-80,0,mid=lambda:seen.update(t=pg.locator('.fl-size').count() and pg.locator('.fl-size').inner_text()))
  q=it(pg,'pc',qid);ok(q['w']<w0-50,'손잡이로 너비 줄이기',w0,q['w']);ok(bool(seen.get('t')),'끄는 동안 크기 숫자',seen)
  # 돌리기 → 바로 세우기
  rh=pg.locator(f'.fl-box[data-id="{qid}"] .fl-rot').bounding_box();bb=pg.locator(f'.fl-box[data-id="{qid}"]').bounding_box()
  drag(pg,rh['x']+rh['width']/2,rh['y']+rh['height']/2,bb['width']/2,bb['height']/2+40);q=it(pg,'pc',qid)
  r=q.get('r',0);ok(r!=0 and (r%15==0 or abs(r-round(r/15)*15)>5),'돌리기(15도 근처면 착)',r)
  pg.locator(f'.fl-box[data-id="{qid}"]').click();pg.wait_for_timeout(200)
  pg.locator('.fl-tb [data-fl="unrot"]').click();pg.wait_for_timeout(300);ok(it(pg,'pc',qid).get('r',0)==0,'바로 세우기')
  # 여럿 고르기 → 왼쪽 맞춤
  pg.locator(f'.fl-box[data-id="{qid}"]').click();pg.wait_for_timeout(200)
  pg.locator('.fl-box[data-id="title"]').click(modifiers=['Shift']);pg.wait_for_timeout(300)
  ok(pg.locator('.fl-box.sel').count()==2 and pg.locator('.fl-tb [data-fl="al-l"]').count()==1,'Shift로 둘 고르면 맞춤 단추')
  pg.locator('.fl-tb [data-fl="al-r"]').click();pg.wait_for_timeout(300)
  a,t=it(pg,'pc',qid),it(pg,'pc','title');ok(a['x']+a['w']==t['x']+t['w'],'오른쪽 맞춤',a['x']+a['w'],t['x']+t['w'])
  # 되돌리기
  pg.locator('[data-se-undo]').click();pg.wait_for_timeout(300);a2=it(pg,'pc',qid);ok(a2['x']+a2['w']!=t['x']+t['w'],'되돌리기')
  # 휴대폰 배치: 따로
  pcx=it(pg,'pc',qid)['x']
  pg.locator('[data-fl-dev="m"]').click();pg.wait_for_timeout(500)
  ok(pg.locator('.fl-canvas.fl-phone').count()==1 and round(pg.locator('.fl-canvas').bounding_box()['width'])==390,'휴대폰 배치는 휴대폰 너비 판에서')
  mq=it(pg,'m',qid);ok(mq is not None,'PC에서 넣은 문장이 휴대폰 배치에도 생김')
  pg.locator(f'.fl-box[data-id="{qid}"]').scroll_into_view_if_needed();pg.wait_for_timeout(200)
  bb=pg.locator(f'.fl-box[data-id="{qid}"]').bounding_box();drag(pg,bb['x']+10,bb['y']+bb['height']/2,0,-60)
  ok(it(pg,'m',qid)['y']!=mq['y'] and it(pg,'pc',qid)['x']==pcx,'휴대폰에서 옮겨도 PC 배치는 그대로')
  pg.locator(f'.fl-box[data-id="{qid}"]').click();pg.wait_for_timeout(200);pg.locator('.fl-tb [data-fl="del"]').click();pg.wait_for_timeout(300)
  ok(it(pg,'m',qid) is None and it(pg,'pc',qid) is not None,'휴대폰에서 빼도 PC에는 남음')
  # 다시 PC → 틀: 잡지형
  pg.locator('[data-fl-dev="pc"]').click();pg.wait_for_timeout(400)
  pg.locator('[data-hb-tpl]').click();pg.get_by_role('menuitem').filter(has_text='잡지형').click();pg.wait_for_timeout(400)
  ok(it(pg,'pc','cover')['w']==620 and it(pg,'pc',qid) is not None,'잡지형 틀: 커버 옆에 프로필, 넣은 문장은 그대로')
  # 빈 곳을 끌어 네모로 여럿 고르기
  pg.locator('.fl-box[data-id="menu"]').scroll_into_view_if_needed();cvb=pg.locator('.fl-canvas').bounding_box()
  pg.mouse.click(cvb['x']+cvb['width']-6,cvb['y']+cvb['height']-6);pg.wait_for_timeout(200)
  pg.locator('[data-se-save]').click();pg.wait_for_timeout(400)
  pg.reload();pg.wait_for_timeout(900);pg.locator('.pc-nav [data-pn="me"]').click();pg.wait_for_timeout(400)
  ok(pg.locator(f'.fl-box[data-id="{qid}"] .hb-q').count()==1 and abs(pg.locator('.fl-box[data-id="cover"]').bounding_box()['width']-620*s)<2,'다시 열어도 그대로')
  ok(pg.locator('.fl-h,.fl-tb,.fl-guides').count()==0,'보는 화면엔 손잡이·막대 없음')
  # 휴대폰: 휴대폰 배치로 보임, 탭하면 고르기
  st=pg.evaluate("Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('mgd2')).map(k=>[k,localStorage.getItem(k)]))")
  ctx=b.new_context(viewport={'width':390,'height':800},has_touch=True);ctx.add_init_script("const s="+json.dumps(st)+";for(const k in s)localStorage.setItem(k,s[k])")
  m=ctx.new_page();m.on('pageerror',lambda e:errs.append(str(e)));m.goto(U);m.wait_for_timeout(900)
  if m.locator('[data-tab2="me"]').count():m.locator('[data-tab2="me"]').click();m.wait_for_timeout(400)
  ok(m.locator(f'.fl-box[data-id="{qid}"]').count()==0 and m.locator('.fl-box[data-id="posts"]').count()==1,'휴대폰: 휴대폰 배치로(뺀 문장은 없음)')
  ok(m.locator('.fl-box[data-id="menu"]').count()==0,'휴대폰엔 PC 메뉴 조각 없음')
  m.locator('[data-se-begin]:visible').first.tap();m.wait_for_timeout(400)
  m.locator('.fl-box[data-id="profile"]').tap();m.wait_for_timeout(300)
  ok(m.locator('.fl-box.sel').count()==1 and m.locator('.fl-tb [data-fl="multi"]').count()==1,'휴대폰 편집: 눌러 고르기 + 여럿 고르기 단추')
  m.locator('.se-bar [data-se-add]').tap();m.get_by_role('menuitem',name='다시 넣기 · 문장 ‘천천히, 날것 그대로’').tap();m.wait_for_timeout(300)
  ok(m.locator(f'.fl-box[data-id="{qid}"]').count()==1,'뺀 조각은 ＋ 추가의 다시 넣기로')
  ok(not errs,'ERR',errs)
print('fails',fails)
