# 글자 크기·색(2026-11-02): 고른 글자에 크기·색 → 저장·읽는 화면 유지, 다른 색, 색 없애기, 이상한 속성은 걸러짐, 펜 색 늘림·다른 색
import json
from base import *
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
SELECT="""(w)=>{const a=document.querySelector('.blocks .rte-area');const tw=document.createTreeWalker(a,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())){const i=n.data.indexOf(w);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+w.length);const s=getSelection();s.removeAllRanges();s.addRange(r);return true}}return false}"""
def html(pg):return pg.evaluate("document.querySelector('.blocks .rte-area').innerHTML")
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(500)
    pg.locator('input[id^="f-title-"]').fill('색 글');pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('오늘은 하늘이 정말 파랬다. 바람도 좋았다.')
    if mob:pg.locator('.t-btn').tap();pg.wait_for_timeout(200)
    ok(pg.locator('[data-fmt="fs"]').count()==1 and pg.locator('[data-fmt="tc"]').count()==1,tag+' 글자 꾸미기에 크기·색 단추')
    # 크기
    pg.evaluate(SELECT,'하늘이');pg.locator('[data-fmt="fs"]').click();pg.get_by_role('menuitem',name='아주 크게').click();pg.wait_for_timeout(200)
    ok('<span class="fs-xl">하늘이</span>' in html(pg),tag+' 고른 글자만 아주 크게',html(pg)[:120])
    # 정해 둔 색
    pg.evaluate(SELECT,'파랬다');pg.locator('[data-fmt="tc"]').click();pg.wait_for_timeout(200)
    ok(pg.locator('.fmt-pop .fmt-sw').count()==16,tag+' 색 16개(또렷한·흐린)')
    pg.locator('.fmt-pop [data-tc="blue"]').click();pg.wait_for_timeout(200)
    ok('<span class="tc-blue">파랬다</span>' in html(pg) and pg.locator('.fmt-pop').count()==0,tag+' 파랑 입힘',html(pg)[:160])
    # 다른 색 고르기
    pg.evaluate(SELECT,'바람도');pg.locator('[data-fmt="tc"]').click();pg.wait_for_timeout(200)
    pg.evaluate("()=>{const i=document.querySelector('.fmt-pop input[type=color]');i.value='#12ab34';i.dispatchEvent(new Event('change',{bubbles:true}))}");pg.wait_for_timeout(200)
    ok('color: rgb(18, 171, 52)' in html(pg),tag+' 다른 색 고르기',html(pg)[-140:])
    # 색 없애기
    pg.evaluate(SELECT,'파랬다');pg.locator('[data-fmt="tc"]').click();pg.locator('.fmt-pop [data-tc=""]').click();pg.wait_for_timeout(200)
    ok('tc-blue' not in html(pg),tag+' 색 없애기')
    pg.evaluate(SELECT,'파랬다');pg.locator('[data-fmt="tc"]').click();pg.locator('.fmt-pop [data-tc="red"]').click();pg.wait_for_timeout(200)
    # 글꼴
    pg.evaluate(SELECT,'좋았다');pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(200)
    ok(pg.locator('.fmt-fonts [data-ff]').count()==21 and '좋았다' in pg.locator('.fmt-fonts [data-ff="pen"] b').inner_text(),tag+' 글꼴 21개 + 기본, 고른 글자로 보여 줌')
    pg.locator('.fmt-fonts [data-ff="pen"]').click();pg.wait_for_timeout(200)
    ok('<span class="ff-pen">좋았다</span>' in html(pg),tag+' 펜 글씨 입힘')
    pg.evaluate(SELECT,'좋았다');pg.locator('[data-fmt="ff"]').click();ok(pg.locator('.fmt-fonts [data-ff="pen"].on').count()==1,tag+' 지금 글꼴 표시')
    pg.locator('.fmt-fonts [data-ff="myeongjo"]').click();pg.wait_for_timeout(200)
    ok('<span class="ff-myeongjo">좋았다</span>' in html(pg),tag+' 다른 글꼴로 바꾸면 겹치지 않음',html(pg)[-120:])
    # 발행 → 읽는 화면
    pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(800)
    post=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(p=>p.title==='색 글')");h=json.dumps(post['bodyJson'],ensure_ascii=False)
    ok('ff-myeongjo' in h and 'fs-xl' in h and 'tc-red' in h and 'rgb(18, 171, 52)' in h,tag+' 저장에 남음',h[:200])
    art=pg.locator('article.post').last
    ok(art.locator('span.fs-xl').count()==1 and art.locator('span.tc-red').count()==1,tag+' 읽는 화면에 크기·색')
    ok('Nanum Myeongjo' in pg.evaluate("getComputedStyle(document.querySelector('article.post span.ff-myeongjo')).fontFamily") and pg.locator('link#mf-myeongjo').count()==1,tag+' 읽는 화면에서 글꼴 받아 와 입힘')
    big=pg.evaluate("parseFloat(getComputedStyle(document.querySelector('article.post span.fs-xl')).fontSize)/parseFloat(getComputedStyle(document.querySelector('article.post .txt')).fontSize)")
    ok(1.5<big<1.7,tag+' 실제로 1.6배',big)
    ok(not errs,tag+' ERR',errs);pg.context.close()
  # 걸러내기: 위험한 속성은 지움
  pg=setup(b,False)
  # sanitize는 내부 함수라 글쓰기 저장으로 확인
  pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400);pg.locator('input[id^="f-title-"]').fill('거르기')
  pg.evaluate("""()=>{const a=document.querySelector('.blocks .rte-area');a.innerHTML='<span class="fs-l evil" onclick="x()" style="color:#123456;background:url(https://e.x)">가</span><span style="position:fixed">나</span><span class="tc-nope">다</span><span class="ff-pen ff-nope">라</span><span style="font-family:Evil">마</span>';a.dispatchEvent(new Event('input',{bubbles:true}))}""")
  pg.locator('.hpub').click();pg.wait_for_timeout(200);pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(800)
  h=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(p=>p.title==='거르기').bodyJson.blocks.map(b=>b.html||'').join('')")
  ok('fs-l' in h and 'rgb(18, 52, 86)' in h and 'evil' not in h and 'onclick' not in h and 'url(' not in h and 'fixed' not in h and 'tc-nope' not in h and 'ff-pen' in h and 'ff-nope' not in h and 'Evil' not in h and '가' in h and '나' in h and '다' in h,'정해 둔 크기·색만 남고 나머지는 지움',h)
  # 펜 색
  pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(400);pg.locator('.blocks .rte-area').first.click();pg.keyboard.type('그림')
  pg.locator('.win.editor [data-x-draw]').last.click();pg.wait_for_timeout(300)
  ok(pg.locator('.ink-bar [data-ic]').count()==16 and pg.locator('.ink-bar [data-ic-own]').count()==1,'펜 색 16개 + 다른 색 고르기')
  pg.evaluate("()=>{const i=document.querySelector('.ink-bar [data-ic-own]');i.value='#00aaff';i.dispatchEvent(new Event('input',{bubbles:true}))}")
  c=pg.locator('.win.editor .rte-area').first.bounding_box();pg.mouse.move(c['x']+20,c['y']+10);pg.mouse.down();pg.mouse.move(c['x']+150,c['y']+16,steps=6);pg.mouse.up();pg.wait_for_timeout(200)
  ok(pg.evaluate("[...document.querySelectorAll('.win.editor svg.ink-ed path')].some(p=>(p.getAttribute('stroke')||'').toLowerCase()==='#00aaff')"),'다른 색으로 그려짐')
  ok(not pg.errs,'ERR3',pg.errs)
print('fails',fails)
