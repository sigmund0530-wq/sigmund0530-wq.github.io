"""Offline Playwright UI regression test; uses a local Python API bridge.
Chromium sandbox in this environment disallows visiting loopback directly.
"""
import sys,io,base64,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from font_service import glyph_outline,build_font,StudioError

html=(ROOT/'index.html').read_text()
html=re.sub(r'<link rel="stylesheet" href="/styles.css">','',html)
html=re.sub(r'<script src="/app.js" defer></script>','',html)
css=(ROOT/'styles.css').read_text()
script=(ROOT/'app.js').read_text()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for width in (1280,390):
  page=browser.new_page(viewport={'width':width,'height':900},accept_downloads=True)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def proxy(url,kwargs):
   if url.startswith('/api/glyph'):
    from urllib.parse import parse_qs,urlsplit
    qs=parse_qs(urlsplit(url).query);body=json.dumps(glyph_outline(qs['font'][0],qs['char'][0]),ensure_ascii=False).encode()
    return {'status':200,'data':base64.b64encode(body).decode(),'content_type':'application/json'}
   if url.startswith('/api/build'):
    req=json.loads(kwargs.get('body','{}'))
    raw,meta=build_font(req['project'],req['format'])
    return {'status':200,'data':base64.b64encode(raw).decode(),'content_type':'font/ttf'}
   raise Exception('Unsupported mock '+url)
  page.expose_function('pythonApi',proxy)
  page.set_content(html,wait_until='domcontentloaded')
  page.add_style_tag(content=css)
  page.evaluate('''() => {
    let __mem = {}; Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>__mem[k]??null,setItem:(k,v)=>{__mem[k]=String(v)},removeItem:k=>{delete __mem[k]}}});
    // FontFace loads are validated separately by the generated TTF tests.
    window.FontFace=class {constructor(family,source){this.family=family;this.source=source;}async load(){return this;}};
    Object.defineProperty(document,'fonts',{configurable:true,value:{add:()=>{}}});
    window.fetch=async(url,opts={})=>{let r=await window.pythonApi(url,opts);let bytes=Uint8Array.from(atob(r.data),c=>c.charCodeAt(0));return new Response(bytes,{status:r.status,headers:{'Content-Type':r.content_type}})};
  }''')
  page.add_script_tag(content=script)
  page.wait_for_timeout(500)
  assert page.locator('#compose-screen').is_visible(),errors
  assert '나의 글씨' in page.locator('#top-name').inner_text()
  page.locator('#width').fill('108')
  assert page.locator('#width-output').inner_text()=='108%'
  if width==390:
   page.locator('#open-menu').click()
   assert page.locator('#sidebar.open').is_visible()
   page.locator('#close-menu').click()
   page.wait_for_timeout(450)
  page.screenshot(path=str(ROOT/f'preview-{width}.png'),full_page=True)
  page.locator('#tab-glyph').click()
  page.wait_for_timeout(800)
  assert '개 점' in page.locator('#glyph-point-count').inner_text(),(errors,page.locator('#glyph-point-count').inner_text())
  before=page.locator('#glyph-fill').get_attribute('d')
  page.locator('#point-add').click()
  after=page.locator('#glyph-fill').get_attribute('d')
  assert after!=before
  assert '수정' in page.locator('#glyph-status').inner_text()
  page.locator('#editor-undo').click()
  page.wait_for_timeout(250)
  assert page.locator('#glyph-fill').get_attribute('d')==before
  page.locator('#editor-redo').click()
  page.wait_for_timeout(250)
  assert page.locator('#glyph-fill').get_attribute('d')==after
  handle=page.locator('#glyph-handles .handle-grab').first.bounding_box()
  page.mouse.move(handle['x']+handle['width']/2,handle['y']+handle['height']/2)
  page.mouse.down();page.mouse.move(handle['x']+handle['width']/2+10,handle['y']+handle['height']/2+8,steps=4);page.mouse.up()
  assert page.locator('#glyph-fill').get_attribute('d')!=after,'Drag did not update glyph contour'
  if width==1280:
   with page.expect_download(timeout=10000) as backup:page.locator('#save-backup').click()
   backup_path=ROOT/'runtime/test-project.json';backup.value.save_as(backup_path)
   saved=json.loads(backup_path.read_text())
   assert saved['project']['overrides'].get('가')
   page.locator('#load-backup').set_input_files(str(backup_path))
   page.wait_for_timeout(700)
   assert '2개' in page.locator('#project-count').inner_text()
  page.screenshot(path=str(ROOT/f'editor-{width}.png'),full_page=True)
  page.locator('#tab-export').click()
  page.locator('#font-name').fill('달빛 글씨')
  with page.expect_download(timeout=90000) as info:page.locator('#download-ttf').click()
  ttfpath=ROOT/f'runtime/test-output-{width}.ttf';info.value.save_as(ttfpath)
  font=TTFont(ttfpath)
  assert len([c for c in font.getBestCmap() if 0xAC00<=c<=0xD7A3])==11172
  assert font['name'].getDebugName(1)=='MGD 달빛 글씨'
  assert not errors,errors
  print('browser',width,'PASS',len(before),'->',len(after),'TTF',ttfpath.stat().st_size)
  page.close()
 browser.close()