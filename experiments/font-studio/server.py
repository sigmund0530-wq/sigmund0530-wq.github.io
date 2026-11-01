"""Start with `python server.py` and visit http://127.0.0.1:8766.

Only listens on loopback; the font compilation API does not authenticate users.
Do not publicly expose this experimental server without auth/rate limiting.
"""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from font_engine import compile_font,InputError,MAX_PROJECT_BYTES

ROOT=Path(__file__).resolve().parent

class Handler(BaseHTTPRequestHandler):
    def send_body(self,body,mime,status=200,headers=None):
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self' data: blob: 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(body)

    def send_json(self,data,status=200):
        self.send_body(json.dumps(data,ensure_ascii=False).encode('utf-8'),'application/json; charset=utf-8',status)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/':path='/index.html'
        if path not in ('/index.html','/health'):
            return self.send_json({'error':'없는 페이지입니다.'},404)
        if path=='/health':return self.send_json({'ok':True,'service':'mgd-font-studio'})
        return self.send_body((ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')

    def do_POST(self):
        if urlparse(self.path).path!='/api/build':return self.send_json({'error':'없는 API입니다.'},404)
        length=int(self.headers.get('Content-Length','0') or 0)
        if not 0<length<=MAX_PROJECT_BYTES:
            return self.send_json({'error':'작업 파일 크기가 너무 큽니다.'},413)
        try:
            body=json.loads(self.rfile.read(length))
            format=body.get('format','ttf')
            raw,meta=compile_font(body['project'],body.get('name','나의 글꼴'),format)
        except (InputError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            return self.send_json({'error':str(exc)},400)
        except Exception:
            # Avoid traceback disclosure to clients, log locally for troubleshooting.
            self.log_exception()
            return self.send_json({'error':'폰트 생성 중 오류가 발생했습니다.'},500)
        self.send_body(raw,'font/woff2' if format=='woff2' else 'font/ttf',200,{
            'X-Font-Hangul-Count':str(meta['hangul_syllables']),
            'X-Font-Override-Count':str(meta['overrides']),
            'Content-Disposition':f'attachment; filename="mgd-font.{format}"'
        })

    def log_exception(self):
        import traceback
        traceback.print_exc()


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766)
    args=p.parse_args()
    srv=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'\n무가당 글자공방: http://127.0.0.1:{args.port}\n종료: Ctrl+C\n',flush=True)
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()

if __name__=='__main__':main()
