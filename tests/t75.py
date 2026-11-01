# 사진·짤 크기: 손잡이 끌기(5% 단위·% 표시) · 사진 메뉴 '크기' · 키보드 · 저장 후 유지 · 읽는 화면 가운데로 좁힘 · 원래대로면 저장 안 함
from base import *
import base64
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
PNG=base64.b64encode(open('p1.jpg','rb').read()).decode()
PASTE="""async(b64)=>{const bin=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const f=new File([bin],'x.jpg',{type:'image/jpeg'});const dt=new DataTransfer();dt.items.add(f);const a=document.querySelector('.blocks .rte-area');a.focus();a.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}"""
def pw(pg):return pg.evaluate("(()=>{const pb=document.querySelector('.blocks .pblock');const pe=pb.querySelector('.prow-edit');const cs=getComputedStyle(pb);return Math.round(pe.getBoundingClientRect().width/(pb.getBoundingClientRect().width-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight))*100)})()")
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400)
    pg.locator('input[id^="f-title-"]').fill('크기 글');pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('짤 하나 ')
    pg.evaluate(PASTE,PNG);pg.wait_for_timeout(900)
    ok(pg.locator('.blocks .pblock .pw-h').count()==1 and not pg.locator('.blocks .pblock .pw-h').first.is_visible() or pg.evaluate("getComputedStyle(document.querySelector('.blocks .pblock .pw-h')).opacity")=='0',tag+' 고르기 전엔 손잡이 안 보임')
    pg.locator('.blocks .pblock [data-phm]').first.click();pg.wait_for_timeout(300)
    ok(pg.locator('.pblock.pw-sel').count()==1 and pg.locator('.pblock.pw-sel .pw-h').count()==4,tag+' 가볍게 누르면 골라지고 네 모서리 손잡이')
    ok(pg.locator('.menu').count()==0,tag+' 가볍게 누르면 메뉴는 안 뜸')
    ok((pg.locator('.ps-more').count()==1)==(not mob),tag+' PC는 ⋯ 버튼, 휴대폰은 꾹 누르기')
    ok(pw(pg)==100,tag+' 처음엔 꽉 차게',pw(pg))
    pg.locator('.blocks .pblock').scroll_into_view_if_needed();pg.wait_for_timeout(200)
    h=pg.locator('.blocks .pblock .pw-h:not(.pw-x)').bounding_box();pb=pg.locator('.blocks .pblock').bounding_box()
    sx,sy=h['x']+h['width']/2,h['y']+h['height']/2;mid=pb['x']+pb['width']/2;tx=mid+(sx-mid)*0.5
    pg.mouse.move(sx,sy);pg.mouse.down();pg.mouse.move((sx+tx)/2,sy,steps=4);pg.mouse.move(tx,sy,steps=4)
    tip=pg.locator('.pw-tip').inner_text() if pg.locator('.pw-tip').count() else '';pg.mouse.up();pg.wait_for_timeout(300)
    w=pw(pg);ok(40<=w<=60,tag+' 끌면 작아짐',w);ok(tip.endswith('%'),tag+' 끄는 동안 % 표시',tip)
    if mob:
      bb=pg.locator('.blocks .pblock [data-phm]').first.bounding_box();cx,cy=bb['x']+bb['width']/2,bb['y']+bb['height']/2
      pg.evaluate("([x,y])=>{const t=document.elementFromPoint(x,y);t.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,clientX:x,clientY:y,pointerType:'touch'}))}",[cx,cy]);pg.wait_for_timeout(700)
      pg.evaluate("([x,y])=>{const t=document.elementFromPoint(x,y);t.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,clientX:x,clientY:y,pointerType:'touch'}));t.click()}",[cx,cy]);pg.wait_for_timeout(300)
    else:
      pg.locator('.ps-more').click();pg.wait_for_timeout(300)
    labels=pg.locator('.menu button,[role=menuitem]').all_text_contents();ok(any('이 사진 빼기' in t for t in labels) and any('원래 크기로' in t for t in labels),tag+' 꾹 누르면 메뉴(빼기·원래 크기로)',labels)
    pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    if pg.locator('.menu').count():pg.mouse.click(3,3);pg.wait_for_timeout(200)
    if not mob:
      pg.locator('.blocks .pblock [data-phm]').first.click();pg.wait_for_timeout(200);pg.locator('.blocks .pblock .pw-h:not(.pw-x)').focus();pg.keyboard.press('ArrowRight');pg.keyboard.press('ArrowRight');pg.wait_for_timeout(200);ok(abs(pw(pg)-(w+10))<=2,tag+' 키보드로 5%씩',(w,pw(pg)))
    cur=pw(pg)
    pg.locator('.hpub').click();pg.wait_for_timeout(300);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
    post=[x for x in rec(pg)['posts'] if x.get('title')=='크기 글'][0];pbk=[x for x in post['bodyJson']['blocks'] if x['type']=='photos'][0]
    ok(abs(pbk.get('w',100)-cur)<=1,tag+' 크기 저장',pbk.get('w'))
    closeall(pg);pg.wait_for_timeout(200)
    pg.locator('.pc-row,.post-card,[data-open-post]').filter(has_text='크기 글').first.click();pg.wait_for_timeout(600)
    r=pg.evaluate("(()=>{const w=document.querySelector('.pw-wrap');if(!w)return null;return Math.round(w.getBoundingClientRect().width/w.parentElement.getBoundingClientRect().width*100)})()")
    ok(r is not None and abs(r-cur)<=3,tag+' 읽는 화면도 같은 크기',r)
    closeall(pg)
    # 원래대로 → 저장값 없음
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400)
    pg.locator('input[id^="f-title-"]').fill('원래 글');pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('하나 ')
    pg.evaluate(PASTE,PNG);pg.wait_for_timeout(900);pg.locator('.blocks .pblock [data-phm]').first.click(button='right');pg.wait_for_timeout(300)
    pg.keyboard.press('Escape');pg.wait_for_timeout(100)
    if pg.locator('.menu').count():pg.mouse.click(3,3);pg.wait_for_timeout(200)
    pg.locator('.blocks .pblock [data-phm]').first.click();pg.wait_for_timeout(200);pg.locator('.blocks .pblock .pw-h:not(.pw-x)').focus();[pg.keyboard.press('ArrowLeft') for _ in range(6)];pg.wait_for_timeout(200)
    pg.locator('.blocks .pblock [data-phm]').first.click(button='right');pg.wait_for_timeout(300)
    pg.locator('.menu button,[role=menuitem]').filter(has_text='원래 크기로').first.click();pg.wait_for_timeout(200)
    pg.locator('.hpub').click();pg.wait_for_timeout(300);pg.locator('input[name="pv"][value="private"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(600)
    post=[x for x in rec(pg)['posts'] if x.get('title')=='원래 글'][0];pbk=[x for x in post['bodyJson']['blocks'] if x['type']=='photos'][0]
    ok('w' not in pbk,tag+' 원래대로면 저장 안 함(예전 글과 같음)',pbk.keys())
    ok(not errs,tag+' ERR',errs);pg.context.close()
