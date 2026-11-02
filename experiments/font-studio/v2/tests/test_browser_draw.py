"""End-to-end browser drawing tests with the real Python vector geometry API."""
import base64,io,json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from font_service import glyph_outline,build_font
from draw_service import apply_paint
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="/styles.css">','').replace('<script src="/app.js" defer></script>','')
css=(ROOT/'styles.css').read_text()
script=(ROOT/'app.js').read_text()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for width in (1280,390):
  page=browser.new_page(viewport={'width':width,'height':850},accept_downloads=True)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('dialog',lambda d:d.accept())
  def proxy(url,opts):
   from urllib.parse import parse_qs,urlsplit
   if url.startswith('/api/glyph'):
    qs=parse_qs(urlsplit(url).query);raw=json.dumps(glyph_outline(qs['font'][0],qs['char'][0]),ensure_ascii=False).encode();mime='application/json'
   elif url.startswith('/api/paint'):
    request=json.loads(opts.get('body','{}'));raw=json.dumps(apply_paint(request)).encode();mime='application/json'
   elif url.startswith('/api/build'):
    request=json.loads(opts.get('body','{}'));raw,meta=build_font(request['project'],request['format']);mime='application/octet-stream'
   else:raise RuntimeError('unhandled '+url)
   return {'data':base64.b64encode(raw).decode(),'mime':mime}
  page.expose_function('pythonApi',proxy)
  page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css)
  page.evaluate('''() => {
    const m={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>m[k]||null,setItem:(k,v)=>{m[k]=String(v)},removeItem:k=>delete m[k]}});
    window.FontFace=class {constructor(f,s){this.family=f}async load(){return this}};
    Object.defineProperty(document,'fonts',{configurable:true,value:{add(){}}});
    window.fetch=async (u,opts={}) => {const result=await window.pythonApi(u,opts);const bytes=Uint8Array.from(atob(result.data),c=>c.charCodeAt(0));return new Response(bytes,{status:200,headers:{'Content-Type':result.mime}})};
  }''')
  page.add_script_tag(content=script)
  page.locator('#tab-glyph').click();page.wait_for_timeout(500)
  page.locator('#blank-glyph').click();page.wait_for_timeout(100)
  assert page.locator('#glyph-fill').get_attribute('d')==''
  assert page.locator('[data-tool="brush"]').get_attribute('class').find('active')>=0
  def xy(x,y):
   return page.evaluate('''([x,y])=>{const svg=document.querySelector('#glyph-canvas');const p=svg.createSVGPoint();p.x=x;p.y=y;const z=p.matrixTransform(svg.getScreenCTM());return [z.x,z.y]}''',[x,y])
  async_error=[]
  def swipe(pts):
   page.locator('#glyph-canvas').scroll_into_view_if_needed()
   for i,(x,y) in enumerate(pts):
    cx,cy=xy(x,y)
    if i==0:page.mouse.move(cx,cy);page.mouse.down()
    else:page.mouse.move(cx,cy,steps=3)
   page.mouse.up()
   page.wait_for_timeout(800)
  swipe([(170,650),(330,260),(525,540),(730,215)])
  page.wait_for_function("document.querySelector('#glyph-fill').getAttribute('d').length>30",timeout=12000)
  added=page.locator('#glyph-fill').get_attribute('d');assert len(added)>50,errors
  assert page.locator('#glyph-status').inner_text()=='내가 수정한 글자'
  page.locator('[data-tool="eraser"]').click()
  swipe([(120,480),(770,490)])
  erased=page.locator('#glyph-fill').get_attribute('d')
  assert erased!=added,('erase did not modify contours',errors)
  page.locator('#editor-undo').click();page.wait_for_timeout(500)
  assert page.locator('#glyph-fill').get_attribute('d')==added,('undo erase',errors)
  page.locator('#editor-redo').click();page.wait_for_timeout(500)
  assert page.locator('#glyph-fill').get_attribute('d')==erased,('redo erase',errors)
  page.locator('[data-tool="rectangle"]').click()
  swipe([(120,115),(330,340)])
  squared=page.locator('#glyph-fill').get_attribute('d');assert squared!=erased,errors
  page.locator('[data-tool="ellipse"]').click()
  swipe([(650,130),(800,300)])
  circled=page.locator('#glyph-fill').get_attribute('d');assert circled!=squared,errors
  page.locator('#zoom-in').click();assert page.locator('#zoom-value').inner_text()=='125%'
  page.locator('#zoom-fit').click();assert page.locator('#zoom-value').inner_text()=='100%'
  # Polygon pen closing via Enter.
  page.locator('[data-tool="polygon"]').click()
  page.locator('#glyph-canvas').scroll_into_view_if_needed()
  for x,y in [(480,110),(680,115),(550,270)]:
   cx,cy=xy(x,y);page.mouse.click(cx,cy)
  page.locator('#glyph-canvas').press('Enter');page.wait_for_timeout(800)
  assert page.locator('#glyph-fill').get_attribute('d')!=circled,('pen no effect',errors)
  page.screenshot(path=str(ROOT/f'drawing-{width}.png'),full_page=True)
  page.locator('#tab-export').click()
  with page.expect_download(timeout=90000) as download:page.locator('#download-ttf').click()
  target=ROOT/f'runtime/drawing-{width}.ttf';download.value.save_as(target)
  with TTFont(target) as f:
   glyph=f['glyf'][f.getBestCmap()[ord('가')]]
   assert glyph.numberOfContours>0
   assert len([c for c in f.getBestCmap() if 0xAC00<=c<=0xD7A3])==11172
  assert not errors,errors
  print('DRAW_UI_PASS',width,'path chars:',len(circled),'font bytes:',target.stat().st_size)
  page.close()
 browser.close()