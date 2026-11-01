import json
import sys
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).parents[1]))
from fontTools.ttLib import TTFont
from io import BytesIO

ROOT=Path(__file__).parents[1]
from font_engine import compile_font
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for viewport in ({'width':1100,'height':800},):
            page=browser.new_page(viewport=viewport,accept_downloads=True)
            failures=[]
            page.on('pageerror',lambda exc:failures.append(str(exc)))
            def font_api_call(value):
                doc=json.loads(value)
                raw,meta=compile_font(doc['project'],doc['name'],doc['format'])
                return base64.b64encode(raw).decode('ascii')
            page.expose_function('fontApiCall',font_api_call)
            page.set_content((ROOT/'index.html').read_text(encoding='utf-8'),wait_until='domcontentloaded')
            page.evaluate("""(()=>{window.fetch=async(url,opts)=>{
                const base64=await window.fontApiCall(opts.body);
                const byte=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
                return new Response(byte,{status:200,headers:{'Content-Type':'font/ttf'}});
            };})()""")
            page.wait_for_timeout(250)
            assert page.locator('#yf-preview .char').count()>10
            page.locator('#yf-weight').fill('11');assert page.locator('#yf-weight-val').inner_text()=='11'
            page.get_by_role('button',name='＋ 선').click()
            page.get_by_role('button',name='획 복제').click()
            page.get_by_role('button',name='좌우 반전').click()
            page.get_by_role('button',name='곡선 전환').click()
            page.get_by_role('button',name='선 닫기').click()
            assert page.locator('#yf-undo').is_enabled()
            page.locator('#yf-undo').click();page.locator('#yf-redo').click()
            page.get_by_role('button',name='개별 글자').click()
            page.locator('#yf-letters button').first.click()
            page.get_by_role('button',name='＋ 선').click()
            page.locator('#yf-fontname').fill('내폰트');print('START export',flush=True)
            with page.expect_download(timeout=60000) as d:
                page.locator('#yf-ttf').click()
            print("DOWNLOAD event",flush=True)
            download=d.value
            out=ROOT/f'tests/sample-{viewport["width"]}.ttf'
            download.save_as(out)
            font=TTFont(out)
            assert len([cp for cp in font.getBestCmap() if 0xAC00<=cp<=0xD7A3])==11172
            assert not font['glyf'][f'uni{ord("안"):04X}'].isComposite()
            print('STATUS',page.locator('#yf-status').inner_text(),flush=True);assert '완료:' in page.locator('#yf-status').inner_text()
            assert page.locator('#yf-real-box').is_visible()
            print('SAVE start',flush=True);page.locator('#yf-save').click();print('SAVE done',flush=True)
            print('WOFF start',flush=True)
            with page.expect_download(timeout=20000) as d:
                page.locator('#yf-woff').click()
            download=d.value
            out2=ROOT/f'tests/sample-{viewport["width"]}.woff2';download.save_as(out2)
            TTFont(out2)
            assert not failures,failures
            page.screenshot(path=str(ROOT/f'tests/preview-{viewport["width"]}.png'),full_page=True)
            print('UI + 실제 TTF/WOFF2 생성 통과',viewport)
            page.close()
        browser.close()
finally:
    pass
