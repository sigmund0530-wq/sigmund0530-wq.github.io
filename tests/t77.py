# 프로필 편집 화면: 설정 → 프로필 편집(따로 화면) · 사진 고르면 맞추기(끌기·확대·미리보기 3개) · 적용·완료 저장 · 위치 다시 맞추기 · 취소하면 안 바뀜
from base import *
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
def rec(pg):return pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.records')||'null')")
def opensettings(pg,mob):
  if mob:pg.locator('[data-m-settings]').first.click();pg.wait_for_timeout(200);pg.get_by_text('설정',exact=True).first.click()
  else:pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click()
  pg.wait_for_timeout(300)
with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in (False,True):
    tag='M' if mob else 'PC';pg=setup(b,mob);errs=pg.errs
    opensettings(pg,mob);pg.locator('[data-set="profile"]').click();pg.wait_for_timeout(300)
    ok(pg.locator('.pe-page').count()==1,tag+' 설정 → 프로필 편집 화면')
    full=pg.evaluate("(()=>{const r=document.querySelector('.pe-sheet').getBoundingClientRect();return Math.round(r.width)===innerWidth})()");ok(full==mob,tag+(' 휴대폰은 화면 가득' if mob else ' PC는 가운데 판'))
    pg.locator('[data-pe-x]').click();pg.wait_for_timeout(200);ok(pg.locator('.pe-page').count()==0,tag+' 취소')
    pg.locator('[data-set="profile"]').click();pg.wait_for_timeout(300)
    pg.fill('[data-pe-name]','새이름');pg.fill('[data-pe-status]','한 줄 소개');ok('6/60' in pg.locator('[data-pe-cnt]').inner_text(),tag+' 소개 글자 수')
    pg.locator('[data-pe-file]').set_input_files('p1.jpg');pg.wait_for_timeout(800)
    ok(pg.locator('.pc-wrap').count()==1 and pg.locator('.pc-ring').count()==1,tag+' 사진 고르면 맞추기 화면(동그란 칸)')
    ok(pg.locator('.pc-prevs canvas').count()==3,tag+' 실제 크기 미리보기 3개')
    t0=pg.evaluate("document.querySelector('.pc-stage img').style.transform")
    st=pg.locator('.pc-stage').bounding_box();cx,cy=st['x']+st['width']/2,st['y']+st['height']/2
    pg.locator('.pc-zoom input').fill('2.5');pg.wait_for_timeout(200)
    w1=pg.evaluate("parseFloat(document.querySelector('.pc-stage img').style.width)");ok(w1>st['width']*2,tag+' 막대로 확대',w1)
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+60,cy+30,steps=5);pg.mouse.up();pg.wait_for_timeout(200)
    t1=pg.evaluate("document.querySelector('.pc-stage img').style.transform");ok(t1!=t0,tag+' 끌어서 옮김')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+2000,cy+2000,steps=5);pg.mouse.up();pg.wait_for_timeout(200)
    gap=pg.evaluate("(()=>{const s=document.querySelector('.pc-stage').getBoundingClientRect(),i=document.querySelector('.pc-stage img').getBoundingClientRect();return i.left<=s.left+1&&i.top<=s.top+1&&i.right>=s.right-1&&i.bottom>=s.bottom-1})()")
    ok(gap,tag+' 칸 밖으로 빈 곳 안 생김')
    pg.locator('[data-pc-ok]').click();pg.wait_for_timeout(300);ok(pg.locator('.pc-wrap').count()==0 and pg.locator('.pe-av img').count()==1,tag+' 적용 → 편집 화면에 새 사진')
    pg.locator('[data-pe-ok]').click();pg.wait_for_timeout(400)
    pr=rec(pg)['profile'];a=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.assets'))")
    ok(pr['displayName']=='새이름' and pr['status']=='한 줄 소개',tag+' 이름·소개 저장')
    ok(pr.get('photoAssetId') in a and a[pr['photoAssetId']]['width']==480,tag+' 480 정사각 프사 저장')
    ok(pr.get('photoSrcId') in a and pr.get('photoCrop',{}).get('z',0)>2,tag+' 원본·맞춘 위치도 저장',pr.get('photoCrop'))
    # 위치 다시 맞추기: 원본에서 이어서
    opensettings(pg,mob) if pg.locator('[data-set="profile"]').count()==0 else None
    pg.locator('[data-set="profile"]').click();pg.wait_for_timeout(300);pg.locator('[data-pe-adj]').click();pg.wait_for_timeout(700)
    ok(abs(float(pg.locator('.pc-zoom input').input_value())-pr['photoCrop']['z'])<0.05,tag+' 다시 맞추기는 지난 위치에서 시작')
    pg.locator('[data-pc-x]').click();pg.wait_for_timeout(200);pg.locator('[data-pe-x]').click();pg.wait_for_timeout(200)
    ok(rec(pg)['profile']['photoAssetId']==pr['photoAssetId'],tag+' 취소하면 그대로')
    # 내 공간 편집에서 '프로필'을 누르면 겹치던 칸 대신 같은 편집 화면
    pg.go_back();pg.wait_for_timeout(300)
    if pg.locator('[data-se-begin]:visible').count()==0:
      pg.locator('[data-tab2="home"],[data-pn="home"],[data-nav="blog"]').first.click() if pg.locator('[data-tab2="home"],[data-pn="home"],[data-nav="blog"]').count() else None;pg.wait_for_timeout(300)
    if pg.locator('[data-se-begin]:visible').count():
      pg.locator('[data-se-begin]:visible').first.click();pg.wait_for_timeout(400)
      pg.locator('[data-se="profile"]').first.click();pg.wait_for_timeout(400)
      ok(pg.locator('.pe-page').count()==1 and pg.locator('.se-panel').count()==0,tag+' 내 공간 편집의 프로필 → 같은 편집 화면(겹치는 칸 없음)')
      ok(pg.locator('[data-pe-show]').count()==1 and pg.locator('[data-pe-keep]').count()==1 and pg.locator('[data-pe-sq]').count()==1,tag+' 보이기·소개 보관·나만 아는 질문도 여기에')
      pg.locator('[data-pe-show]').uncheck();pg.locator('[data-pe-keep]').check();pg.fill('[data-pe-status]','두 번째 소개');pg.locator('[data-pe-ok]').click();pg.wait_for_timeout(400)
      lay=pg.evaluate("JSON.parse(localStorage.getItem('mgd2.v1.layout.desktop')||'{}')");r=rec(pg)['profile']
      ok((lay.get('hide') or {}).get('profile') is True,tag+' 방문자에게 숨기기 저장')
      ok(r.get('keepBio') and r.get('bioHistory') and r['bioHistory'][0]['text']=='한 줄 소개',tag+' 이전 소개 보관',r.get('bioHistory'))
      pg.locator('[data-se-cancel],.se-bar button:has-text("취소")').first.click();pg.wait_for_timeout(400)
      if pg.locator('.dialog [data-o]').count():pg.locator('.dialog [data-o]').click();pg.wait_for_timeout(300)
      ok(rec(pg)['profile']['status']=='두 번째 소개',tag+' 편집 취소해도 프로필 저장은 그대로')
    else:ok(False,tag+' 내 공간 편집 버튼을 못 찾음')
    ok(not errs,tag+' ERR',errs);pg.context.close()
