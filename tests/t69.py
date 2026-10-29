# 붙인 정보로 다시 보기: 같은 글을 여러 모아보기에서, 같은 대상끼리 묶고 원문 한 줄, 글쓰기 중 '함께 보기'
from base import *

with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob)
    write(pg,mob,'기준 글','자유롭게 쓴 이야기',vis='public')
    pg.evaluate('''()=>{const k='mgd2.v1.records',r=JSON.parse(localStorage.getItem(k)),base=r.posts[0];
      const book=(id,v,st)=>({id,schemaId:'preset:독서 기록',name:'독서 기록',fields:[{id:id+'a',key:'b',name:'책 이름',type:'text',value:v,options:[]},{id:id+'b',key:'s',name:'읽은 상태',type:'select',value:st,options:['읽고 싶음','읽는 중','다 읽음']}]});
      const shop=(id,v)=>({id,schemaId:'preset:맛집·카페',name:'맛집·카페',fields:[{id:id+'a',key:'n',name:'가게 이름',type:'text',value:v,options:[]}]});
      const buy=(id,d,won)=>({id,schemaId:'preset:구매 정보',name:'구매 정보',fields:[{id:id+'a',key:'d',name:'구매한 날',type:'date',value:d,options:[]},{id:id+'b',key:'p',name:'가격',type:'number',value:won,options:[]}]});
      const mk=(id,title,txt,date,fs)=>({...base,id,title,recordedAt:date,createdAt:date+'T09:00:00Z',bodyJson:{blocks:[{id:id+'t',type:'text',html:txt}]},functions:fs});
      r.posts=[mk('p1','책방에 간 날','퇴근길에 동네 책방에 들렀다. 예전에 읽다 만 가상 소설이 보여서 다시 샀다. 친구랑 국수를 먹었다.','2026-10-20',[book('g1','가상 소설','읽는 중'),shop('g2','골목 국수'),buy('g3','2026-10-20','15000')]),
        mk('p2','삼 년 전','가상 소설은 왜 사람들이 좋아하는지 모르겠다.','2023-05-01',[book('g4','가상 소설','다 읽음')]),
        mk('p3','다른 책','짧은 시집을 읽었다.','2026-09-01',[book('g5','작은 시집','다 읽음')]),
        {...mk('p4','비밀 글','혼자만 아는 책','2026-10-01',[book('g6','비공개 책','읽는 중')]),status:'draft'}];
      localStorage.setItem(k,JSON.stringify(r))}''')
    pg.reload();pg.wait_for_timeout(450)
    # 전체 글 → 모아 보기
    if mob:
      pg.locator('[data-tab2="me"]').click();pg.wait_for_timeout(250);pg.locator('.pfc-m').click()
    else:
      pg.locator('.pc-space-nav [data-act="goPosts"]').click();pg.wait_for_timeout(250);pg.locator('.pfc-link').click()
    pg.wait_for_timeout(250)
    tabs=pg.locator('.pfc-tabs [role=tab]').all_inner_texts()
    assert tabs==['읽은 책','다녀온 곳','산 것'],tabs
    g=pg.locator('.pfc-g',has_text='가상 소설')
    assert g.locator('.pfc-row').count()==2,'same book from two posts'
    assert '이 이야기를 쓴 글 2편' in g.inner_text()
    assert '읽다 만 가상 소설' in g.inner_text() and '모르겠다' in g.inner_text(),'original sentences shown'
    assert '비공개 책' not in pg.locator('.pfc').inner_text(),'drafts excluded'
    pg.locator('[data-pfc-chip="읽은 상태=다 읽음"]').click();pg.wait_for_timeout(150)
    assert pg.locator('.pfc-row').count()==2 and '작은 시집' in pg.locator('.pfc').inner_text()
    # 같은 글이 다른 모아보기에서도
    pg.locator('[data-pfc-view="다녀온 곳"]').click();pg.wait_for_timeout(150)
    assert '골목 국수' in pg.locator('.pfc').inner_text() and '책방에 간 날' in pg.locator('.pfc').inner_text()
    pg.locator('[data-pfc-view="산 것"]').click();pg.wait_for_timeout(150)
    assert '2026년 10월' in pg.locator('.pfc').inner_text() and '15,000원' in pg.locator('.pfc-sum').inner_text()
    # 원래 글 열기 → 읽는 화면에서 다시 모아 보기로
    pg.locator('.pfc-row').first.click();pg.wait_for_timeout(400)
    assert pg.locator('.win:visible').count()>=1
    assert pg.locator('.pfc-from:visible').count()==3
    pg.locator('.pfc-from:visible',has_text='읽은 책').click();pg.wait_for_timeout(300)
    assert pg.locator('.pfc-g.hl h2').inner_text()=='가상 소설'
    closeall(pg)
    # 글쓰기 중: 같은 책을 붙이면 '내 글 2편 · 함께 보기'
    pg.locator('[data-tab2="write"]').click() if mob else pg.locator('[data-act="newPostFeed"]:visible').first.click();pg.wait_for_timeout(300)
    pg.locator('[data-pf-add]').click();pg.locator('[data-pf-q]').fill('책')
    assert '→ 읽은 책' in pg.locator('.pf-sugs').inner_text()
    pg.keyboard.press('Enter');pg.wait_for_timeout(150)
    assert '발행하면 ‘읽은 책’에서' in pg.locator('.pf-again').inner_text()
    pg.locator('.pf-card input[data-value="0"]').fill('가상 소설');pg.wait_for_timeout(500)
    assert '내 글 2편' in pg.locator('.pf-again').inner_text(),pg.locator('.pf-again').inner_text()
    pg.locator('[data-pf-same]').click();pg.wait_for_timeout(300)
    assert pg.locator('.pfc-win .pfc-row').count()==2
    assert not pg.errs,pg.errs
    print('OK','mobile' if mob else 'PC','collect views, same target, excerpt, chips, from post, editor hint')
    pg.context.close()
  b.close()
