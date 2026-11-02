# 자소로 설계 · 배치 · 점 고치기 (2026-11-02): 조각 점을 끌면 그 조각이 든 글자가 다 바뀌고, 꼴 상자, 윤곽 점 고치기, 발행하면 잘라 저장
import json
from base import *
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
SELECT="""(w)=>{const a=[...document.querySelectorAll('.blocks .rte-area')].pop();const tw=document.createTreeWalker(a,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())){const i=n.data.indexOf(w);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+w.length);const s=getSelection();s.removeAllRanges();s.addRange(r);return true}}return false}"""
REC="JSON.parse(localStorage.getItem('mgd2.v1.records'))"
FONT="JSON.parse(localStorage.getItem('mgd2.v1.records')).myFonts.find(f=>f.mode==='jamo')"
def html(pg):return pg.evaluate("[...document.querySelectorAll('.blocks .rte-area')].pop().innerHTML")
GLYPHS="""async(arg)=>{const [u,chars]=arg;await new Promise(r=>{if(window.opentype)return r();const s=document.createElement('script');s.src='vendor/opentype-1.3.4.min.js';s.onload=r;document.head.appendChild(s)});
  const f=opentype.parse(await (await fetch(u)).arrayBuffer());const o={};for(const ch of chars){const g=f.charToGlyph(ch);o[ch]=g&&g.index?JSON.stringify(g.path.commands).length:0}return o}"""
with sync_playwright() as p:
  b=p.chromium.launch()
  # 엔진: 한글 분해·조합(주소에 ?fontdev 일 때만 열리는 점검 창구)
  pg=b.new_page();pg.goto('http://127.0.0.1:8820/app.html?fontdev');pg.wait_for_timeout(800)
  r=pg.evaluate("""async()=>{const f={id:'ftst1',mode:'jamo',base:'gdodum',p:{},glyphs:{},own:{}};const t='가각뷁쀍똠ㄱㅏ';const buf=await window.__mgdFont.build(f,t);
    await new Promise(r=>{const s=document.createElement('script');s.src='vendor/opentype-1.3.4.min.js';s.onload=r;document.head.appendChild(s)});const F=opentype.parse(buf);const o={};for(const ch of t){const g=F.charToGlyph(ch);o[ch]=g&&g.index?g.path.commands.length:0}
    const f2=Object.assign({},f,{jamo:{'ㄱ':[{p:[[10,14],[84,14],[40,96]]}]}});const F2=opentype.parse(await window.__mgdFont.build(f2,'가나각'));const s=ch=>JSON.stringify(F.charToGlyph(ch).path.commands),s2=ch=>JSON.stringify(F2.charToGlyph(ch).path.commands);
    return {o,ga:s('가')!==s2('가'),gak:s('각')!==s2('각')}}""")
  ok(all(v>4 for v in r['o'].values()),'11,172자 조합: 가·각·뷁·쀍·똠·낱자 ㄱ·ㅏ 모두 모양 있음',r['o'])
  ok(r['ga'] and r['gak'],'ㄱ 조각을 고치면 초성(가)·받침(각) 모두 바뀜')
  pg.close()
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
    pg.wait_for_timeout(500);pg.locator('input[id^="f-title-"]').last.fill('자소 글');pg.locator('.blocks .rte-area').last.click();pg.keyboard.type('가나다 고구마 과자')
    if mob:pg.locator('.t-btn').tap();pg.wait_for_timeout(200)
    pg.evaluate(SELECT,'가나다 고구마');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-room]').click();pg.wait_for_timeout(700);pg.locator('.mr-fonts [data-uf-make]').click();pg.wait_for_timeout(1500)
    ok(pg.locator('[data-fm-base="@jamo"]').count()==1,tag+' 시작 화면에 자소로 설계')
    pg.locator('[data-fm-base="@jamo"]').click();pg.wait_for_timeout(800)
    ok(pg.locator('[data-fm-tab]').count()==4 and pg.locator('[data-fm-p="jw"]').count()==1 and pg.locator('[data-fm-cap]').count()==3,tag+' 탭 넷(전체 모양·자소·배치·글자 고치기), 획 두께·획 끝')
    pg.locator('[data-fm-p="jw"]').fill('110');pg.locator('[data-fm-cap="square"]').click();pg.wait_for_timeout(1500)
    ok(pg.evaluate("[...document.fonts].some(f=>f.family.startsWith('mgdt_')&&f.status==='loaded')") and pg.evaluate("getComputedStyle(document.querySelector('[data-fm-out]')).fontFamily").startswith('mgdt_'),tag+' 써 보기가 자소 글꼴로')
    # 자소: ㄱ 오른쪽 아래 점 끌기
    pg.locator('[data-fm-tab="piece"]').click();pg.wait_for_timeout(600);cv=pg.locator('.fm-pcv');cv.scroll_into_view_if_needed();pg.wait_for_timeout(200);bb=cv.bounding_box();k=bb['width']/128
    pg.mouse.move(bb['x']+(84+14)*k,bb['y']+(92+14)*k);pg.mouse.down();pg.mouse.move(bb['x']+(50+14)*k,bb['y']+(96+14)*k,steps=6);pg.mouse.up();pg.wait_for_timeout(800)
    j=pg.evaluate(FONT+".jamo")
    ok(j and j['ㄱ'][0]['p'][2][0]<60,tag+' 자소 점 끌기 → 그 조각만 저장',j)
    ok('가' in pg.locator('[data-pc-sample]').inner_text() and pg.evaluate("getComputedStyle(document.querySelector('[data-pc-sample]')).fontFamily").startswith('mgdj_'),tag+' 조각 아래에 그 조각이 든 글자 보기')
    # 선 두 번 누르면 점 더하기, 점 빼기
    pg.mouse.dblclick(bb['x']+(40+14)*k,bb['y']+(14+14)*k);pg.wait_for_timeout(600)
    n=len(pg.evaluate(FONT+".jamo['ㄱ'][0].p"));ok(n==4,tag+' 선을 두 번 누르면 점 더하기',n)
    pg.locator('[data-pc-ptdel]').click();pg.wait_for_timeout(600);ok(len(pg.evaluate(FONT+".jamo['ㄱ'][0].p"))==3,tag+' 점 빼기')
    pg.locator('[data-pcj="ㅇ"]').click();pg.wait_for_timeout(300);pg.locator('[data-pc-add]').click();pg.wait_for_timeout(600)
    ok(len(pg.evaluate(FONT+".jamo['ㅇ']"))==2,tag+' 획 더하기')
    pg.locator('[data-pc-reset]').click();pg.wait_for_timeout(600);ok('ㅇ' not in pg.evaluate(FONT+".jamo"),tag+' 처음 모양으로')
    # 배치: 가(세로 모음) 초성 상자 옮기기
    pg.locator('[data-fm-tab="lay"]').click();pg.wait_for_timeout(800);cv=pg.locator('.fm-lcv');cv.scroll_into_view_if_needed();pg.wait_for_timeout(200);bb=cv.bounding_box();k=bb['width']/1180
    pg.mouse.move(bb['x']+(300+90)*k,bb['y']+(480+90)*k);pg.mouse.down();pg.mouse.move(bb['x']+(360+90)*k,bb['y']+(480+90)*k,steps=5);pg.mouse.up();pg.wait_for_timeout(800)
    L=pg.evaluate(FONT+".lay.v0.L");ok(L and L[0]>=120,tag+' 배치: 초성 상자 옮김',L)
    pg.locator('[data-lyf="h1"]').click();pg.wait_for_timeout(500);ok('곡' in pg.locator('[data-ly-sample]').inner_text(),tag+' 꼴 바꾸기(곡)')
    # 글자 고치기: 점 도구로 윤곽 점 끌기
    pg.locator('[data-fm-tab="glyph"]').click();pg.wait_for_timeout(500);pg.locator('.fm-add input').fill('가');pg.locator('.fm-add button').click();pg.wait_for_timeout(300);pg.locator('[data-fm-chips] [data-c="가"]').click();pg.locator('[data-fm-tool="point"]').click();pg.wait_for_timeout(1200)
    cv=pg.locator('.fm-cv');cv.scroll_into_view_if_needed();pg.wait_for_timeout(300);bb=cv.bounding_box()
    hit=pg.evaluate("""()=>{const c=document.querySelector('.fm-cv'),x=c.getContext('2d'),W=c.width,H=c.height,d=x.getImageData(0,0,W,H).data,r=c.getBoundingClientRect(),s=W/r.width;
      for(let y=0;y<H;y++)for(let X=Math.floor(W*0.55);X<W;X++){const i=(y*W+X)*4;if(d[i+3]>200&&d[i]<140)return [X/s,y/s]}return null}""")
    ok(hit,tag+' 점 도구: 윤곽 점이 보임',hit)
    if hit:
      pg.mouse.move(bb['x']+hit[0]+1,bb['y']+hit[1]+4);pg.mouse.down();pg.mouse.move(bb['x']+hit[0]+30,bb['y']+hit[1]-25,steps=5);pg.mouse.up();pg.wait_for_timeout(800)
    ed=pg.evaluate(FONT+".edit")or{};ok('가' in ed and len(ed['가']['c'])>8,tag+' 점 고치기 저장(그 글자만)',list(ed))
    pg.locator('[data-fm-done]').click();pg.wait_for_timeout(2000)
    f=pg.evaluate(FONT);ok(f['name'] in pg.locator('.mr-fonts').inner_text() and '자소로 설계' in pg.locator('.mr-fonts').inner_text(),tag+' 내 방 내 글꼴에 보임')
    pg.locator('#ed-park').click();pg.wait_for_timeout(500);pg.evaluate(SELECT,'가나다 고구마');pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(400);pg.locator(f'.fmt-fonts [data-uf="{f["id"]}"]').click();pg.wait_for_timeout(900)
    ok(f'<span class="uf-{f["id"]}">가나다 고구마</span>' in html(pg),tag+' 글쓰기로 돌아와 골라 입힘',html(pg))
    pg.locator('.hpub').last.click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(3000)
    post=pg.evaluate(REC+".posts.find(p=>p.title==='자소 글')");fs=(post.get('fonts') or {}).get(f['id'])
    ok(fs,tag+' 발행하면 쓴 글자만 잘라 저장')
    if fs:
      g=pg.evaluate(GLYPHS,[pg.evaluate(f"JSON.parse(localStorage.getItem('mgd2.v1.assets'))['{fs['a']}'].dataUrl"),'가나다고구마'])
      ok(all(v>50 for v in g.values()),tag+' 잘라 낸 글꼴: 여섯 글자 모양',g)
    ok(not errs,tag+' ERR',errs);pg.context.close()
print('fails',fails)
