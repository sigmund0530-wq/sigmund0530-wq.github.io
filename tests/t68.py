# 블록 양식: 검색 조건, 범위·빈 값·공개 범위, 사용자 구성 재사용
from base import *

with sync_playwright() as p:
  b=p.chromium.launch()
  for mob in [False,True]:
    pg=setup(b,mob)
    # Seed only synthetic records using the application's own saved post shape.
    write(pg,mob,'기준 글','자유롭게 쓴 이야기',vis='public')
    pg.evaluate('''()=>{const k='mgd2.v1.records',r=JSON.parse(localStorage.getItem(k)),base=r.posts[0];
      const block=(value)=>[{id:'instance-'+value,schemaId:'test-reading',name:'독서 기록',fields:[{id:'book',key:'book',name:'책 이름',type:'text',value:'가상 도서',options:[]},{id:'pages',key:'pages',name:'읽은 쪽',type:'number',value,options:[]},{id:'state',key:'state',name:'읽은 상태',type:'select',value:'다 읽음',options:['읽는 중','다 읽음']}]}];
      r.posts=['0','80','200',''].map((v,i)=>({...base,id:'test-'+i,title:'기록 '+i,functions:block(v),visibility:'public'}));
      r.posts.push({...base,id:'secret',title:'비밀 기록',visibility:'private',functions:[{id:'s',schemaId:'secret-schema',name:'비밀 블록',fields:[{id:'s',key:'s',name:'비밀 항목',type:'text',value:'비밀값'}]}]});localStorage.setItem(k,JSON.stringify(r))}''')
    pg.reload();pg.wait_for_timeout(450)
    if mob: pg.locator('[data-tab2="follow"]').click()
    pg.locator('[data-fsrch]:visible').first.click()
    pg.locator('[data-pf-filter]').select_option('test-reading')
    assert pg.locator('.srch-post').count()==4
    pg.locator('[data-pf-condition]').click()
    row=pg.locator('.pf-filter-row').first
    row.locator('[data-field]').select_option('pages|number');row.locator('[data-op]').select_option('lte');row.locator('[data-val]').fill('100')
    assert pg.locator('.srch-post').count()==2,'0 is included; blank is excluded'
    pg.locator('[data-pf-condition]').click();row=pg.locator('.pf-filter-row').last
    row.locator('[data-field]').select_option('state|select');row.locator('[data-val]').select_option('읽는 중')
    assert pg.locator('.srch-post').count()==0,'AND conditions'
    row.locator('[data-val]').select_option('다 읽음');assert pg.locator('.srch-post').count()==2
    pg.locator('#srch-q').fill('기록 1');assert pg.locator('.srch-post').count()==1
    pg.locator('[data-pf-reset]').click();pg.locator('#srch-q').fill('가상 도서');assert pg.locator('.srch-post').count()==4,'metadata shares keyword search'
    # Owner can find private metadata. Switch using supported preview control.
    if not mob:
      pg.locator('.pc-nav [data-pn="menu"]').click()
      pg.get_by_role('menuitem',name='내 공간 미리 보기').click()
      pg.locator('[data-fsrch]:visible').first.click()
      assert '비밀 블록' not in pg.locator('[data-pf-filter]').inner_text()
      pg.locator('#srch-q').fill('비밀값')
      assert pg.locator('.srch-post').count()==0
    else:
      assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'mobile overflow'
    pg.screenshot(path='/workspace/scratch/b2ad18ac0534/pf-test-runtime/blocks-'+('mobile' if mob else 'pc')+'.png',full_page=True)
    assert not pg.errs,pg.errs
    pg.context.close()
    print('OK', 'mobile' if mob else 'PC','block type filter, numeric zero/blank, select, AND, shared keyword search')
  b.close()
