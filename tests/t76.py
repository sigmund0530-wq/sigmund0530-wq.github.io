# 사진 꾹 눌러 옮기기(손가락): 꾹 → 그대로 떼면 메뉴 · 꾹 → 끌어서 글 위에 놓으면 그 자리로 · 다른 사진 옆에 놓으면 같은 줄 · 짧게 누르면 고르기
from base import *
import base64
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
P1=base64.b64encode(open('p1.jpg','rb').read()).decode();P2=base64.b64encode(open('p2.jpg','rb').read()).decode()
PASTE="""async(b64)=>{const bin=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const f=new File([bin],'x.jpg',{type:'image/jpeg'});const dt=new DataTransfer();dt.items.add(f);const a=[...document.querySelectorAll('.blocks .rte-area')].pop();a.focus();const s=getSelection();s.selectAllChildren(a);s.collapseToEnd();a.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}"""
EV="""([type,x,y])=>{const t=document.elementFromPoint(x,y)||document.body;t.dispatchEvent(new PointerEvent(type,{bubbles:true,cancelable:true,clientX:x,clientY:y,pointerType:'touch',pointerId:7}))}"""
def order(pg):return pg.evaluate("[...document.querySelectorAll('.blocks > *')].map(e=>e.classList.contains('pblock')?'P'+e.querySelectorAll('.ph-item').length:(e.textContent.trim()?'T':'t'))")
def center(pg,sel,i=0):bb=pg.locator(sel).nth(i).bounding_box();return bb['x']+bb['width']/2,bb['y']+bb['height']/2
with sync_playwright() as p:
  b=p.chromium.launch()
  pg=setup(b,True);errs=pg.errs
  pg.locator('[data-tab2="write"]').click();pg.wait_for_timeout(400)
  pg.locator('input[id^="f-title-"]').fill('옮기기');pg.locator('.blocks .rte-area').first.click()
  pg.keyboard.type('첫째 줄이에요');pg.keyboard.press('Enter');pg.keyboard.type('둘째 줄이에요');pg.keyboard.press('Enter');pg.keyboard.type('셋째 줄 ')
  pg.evaluate(PASTE,P1);pg.wait_for_timeout(900)
  o0=order(pg);ok(o0[-2]=='P1' or 'P1' in o0,'사진 들어감',o0)
  # 1) 꾹 누르고 그대로 떼면 메뉴
  x,y=center(pg,'.blocks .pblock [data-phm]');pg.evaluate(EV,['pointerdown',x,y]);pg.wait_for_timeout(600)
  ok(pg.locator('.ph-item.ps-lift').count()==1,'꾹 누르면 사진이 들림')
  pg.evaluate(EV,['pointerup',x,y]);pg.wait_for_timeout(300);ok(pg.locator('.menu').count()==1,'그대로 떼면 메뉴')
  pg.keyboard.press('Escape');pg.wait_for_timeout(150)
  if pg.locator('.menu').count():pg.mouse.click(3,3);pg.wait_for_timeout(200)
  # 2) 꾹 → 끌어서 첫째 줄 위에 놓기
  x,y=center(pg,'.blocks .pblock [data-phm]');tb=pg.locator('.blocks .rte-area').first.bounding_box();tx,ty=tb['x']+40,tb['y']+tb['height']/2
  pg.evaluate(EV,['pointerdown',x,y]);pg.wait_for_timeout(600)
  for k in range(1,9):pg.evaluate(EV,['pointermove',x+(tx-x)*k/8,y+(ty-y)*k/8]);pg.wait_for_timeout(30)
  ok(pg.locator('.ps-ghost').count()==1,'끄는 동안 사진 그림자가 따라옴')
  ok(pg.locator('.rte-area.drop-text').count()==1,'놓을 자리 표시')
  pg.evaluate(EV,['pointerup',tx,ty]);pg.wait_for_timeout(500)
  o1=order(pg);ok(pg.locator('.ps-ghost').count()==0 and pg.locator('.menu').count()==0,'놓으면 그림자 사라지고 메뉴 없음')
  ok(o1.index('P1')<=2,'사진이 위로 옮겨짐',(o0,o1))
  ok('첫째 줄이에요' in pg.locator('.blocks').inner_text() and '셋째 줄' in pg.locator('.blocks').inner_text(),'글은 그대로')
  # 3) 두 번째 사진을 넣고, 첫 사진 옆으로 끌면 같은 줄
  pg.evaluate(PASTE,P2);pg.wait_for_timeout(900);n_before=pg.locator('.blocks .pblock').count()
  pg.evaluate("(()=>{const ps=document.querySelectorAll('.blocks .pblock');ps[ps.length-1].scrollIntoView({block:'end'})})()");pg.wait_for_timeout(300)
  x,y=center(pg,'.blocks .pblock [data-phm]',n_before-1);fx,fy=center(pg,'.blocks .pblock [data-phm]',0);fx+=40
  pg.evaluate(EV,['pointerdown',x,y]);pg.wait_for_timeout(600)
  for k in range(1,9):pg.evaluate(EV,['pointermove',x+(fx-x)*k/8,y+(fy-y)*k/8]);pg.wait_for_timeout(30)
  pg.evaluate(EV,['pointerup',fx,fy]);pg.wait_for_timeout(500)
  ok(any(o=='P2' for o in order(pg)),'다른 사진 옆에 놓으면 한 줄에 두 장',order(pg))
  # 4) 짧게 누르면 고르기만
  pg.locator('.blocks .pblock [data-phm]').first.tap();pg.wait_for_timeout(300);ok(pg.locator('.pblock.pw-sel').count()==1 and pg.locator('.menu').count()==0,'짧게 누르면 고르기')
  # 5) 저장해도 순서 유지
  pg.locator('.hpub').click();pg.wait_for_timeout(300);pg.locator('input[name="pv"][value="private"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
  post=[x for x in pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts") if x.get('title')=='옮기기'][0]
  bt=[b['type'] for b in post['bodyJson']['blocks']];ok(bt.index('photos')<=1,'발행해도 옮긴 자리 그대로',bt)
  ok(not errs,'ERR',errs)
