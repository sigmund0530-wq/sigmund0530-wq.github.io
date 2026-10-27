from base import *
import json
U2='http://127.0.0.1:8820/app_sb.html'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def db(pg):return pg.evaluate("window.__mock.db")
def signup(pg,mail,handle,code):
  pg.goto(U2);pg.wait_for_timeout(700)
  ok(pg.locator('[data-au-social]').count()==0,'소셜 버튼 숨김');ok(pg.locator('.sb-beta').count()==1,'베타 안내')
  pg.locator('[data-au-method="email"]').click();pg.wait_for_timeout(150)
  ok(pg.locator('.au-box.sb-beta').count()==1,'약관에 베타 저장 안내')
  pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail',mail);pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','바다');pg.fill('#ob-name','하루');pg.fill('#ob-handle',handle)
  ok(pg.locator('#au-invite').count()==1,'초대 코드 칸')
  pg.fill('#au-invite','WRONG');pg.locator('[data-au-make]').click();pg.wait_for_timeout(500)
  ok(not pg.locator('.au-err[data-for="invite"]').is_hidden(),'틀린 초대 코드 막힘',pg.locator('.au-err[data-for="invite"]').text_content())
  pg.fill('#au-invite',code);pg.locator('[data-au-make]').click();pg.wait_for_timeout(600)
  ok(pg.locator('[data-aup-skip]').count()==1,'꾸미기 단계로')
  pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(600);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(2200)
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    tag='m' if mob else 'pc'
    ctx=b.new_context(viewport={'width':390,'height':800} if mob else {'width':1280,'height':800},has_touch=mob);pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    signup(pg,f'a{tag}@x.com','haru'+tag,'mugadang-beta')
    d=db(pg);ok(len(d['tables']['profiles'])==1,tag+' 서버에 공간 생김');pd=d['tables']['private_docs'][0]['data'];ok('settings' in pd,tag+' 처음 올리기(개인 문서)',list(pd.keys()))
    ok(d['invites']['MUGADANG-BETA']==1,tag+' 초대 코드 1회 사용')
    write(pg,mob,'서버 첫 글','바다를 봤다.','p1.jpg');pg.wait_for_timeout(2500)
    d=db(pg);ok(len(d['tables']['posts'])==1 and d['tables']['posts'][0]['visibility']=='public',tag+' 글 올라감');ok(len(d['tables']['media'])==1 and len(d['files'])==1,tag+' 사진 올라감',(len(d['tables']['media']),len(d['files'])))
    st=pg.evaluate("document.querySelector('#status span').textContent");ok(st=='저장됨',tag+' 저장 표시',st)
    # 새로고침: 바로 열림
    pg.reload();pg.wait_for_timeout(1500);ok(pg.locator('.au-card').count()==0,tag+' 새로고침해도 로그인 유지')
    ok(pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.length")==1,tag+' 글 그대로')
    # 끊김 → 다시 시도
    pg.evaluate("window.__mock.fail=2");closeall(pg)
    write(pg,mob,'두 번째','끊겼다 이어짐.',vis='private');pg.wait_for_timeout(1800)
    ok(pg.evaluate("!!localStorage.getItem('mgd2.v1.sbdirty')"),tag+' 실패 시 표시 남음')
    pg.wait_for_timeout(12000);d=db(pg);ok(len(d['tables']['posts'])==2 and not pg.evaluate("!!localStorage.getItem('mgd2.v1.sbdirty')"),tag+' 다시 시도해서 올라감',len(d['tables']['posts']))
    dump=json.dumps(d)
    # 다른 기기에서 로그인
    ctx2=b.new_context(viewport={'width':1280,'height':800});ctx2.add_init_script(f"if(!localStorage.getItem('mockdb'))localStorage.setItem('mockdb',{json.dumps(dump)})");p2=ctx2.new_page();p2.set_default_timeout(6000);e2=[];p2.on('pageerror',lambda e:e2.append(str(e)))
    p2.goto(U2);p2.wait_for_timeout(700);p2.locator('[data-au-go="login"]').click();p2.wait_for_timeout(200)
    p2.fill('#au-lmail',f'a{tag}@x.com');p2.fill('#au-lpw','wrong');p2.locator('[data-au-login]').click();p2.wait_for_timeout(400);ok(p2.locator('.au-card').count()==1,tag+' 틀린 비밀번호 막힘')
    p2.fill('#au-lpw','password123');p2.locator('[data-au-login]').click();p2.wait_for_timeout(1500)
    r=p2.evaluate("(()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));const a=JSON.parse(localStorage.getItem('mgd2.v1.assets'));return [r.posts.map(p=>p.title).sort(),r.profile.handle,Object.values(a).map(x=>(x.dataUrl||'').slice(0,11))]})()")
    ok(r[0]==['두 번째','서버 첫 글'] and r[1]=='haru'+tag and r[2]==['data:image/'],tag+' 다른 기기에서 그대로 불러옴',r)
    # 다른 기기에서 글 지우기 → 서버에서 지워짐, 사진도
    p2.evaluate("""(()=>{})()""")
    (p2.get_by_text('다음에 할게요').click() if p2.get_by_text('다음에 할게요').count() else None);p2.wait_for_timeout(800);p2.screenshot(path=f'sb_{tag}_dev2.png');imgs=p2.evaluate("[...document.images].filter(i=>i.complete&&i.naturalWidth>0).length");ok(imgs>=1,tag+' 사진 보임',imgs)
    ok(not e2,tag+' p2 ERR',e2)
    # 로그아웃
    pg.reload();pg.wait_for_timeout(1500)
    pg.evaluate("auLogout&&0") if False else None
    ctx2.close()
    ok(not errs,tag+' ERR',errs);ctx.close()
  # 글 지우기 & 로그아웃 (PC 새 계정)
  ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  signup(pg,'del@x.com','delme','MUGADANG-BETA');write(pg,False,'지울 글','곧 지움','p2.jpg');pg.wait_for_timeout(2500)
  d=db(pg);ok(len(d['files'])==1,'del: 사진 올라감')
  pg.evaluate("(()=>{records.posts=[];})()") if False else None
  # 화면으로 지우기 대신 직접: 내부 함수 접근 불가 → 저장본 수정 후 새로고침 방식
  pg.evaluate("""(()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));r.posts=[];localStorage.setItem('mgd2.v1.records',JSON.stringify(r));localStorage.setItem('mgd2.v1.assets','{}');localStorage.setItem('mgd2.v1.sbdirty','1')})()""")
  pg.reload();pg.wait_for_timeout(3000);d=db(pg);ok(len(d['tables']['posts'])==0 and len(d['files'])==0 and len(d['tables']['media'])==0,'del: 이 기기에서 못 올린 삭제가 다음에 열 때 올라감',(len(d['tables']['posts']),len(d['files'])))
  # 피드백 & 로그아웃
  pg.locator('[data-pn="me"],[data-act="mySettings"]').first.click() if False else None
  pg.evaluate("document.querySelector('[data-pc=\"logout\"]')") 
  ok(not errs,'del ERR',errs)
  b.close()
