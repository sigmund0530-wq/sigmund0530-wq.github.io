# 모양 넣기 · 기호 · 둥글기 고침 (2026-11-02): 하트·별 등 채운 모양, 내 그림(SVG) 가져오기, ♥ 같은 기호 글자, 둥글기가 가는 획을 지우지 않음
import json
from base import *
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
SELECT="""(w)=>{const a=[...document.querySelectorAll('.blocks .rte-area')].pop();const tw=document.createTreeWalker(a,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())){const i=n.data.indexOf(w);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+w.length);const s=getSelection();s.removeAllRanges();s.addRange(r);return true}}return false}"""
REC="JSON.parse(localStorage.getItem('mgd2.v1.records'))"
FONT=REC+".myFonts.find(f=>f.base==='gdodum')"
GL="""async(arg)=>{const [u,chars]=arg;await new Promise(r=>{if(window.opentype)return r();const s=document.createElement('script');s.src='vendor/opentype-1.3.4.min.js';s.onload=r;document.head.appendChild(s)});
  const f=opentype.parse(await (await fetch(u)).arrayBuffer());const o={};for(const ch of chars){const g=f.charToGlyph(ch);o[ch]=g&&g.index?g.path.commands.filter(c=>c.type==='M').length:0}return o}"""
def drag(pg,a,b):
  bb=pg.locator('.fm-cv').bounding_box();k=bb['width']/1180
  pg.mouse.move(bb['x']+(a[0]+90)*k,bb['y']+(a[1]+90)*k);pg.mouse.down();pg.mouse.move(bb['x']+(b[0]+90)*k,bb['y']+(b[1]+90)*k,steps=6);pg.mouse.up();pg.wait_for_timeout(700)
with sync_playwright() as p:
  b=p.chromium.launch()
  # 둥글기: 가는 획이 사라지지 않음(넓이 거의 그대로), 자소로 설계는 숨은 둥글기를 안 씀
  pg=b.new_page();pg.goto('http://127.0.0.1:8820/app.html?fontdev');pg.wait_for_timeout(800)
  r=pg.evaluate("""async()=>{await new Promise(r=>{const s=document.createElement('script');s.src='vendor/opentype-1.3.4.min.js';s.onload=r;document.head.appendChild(s)});
    const area=async(f,ch)=>{const F=opentype.parse(await window.__mgdFont.build(f,ch));const g=F.charToGlyph(ch);const c=document.createElement('canvas');c.width=c.height=200;const x=c.getContext('2d');const pth=g.getPath(0,170,200);pth.fill='#000';pth.draw(x);const d=x.getImageData(0,0,200,200).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>128)n++;return n};
    const b0=await area({base:'gbatang',p:{},glyphs:{},own:{}},'u'),b1=await area({base:'gbatang',p:{rd:40},glyphs:{},own:{}},'u');
    const j0=await area({mode:'jamo',base:'gdodum',p:{ct:45},glyphs:{},own:{}},'밥'),j1=await area({mode:'jamo',base:'gdodum',p:{ct:45,rd:40,wt:30},glyphs:{},own:{}},'밥');return {b0,b1,j0,j1}}""")
  ok(r['b1']>r['b0']*0.9,'둥글기 40: 가는 획이 사라지지 않음',r)
  ok(r['j0']==r['j1'],'자소로 설계: 바탕에서 남은 굵기·둥글기 안 씀',r)
  pg.close()
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    pg.locator('[data-tab2="room"]').click() if mob else pg.locator('.pc-nav [data-pn="room"]').click()
    pg.wait_for_timeout(600);pg.locator('.mr-fonts [data-uf-make]').click();pg.wait_for_timeout(800);pg.locator('[data-fm-base="gdodum"]').click();pg.wait_for_timeout(300)
    pg.locator('[data-fm-tab="glyph"]').click();pg.wait_for_timeout(500)
    ok(pg.locator('[data-fm-sym]').count()>=20,tag+' 기호 단추들')
    pg.locator('[data-fm-sym="♥"]').click();pg.wait_for_timeout(500)
    ok(pg.locator('.fm-chip.on').inner_text()=='♥',tag+' ♥를 누르면 고칠 글자로')
    pg.locator('[data-fm-tool="shape"]').click();pg.wait_for_timeout(200)
    ok(pg.locator('[data-fm-shapes]').is_visible() and pg.locator('[data-fm-shape]').count()==7,tag+' 모양 도구: 하트·별·반짝이·꽃·물방울·동그라미·달')
    pg.locator('.fm-cv').scroll_into_view_if_needed();pg.wait_for_timeout(200)
    drag(pg,(150,150),(850,800))
    g=pg.evaluate(FONT+".glyphs['♥']");ok(g and len(g)==1 and g[0].get('k')=='heart' and len(g[0]['f'][0])>100,tag+' 하트를 끌어 놓음',g and g[0].get('k'))
    drag(pg,(400,400),(405,404));ok(len(pg.evaluate(FONT+".glyphs['♥']"))==1,tag+' 너무 작게 끌면 안 넣음')
    pg.locator('[data-fm-sym="★"]').click();pg.locator('[data-fm-shape="star"]').click();drag(pg,(100,100),(900,900))
    with pg.expect_file_chooser() as fc:pg.locator('.fm-svg').click()
    fc.value.set_files('testshape.svg');pg.wait_for_timeout(800)
    ok(pg.locator('.fm-svg.on').count()==1 and not pg.evaluate("window.__svgxss||0"),tag+' 그림(SVG) 가져오기, 그림 속 코드는 안 돌아감')
    pg.locator('[data-fm-sym="○"]').click();drag(pg,(100,100),(900,900))
    o=pg.evaluate(FONT+".glyphs['○']");ok(o and o[0].get('eo')==1 and len(o[0]['f'])==2,tag+' 가져온 그림: 바깥·안쪽 두 줄, 구멍 규칙',o and (o[0].get('eo'),len(o[0]['f'])))
    pg.locator('[data-fm-done]').click();pg.wait_for_timeout(1500)
    f=pg.evaluate(FONT)
    # 글에서 쓰기 → 발행 → 잘라 낸 글꼴에 ♥ ★ ○
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
    pg.wait_for_timeout(500);pg.locator('input[id^="f-title-"]').last.fill('하트 글');pg.locator('.blocks .rte-area').last.click();pg.keyboard.type('좋아 ♥★○')
    if mob:pg.locator('.t-btn').tap();pg.wait_for_timeout(200)
    pg.evaluate(SELECT,'♥★○');pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(400);pg.locator(f'.fmt-fonts [data-uf="{f["id"]}"]').click();pg.wait_for_timeout(900)
    pg.locator('.hpub').last.click();pg.wait_for_timeout(200);pg.locator('input[name="pv"][value="public"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(2500)
    fs=(pg.evaluate(REC+".posts.find(p=>p.title==='하트 글')").get('fonts') or {}).get(f['id'])
    ok(fs,tag+' 발행하면 잘라 저장')
    if fs:
      g=pg.evaluate(GL,[pg.evaluate(f"JSON.parse(localStorage.getItem('mgd2.v1.assets'))['{fs['a']}'].dataUrl"),'♥★○'])
      ok(g['♥']>=1 and g['★']>=1 and g['○']==2,tag+' 잘라 낸 글꼴에 하트·별·구멍 난 동그라미',g)
    ok(not errs,tag+' ERR',errs);pg.context.close()
print('fails',fails)
