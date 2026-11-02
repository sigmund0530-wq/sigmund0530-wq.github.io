"""Mobile font workshop: viewport and multi-touch regression (Chromium emulation)."""
import base64
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from font_service import glyph_outline
html=re.sub(r'<link rel="stylesheet" href="/styles.css">','',(ROOT/'index.html').read_text())
html=re.sub(r'<script src="/app.js" defer></script>','',html)
css=(ROOT/'styles.css').read_text();js=(ROOT/'app.js').read_text()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def proxy(url,options):
  assert url.startswith('/api/glyph'),url
  qs=parse_qs(urlsplit(url).query)
  body=json.dumps(glyph_outline(qs['font'][0],qs['char'][0]),ensure_ascii=False).encode()
  return {'body':base64.b64encode(body).decode()}
 page.expose_function('pythonApi',proxy)
 page.set_content(html,wait_until='domcontentloaded')
 page.add_style_tag(content=css)
 page.evaluate("""() => {
  let m={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>m[k]||null,setItem:(k,v)=>m[k]=String(v)}});
  window.FontFace=class{constructor(f){this.family=f}async load(){return this}};
  Object.defineProperty(document,'fonts',{configurable:true,value:{add(){}}});
  window.fetch=async(u,o={})=>{const r=await window.pythonApi(u,o),b=Uint8Array.from(atob(r.body),c=>c.charCodeAt(0));return new Response(b,{status:200,headers:{'Content-Type':'application/json'}})};
 }""")
 page.add_script_tag(content=js)
 page.locator('#tab-glyph').click()
 page.wait_for_function("document.querySelector('#glyph-fill').getAttribute('d').length>100",timeout=30000)
 page.locator('#editor-focus').click()
 assert page.locator('body').evaluate("e=>e.classList.contains('focus-editor')")
 assert page.locator('.editor-canvas-wrap').bounding_box()['height']>340
 page.locator('#mobile-inspector').click()
 assert page.locator('#outline-list button').count()>1
 page.locator('#outline-list button').nth(1).click()
 assert page.locator('#outline-list button').nth(1).get_attribute('aria-selected')=='true'
 page.locator('#close-mobile-inspector').click()
 # Use original outlines to verify that pinch does not make an unwanted edit.
 before=page.locator('#glyph-fill').get_attribute('d')
 svg=page.locator('#glyph-canvas')
 box=svg.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
 session=page.context.new_cdp_session(page)
 def pt(i,x,y):return {'id':i,'x':x,'y':y}
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[pt(1,x-30,y)]})
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[pt(1,x-30,y),pt(2,x+30,y)]})
 session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[pt(1,x-90,y-10),pt(2,x+90,y+10)]})
 page.wait_for_timeout(160)
 assert int(page.locator('#zoom-value').inner_text().strip('%'))>100
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[pt(1,x-90,y-10)]})
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert page.locator('#glyph-fill').get_attribute('d')==before
 page.locator('#editor-focus').click()
 assert not page.locator('body').evaluate("e=>e.classList.contains('focus-editor')")
 assert not errors,errors
 print('MOBILE_TOUCH_PASS')
 browser.close()
