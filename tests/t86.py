# 내 공간 편집 배율·글쓰기 사진/짤 보정 회귀 검증 (2026-11-03)
# 실행: cd tests && python3 t86.py
# 테스트 자동 실행 목록에는 실제 통합 검증 후 넣을 것.
from base import *
from pathlib import Path
import base64, tempfile, json
fails=[]
def ok(cond,message):
  print(('OK   ' if cond else 'FAIL ')+message)
  if not cond:fails.append(message)
GIF='R0lGODlhAgACAIAAAAAAAAAAACH/C05FVFNDQVBFMi4wAwEAAAAh+QQACQAAACwAAAAAAgACAAAIBgABCAQQEAAh+QQACQAAACwAAAAAAgACAAAIBgADCAwQEAA7'
with tempfile.TemporaryDirectory() as td:
  gif=Path(td)/'moving.gif';gif.write_bytes(base64.b64decode(GIF))
  with sync_playwright() as p:
    browser=p.chromium.launch()
    for mobile in (False,True):
      label='M' if mobile else 'PC'
      page=setup(browser,mobile);errs=page.errs
      if mobile:page.locator('[data-tab2="write"]').click()
      else:page.locator('[data-act="newPostFeed"]:visible').first.click()
      page.wait_for_timeout(400)
      page.locator('input[id^="f-title-"]').fill(label+' 짤 보정 확인')
      page.locator('input[id^="f-ins-"]').set_input_files(str(gif));page.wait_for_timeout(1100)
      image=page.locator('.win.editor .pblock .ph-item img').first
      ok(image.count()==1,label+' GIF inserted')
      if not image.count():continue
      ok(image.get_attribute('src').startswith('data:image/gif'),label+' animated GIF binary retained')
      page.locator('.win.editor .pblock [data-phm]').first.click();page.wait_for_timeout(150)
      ok(page.locator('.mgd-photo-tools:visible').count()==1,label+' contextual photo actions')
      page.locator('.mgd-photo-tools button').first.click()
      ok(page.locator('.mgd-fx-sheet').count()==1,label+' photo editor open')
      ok(page.locator('.mgd-fx-sheet [data-fx-basic] input').count()==3,label+' basic settings only')
      ok(page.locator('.mgd-fx-sheet [data-fx-extra]').is_hidden(),label+' advanced collapsed')
      ok(page.locator('.mgd-fx-sheet').evaluate('(e)=>getComputedStyle(e.parentElement).backgroundColor')=='rgba(0, 0, 0, 0)',label+' no dark backdrop')
      page.locator('.mgd-fx-presets button').filter(has_text='흑백').click()
      ok('grayscale(1)' in image.evaluate('(e)=>e.style.filter'),label+' live GIF filter preview')
      page.locator('[data-fx-cancel]').click()
      ok('grayscale(1)' not in image.evaluate('(e)=>e.style.filter'),label+' cancel restores previous appearance')
      page.locator('.mgd-photo-tools button').first.click()
      page.locator('.mgd-fx-presets button').filter(has_text='흑백').click()
      page.locator('[data-fx-save]').click()
      ok('grayscale(1)' in image.evaluate('(e)=>e.style.filter'),label+' save keeps adjustment')
      page.locator('.hpub').click();page.wait_for_timeout(250)
      page.locator('.dialog [data-o]').click();page.wait_for_timeout(950)
      post=page.evaluate("(name)=>JSON.parse(localStorage.getItem('mgd2.v1.records')).posts.find(x=>x.title===name)",label+' 짤 보정 확인')
      photos=[x for x in post['bodyJson']['blocks'] if x['type']=='photos'] if post else []
      ok(bool(photos and photos[0]['items'][0].get('fx',{}).get('gray')==100),label+' grayscale settings persisted')
      # Reader: display filter must be on the published image, not only preview
      ok(page.locator('article.post .pfig img[style*="grayscale"]').count()>0,label+' reader uses adjustment')
      ok(not errs,label+' no page errors '+str(errs))
      page.context.close()
    browser.close()
print('fails',fails)
