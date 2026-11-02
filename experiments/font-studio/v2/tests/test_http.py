import urllib.request
import urllib.error
import json
import io
import subprocess
import socket
import time
import sys
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from font_service import project_default

class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=socket.socket();s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1];s.close()
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port',str(cls.port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(40):
   try:
    urllib.request.urlopen(f'http://127.0.0.1:{cls.port}/health',timeout=1);break
   except Exception:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=10)
 def url(self,p):return f'http://127.0.0.1:{self.port}'+p
 def test_get_templates_and_glyph(self):
  with urllib.request.urlopen(self.url('/api/templates')) as r:
   x=json.load(r);self.assertGreaterEqual(len(x['templates']),3)
  with urllib.request.urlopen(self.url('/api/glyph?font=gothic&char=%EA%B0%80')) as r:
   x=json.load(r);self.assertGreater(x['points'],10)
 def test_post_real_font(self):
  p=project_default();body=json.dumps({'project':p,'format':'ttf'}).encode()
  req=urllib.request.Request(self.url('/api/build'),data=body,headers={'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(req,timeout=40) as r:
   self.assertEqual(r.headers['X-Hangul-Count'],'11172')
   font=TTFont(io.BytesIO(r.read()));self.assertEqual(len([c for c in font.getBestCmap() if 0xAC00<=c<=0xD7A3]),11172)
 def test_reject_bad_request(self):
  bad={'project':dict(project_default(),width=999),'format':'ttf'}
  req=urllib.request.Request(self.url('/api/build'),data=json.dumps(bad).encode(),headers={'Content-Type':'application/json'},method='POST')
  with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req,timeout=40)
  self.assertEqual(err.exception.code,400)
 def test_reject_origin(self):
  body=json.dumps({'project':project_default(),'format':'ttf'}).encode()
  req=urllib.request.Request(self.url('/api/build'),data=body,headers={'Content-Type':'application/json','Origin':'https://malicious.example'},method='POST')
  with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req,timeout=5)
  self.assertEqual(err.exception.code,403)

if __name__=='__main__':unittest.main()