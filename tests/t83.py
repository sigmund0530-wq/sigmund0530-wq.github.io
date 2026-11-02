# 내 글꼴(2026-11-02): 글꼴 올리기 · 손글씨 글꼴 만들기 · 발행하면 쓴 글자만 잘라 저장 · 다른 사람에게도 그 글꼴로 보임
import json
from base import *
U2='http://127.0.0.1:8820/app_sb.html'
FONT='testfont.otf'
fails=[]
def ok(c,m,*a):
  print(('OK   ' if c else 'FAIL ')+m,*a)
  if not c:fails.append(m)
SELECT="""(w)=>{const a=[...document.querySelectorAll('.blocks .rte-area')].pop();const tw=document.createTreeWalker(a,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())){const i=n.data.indexOf(w);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+w.length);const s=getSelection();s.removeAllRanges();s.addRange(r);return true}}return false}"""
REC="JSON.parse(localStorage.getItem('mgd2.v1.records'))"
def html(pg):return pg.evaluate("[...document.querySelectorAll('.blocks .rte-area')].pop().innerHTML")
def write(pg,title,txt,mob=False):
  pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click()
  pg.wait_for_timeout(500);pg.locator('input[id^="f-title-"]').last.fill(title);pg.locator('.blocks .rte-area').last.click();pg.keyboard.type(txt)
  if mob:pg.locator('.t-btn').tap();pg.wait_for_timeout(200)
def publish(pg,vis='public'):
  pg.locator('.hpub').last.click();pg.wait_for_timeout(200);pg.locator(f'input[name="pv"][value="{vis}"]').check();pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(500)
def upload(pg,share=True):
  with pg.expect_file_chooser() as fc:pg.locator('[data-uf-up]').first.click()
  fc.value.set_files(FONT);pg.locator('#uf-ok').wait_for()
  if share:pg.locator('#uf-ok').check()
  pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(1200)
def draw(pg,n=2):
  bb=pg.locator('.fm-cv').bounding_box()
  for k in range(n):
    pg.mouse.move(bb['x']+bb['width']*.2,bb['y']+bb['height']*(.25+k*.3));pg.mouse.down();pg.mouse.move(bb['x']+bb['width']*.7,bb['y']+bb['height']*(.3+k*.3),steps=8);pg.mouse.move(bb['x']+bb['width']*.5,bb['y']+bb['height']*.8,steps=6);pg.mouse.up()
  pg.wait_for_timeout(300)
def signup(pg,mail,handle,name):
  pg.goto(U2);pg.wait_for_timeout(700);pg.locator('[data-au-method="email"]').click();pg.wait_for_timeout(150)
  pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',mail);pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','바다');pg.fill('#ob-name',name);pg.fill('#ob-handle',handle)
  pg.fill('#au-invite','MUGADANG-BETA');pg.locator('[data-au-make]').click();pg.wait_for_timeout(600)
  pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(600);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(2000)
def logout(pg):
  pg.evaluate("localStorage.removeItem('mocksess');Object.keys(localStorage).filter(k=>k.startsWith('mgd2.')).forEach(k=>localStorage.removeItem(k))")
with sync_playwright() as p:
  b=p.chromium.launch()
  # ── 1) 서버 없이(미리보기): 올리기 · 입히기 · 발행 · 다시 열기 · 만들기 ──
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    write(pg,'글꼴 글','오늘은 하늘이 정말 좋았다',mob)
    pg.evaluate(SELECT,'하늘이');pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(200)
    ok(pg.locator('.fmt-fonts [data-uf-up]').count()==1 and pg.locator('.fmt-fonts [data-uf-make]').count()==1,tag+' 글꼴 목록에 올리기·만들기')
    upload(pg)
    f=pg.evaluate(REC+".myFonts[0]");ok(f and f['name']=='Mugadang Test Hand Regular' and f['share'] and f['how']=='upload',tag+' 올린 글꼴: 이름은 파일에서 읽음',f)
    ok(pg.evaluate("localStorage.getItem('mgd2.v1.records').length<20000 && !localStorage.getItem('mgd2.v1.assets').includes('font/')"),tag+' 원본은 localStorage에 안 넣음(이 기기 보관함)')
    ok(f'<span class="uf-{f["id"]}">하늘이</span>' in html(pg),tag+' 고른 글자에 바로 입혀짐',html(pg))
    fam=pg.evaluate("getComputedStyle(document.querySelector('.blocks .rte-area [class*=uf-]')).fontFamily")
    ok(fam.startswith('mgdu_'+f['id']),tag+' 글쓰기에서 그 글꼴로 보임',fam)
    publish(pg);pg.wait_for_timeout(1500)
    post=pg.evaluate(REC+".posts.find(p=>p.title==='글꼴 글')");fs=post.get('fonts') or {}
    ok(f['id'] in fs and fs[f['id']]['a'],tag+' 발행하면 쓴 글자만 잘라 저장',fs)
    a=pg.evaluate(f"JSON.parse(localStorage.getItem('mgd2.v1.assets'))['{fs.get(f['id'],{}).get('a','x')}']")
    ok(a and a['mime']=='font/otf' and len(a['dataUrl'])<6000,tag+' 잘라 낸 글꼴은 작음',a and len(a['dataUrl']))
    # 잘라 낸 글꼴에 든 글자 = 하늘이
    chars=pg.evaluate("""async(u)=>{await new Promise(r=>{const s=document.createElement('script');s.src='vendor/opentype-1.3.4.min.js';s.onload=r;document.head.appendChild(s)});const b=await (await fetch(u)).arrayBuffer();const f=opentype.parse(b);const o=[];for(let i=0;i<f.glyphs.length;i++){const g=f.glyphs.get(i);if(g.unicode&&g.unicode!==32)o.push(String.fromCodePoint(g.unicode))}return o.sort().join('')}""",a['dataUrl'])
    ok(chars==''.join(sorted('하늘이')),tag+' 잘라 낸 글꼴 속 글자',chars)
    # 다시 열어도(이 기기 보관함) 그 글꼴
    pg.reload();pg.wait_for_timeout(1200)
    pg.evaluate(f"document.querySelector('[data-act=\"editPost\"]')||0")
    write(pg,'둘째 글','하늘 아래',mob);pg.evaluate(SELECT,'하늘');pg.locator('[data-fmt="ff"]').click();pg.wait_for_timeout(300)
    pg.locator(f'.fmt-fonts [data-uf="{f["id"]}"]').click();pg.wait_for_timeout(800)
    fam=pg.evaluate("getComputedStyle(document.querySelector('.blocks .rte-area [class*=uf-]')).fontFamily")
    ok(fam.startswith('mgdu_') and pg.evaluate("[...document.fonts].some(f=>f.family.startsWith('mgdu_')&&f.status==='loaded')"),tag+' 새로 열어도 이 기기 보관함에서 불러옴',fam)
    # 손글씨 만들기
    pg.evaluate(SELECT,'아래');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-make]').click();pg.wait_for_timeout(500)
    ok(pg.locator('[data-fm-base]').count()==6 and '빈 종이' in pg.locator('.fm-start').inner_text(),tag+' 만들기: 바탕 넷 + 자소로 설계 + 빈 종이에서 고르기')
    pg.locator('[data-fm-base=""]').click();pg.wait_for_timeout(400)
    ok(pg.locator('.fm-chip').count()>=10 and pg.locator('[data-fm-prog]').inner_text()=='오늘 0/10',tag+' 오늘의 글자 열 자')
    first=pg.locator('.fm-chip.on').inner_text();draw(pg)
    ok(pg.locator('.fm-chip.on.done').count()==1 and pg.locator('[data-fm-prog]').inner_text()=='오늘 1/10',tag+' 그리면 바로 모임',first)
    pg.locator('.fm-add input').fill('아래');pg.locator('.fm-add button').click();pg.wait_for_timeout(200)
    ok(pg.locator('.fm-chip.on').inner_text()=='아',tag+' 그리고 싶은 글자 넣기');draw(pg,1)
    pg.locator('[data-fm-next]').click();pg.wait_for_timeout(100)
    ok(pg.locator('.fm-chip.on').inner_text()!='아',tag+' 다음 글자')
    pg.locator('.fm-chip',has_text='아').first.click();pg.locator('[data-fm-clear]').click();pg.wait_for_timeout(600)
    mf=pg.evaluate(REC+".myFonts.find(f=>f.how==='made')");ok(mf and '아' not in mf['glyphs'] and first in mf['glyphs'],tag+' 다시 그리기로 비우면 그 글자 빠짐',mf and list(mf['glyphs']))
    draw(pg,1);pg.locator('[data-fm-undo]').click();pg.wait_for_timeout(500);ok('아' not in pg.evaluate(REC+".myFonts.find(f=>f.how==='made').glyphs"),tag+' 되돌리기')
    draw(pg,1);pg.locator('.fm-name').fill('내 손글씨');pg.locator('[data-fm-done]').click();pg.wait_for_timeout(800)
    mf=pg.evaluate(REC+".myFonts.find(f=>f.how==='made')")
    ok(mf['name']=='내 손글씨' and '아' in mf['glyphs'] and pg.locator('.fm').count()==0,tag+' 완료: 이름·글자 저장')
    ok(f'<span class="uf-{mf["id"]}">아래</span>' in html(pg),tag+' 만든 뒤 골라 둔 글자에 바로 입혀짐',html(pg))
    publish(pg);pg.wait_for_timeout(1500)
    post=pg.evaluate(REC+".posts.find(p=>p.title==='둘째 글')");fs=post.get('fonts') or {}
    ok(mf['id'] in fs and f['id'] in fs,tag+' 손글씨 글꼴도 잘라 저장',list(fs))
    # 내 글꼴 서랍: 나에게만으로 바꾸면 남에게는 안 감
    closeall(pg)
    write(pg,'셋째','하늘',mob);pg.evaluate(SELECT,'하늘');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-sheet]').click();pg.wait_for_timeout(300)
    ok(pg.locator('.uf-list li').count()==2 and '직접 그림' in pg.locator('.uf-list').inner_text(),tag+' 내 글꼴 서랍에 둘')
    pg.locator(f'.uf-list li[data-id="{f["id"]}"] [data-uf-share]').click();pg.wait_for_timeout(200)
    ok(not pg.evaluate(REC+f".myFonts.find(x=>x.id==='{f['id']}').share"),tag+' 나에게만 보이기')
    pg.locator('.dialog [data-c]').click();pg.wait_for_timeout(1500)
    post=pg.evaluate(REC+".posts.find(p=>p.title==='글꼴 글')")
    ok(f['id'] not in (post.get('fonts') or {}),tag+' 나에게만으로 바꾸면 발행한 글의 잘라 둔 글꼴도 뺌')
    # 바탕 글꼴에서: 막대로 모양 → 글자 고치기 → 발행
    pg.locator('.dialog [data-c]').click() if pg.locator('.dialog [data-c]').count() else None
    pg.reload();pg.wait_for_timeout(1200);write(pg,'바탕 글','바람이 분다',mob);pg.evaluate(SELECT,'바람이');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-make]').click();pg.wait_for_timeout(1500)
    pg.locator('[data-fm-close]').click();pg.wait_for_timeout(200);n0=len(pg.evaluate(REC+".myFonts"))
    pg.evaluate(SELECT,'바람이');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-make]').click();pg.wait_for_timeout(800)
    pg.locator('[data-fm-base="gdodum"]').click();pg.wait_for_timeout(300)
    ok(pg.locator('[data-fm-tab="shape"].on').count()==1 and pg.locator('[data-fm-p]').count()==5,tag+' 바탕 고르면 전체 모양 막대 다섯')
    pg.locator('[data-fm-close]').click();pg.wait_for_timeout(400)
    ok(len(pg.evaluate(REC+".myFonts"))==n0,tag+' 아무것도 안 바꾸고 닫으면 남기지 않음')
    pg.evaluate(SELECT,'바람이');pg.locator('[data-fmt="ff"]').click();pg.locator('[data-uf-make]').click();pg.wait_for_timeout(800);pg.locator('[data-fm-base="gdodum"]').click();pg.wait_for_timeout(300)
    pg.locator('[data-fm-p="wt"]').fill('20');pg.locator('[data-fm-p="rd"]').fill('15');pg.wait_for_timeout(2500)
    ok(pg.evaluate("getComputedStyle(document.querySelector('[data-fm-out]')).fontFamily").startswith('mgdt_') and pg.evaluate("[...document.fonts].some(f=>f.family.startsWith('mgdt_')&&f.status==='loaded')"),tag+' 막대를 움직이면 써 보기가 그 모양으로')
    pg.locator('[data-fm-tab="glyph"]').click();pg.wait_for_timeout(1200)
    chip=pg.locator('.fm-chip.on').inner_text();pg.locator('[data-fm-tool="circle"]').click();bb=pg.locator('.fm-cv').bounding_box()
    pg.mouse.move(bb['x']+bb['width']*.8,bb['y']+bb['height']*.2);pg.mouse.down();pg.mouse.move(bb['x']+bb['width']*.86,bb['y']+bb['height']*.2,steps=5);pg.mouse.up();pg.wait_for_timeout(600)
    pg.locator('[data-fm-tool="erase"]').click();pg.mouse.move(bb['x']+bb['width']*.3,bb['y']+bb['height']*.5);pg.mouse.down();pg.mouse.move(bb['x']+bb['width']*.5,bb['y']+bb['height']*.5,steps=6);pg.mouse.up();pg.wait_for_timeout(600)
    pg.locator('[data-fm-done]').click();pg.wait_for_timeout(2000)
    bf=pg.evaluate(REC+".myFonts.find(f=>f.base==='gdodum')")
    ok(bf and bf['p']['wt']==20 and len(bf['glyphs'].get(chip,[]))==2 and bf['glyphs'][chip][1][0]<0,tag+' 저장: 바탕·모양·더한 획·지운 획',bf and (bf.get('p'),{k:len(v) for k,v in bf['glyphs'].items()}))
    ok(f'<span class="uf-{bf["id"]}">바람이</span>' in html(pg) and pg.evaluate(f"getComputedStyle(document.querySelector('.uf-{bf['id']}')).fontFamily").startswith('mgdu_'),tag+' 고른 글자에 바로, 글쓰기에서 그 모양으로')
    publish(pg);pg.wait_for_timeout(2500)
    post=pg.evaluate(REC+".posts.find(p=>p.title==='바탕 글')");fs=(post.get('fonts') or {}).get(bf['id'])
    ok(fs,tag+' 바탕에서 만든 글꼴도 잘라 저장')
    info=pg.evaluate("""async(u)=>{const b=await (await fetch(u)).arrayBuffer();const f=opentype.parse(b);const o=[];for(let i=0;i<f.glyphs.length;i++){const g=f.glyphs.get(i);if(g.unicode&&g.unicode!==32)o.push([String.fromCodePoint(g.unicode),g.path.commands.length])}return o}""",pg.evaluate(f"JSON.parse(localStorage.getItem('mgd2.v1.assets'))['{fs['a'] if fs else 'x'}'].dataUrl") if fs else 'data:,')
    ok(sorted(c for c,n in info)==sorted('바람이') and all(n>10 for c,n in info),tag+' 잘라 낸 글꼴: 바람이 세 글자, 모양 있음',info)
    ok(not errs,tag+' ERR',errs);pg.context.close()
  # ── 2) 서버: 하루가 올린 글꼴로 쓴 글을 민지가 그 글꼴로 봄 ──
  ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(8000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U2);pg.wait_for_timeout(300);pg.evaluate("localStorage.clear()")
  signup(pg,'haru@x.com','haru','하루')
  write(pg,'하루의 글꼴','오늘은 하늘이 정말 좋았다');pg.evaluate(SELECT,'하늘이');pg.locator('[data-fmt="ff"]').click();upload(pg)
  publish(pg);pg.wait_for_timeout(4500)
  d=pg.evaluate("window.__mock.db");md=d['tables']['media']
  src=[m for m in md if m['id'].startswith('font-')];sub=[m for m in md if m['kind']=='font' and not m['id'].startswith('font-')]
  ok(len(src)==1 and len(sub)==1,'서버: 원본 하나 + 잘라 낸 것 하나 (kind font)',[(m['id'],m['kind']) for m in md])
  prow=[x for x in d['tables']['posts'] if x['data']['title']=='하루의 글꼴'][0]
  ok(sub and sub[0]['id'] in prow['media_ids'] and src[0]['id'] not in prow['media_ids'],'잘라 낸 것만 글에 걸림(원본은 주인만)')
  logout(pg);signup(pg,'minji@x.com','minji','민지')
  pg.locator('.pc-nav [data-pn="feed"]').click();pg.wait_for_timeout(1200);pg.get_by_role('tab',name='무작위').first.click();pg.wait_for_timeout(1500)
  pg.get_by_text('하루의 글꼴').first.click();pg.wait_for_timeout(2000)
  info=pg.evaluate("(()=>{const e=document.querySelector('.win [class*=ufp-]');return e?[e.className,getComputedStyle(e).fontFamily]:null})()")
  ok(info and 'mgdp_' in info[1],'민지에게도 하루의 글꼴로 보임',info)
  ok(pg.evaluate("[...document.fonts].some(f=>f.family.startsWith('mgdp_')&&f.status==='loaded')"),'잘라 낸 글꼴을 받아 그림')
  ok(pg.evaluate("!Object.keys(JSON.parse(localStorage.getItem('mgd2.v1.records')).myFonts||{}).length"),'민지의 내 글꼴엔 섞이지 않음')
  ok(not errs,'ERR2',errs)
print('fails',fails)
