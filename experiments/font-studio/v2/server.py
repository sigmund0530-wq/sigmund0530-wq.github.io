"""MGD Font Studio v2 - localhost-only development service (not public hosting)."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from threading import BoundedSemaphore
import json
from font_service import (FONTS,StudioError,MAX_PROJECT_BYTES,ensure_font,
                          glyph_outline,build_font,read_font_info)
ROOT=Path(__file__).resolve().parent
SLOTS=BoundedSemaphore(2)
class Handler(BaseHTTPRequestHandler):
 def respond(self,body,mime,status=200,headers=None):
  self.send_response(status)
  self.send_header('Content-Type',mime)
  self.send_header('Content-Length',str(len(body)))
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('X-Frame-Options','DENY')
  self.send_header('Referrer-Policy','no-referrer')
  self.send_header('Cache-Control','no-store')
  self.send_header('Content-Security-Policy',"default-src 'self'; font-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'")
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers()
  try:self.wfile.write(body)
  except (ConnectionResetError,BrokenPipeError):pass
 def json(self,object,status=200):self.respond(json.dumps(object,ensure_ascii=False).encode('utf-8'),'application/json; charset=utf-8',status)
 def do_GET(self):
  url=urlsplit(self.path);route=url.path;qs=parse_qs(url.query)
  try:
   if route in ('/','/index.html'):
    return self.respond((ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
   if route=='/app.js':return self.respond((ROOT/'app.js').read_bytes(),'text/javascript; charset=utf-8')
   if route=='/styles.css':return self.respond((ROOT/'styles.css').read_bytes(),'text/css; charset=utf-8')
   if route=='/api/templates':
    return self.json({'templates':[dict(id=k,**{x:v for x,v in obj.items() if x in ('label','license')}) for k,obj in FONTS.items()]})
   if route=='/api/glyph':
    return self.json(glyph_outline(qs.get('font',['gothic'])[0],qs.get('char',['가'])[0]))
   if route.startswith('/api/fonts/'):
    font_id=route.removeprefix('/api/fonts/')
    if font_id not in FONTS:return self.json({'error':'없는 글꼴입니다.'},404)
    return self.respond(ensure_font(font_id).read_bytes(),'font/ttf',headers={'Cache-Control':'private, max-age=3600'})
   if route=='/health':return self.json({'ok':True,'version':'2.0','local_only':True})
   return self.json({'error':'없는 페이지입니다.'},404)
  except StudioError as e:return self.json({'error':str(e)},400)
  except (OSError,ValueError) as e:return self.json({'error':'파일이나 데이터를 읽는 중 오류가 발생했습니다.'},500)
 def do_POST(self):
  if urlsplit(self.path).path!='/api/build':return self.json({'error':'없는 API입니다.'},404)
  origin=self.headers.get('Origin','')
  if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
   return self.json({'error':'이 주소에서는 요청할 수 없습니다.'},403)
  if 'application/json' not in self.headers.get('Content-Type',''):return self.json({'error':'JSON만 지원합니다.'},415)
  try:length=int(self.headers.get('Content-Length','0'))
  except ValueError:return self.json({'error':'잘못된 요청 크기입니다.'},400)
  if not 0<length<=MAX_PROJECT_BYTES:return self.json({'error':'프로젝트가 너무 큽니다.'},413)
  if not SLOTS.acquire(blocking=False):return self.json({'error':'다른 파일 생성이 진행 중입니다. 다시 시도하세요.'},429)
  try:
   try:
    data=json.loads(self.rfile.read(length))
    if not isinstance(data,dict):raise StudioError('올바른 프로젝트가 아닙니다.')
    fmt=data.get('format','ttf')
    raw,meta=build_font(data.get('project'),fmt)
    return self.respond(raw,'font/woff2' if fmt=='woff2' else 'font/ttf',headers={
     'Content-Disposition':f'attachment; filename="MGD-Font.{fmt}"',
     'X-Hangul-Count':str(meta['hangul']),
     'X-Modified-Count':str(meta['modified_glyphs'])})
   except (StudioError,ValueError,TypeError,KeyError) as exc:return self.json({'error':str(exc)},400)
   except Exception:
    import traceback;traceback.print_exc()
    return self.json({'error':'폰트 생성에 실패했습니다. 프로젝트 데이터를 확인하세요.'},500)
  finally:SLOTS.release()
 def log_message(self,fmt,*args):
  if self.path not in ('/health',):super().log_message(fmt,*args)

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8770);args=p.parse_args()
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 print(f'무가당 폰트 공방 v2: http://127.0.0.1:{args.port} (로컬 전용)',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()