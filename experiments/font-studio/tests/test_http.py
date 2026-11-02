import json
import subprocess
import sys
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fontTools.ttLib import TTFont
from io import BytesIO
from font_engine import default_project
ROOT=Path(__file__).resolve().parents[1]

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port','18766'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for i in range(40):
            try:
                with urllib.request.urlopen('http://127.0.0.1:18766/health',timeout=1) as r:
                    if json.load(r)['ok']:break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('server not ready')

    @classmethod
    def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=4)

    def test_page(self):
        with urllib.request.urlopen('http://127.0.0.1:18766/') as r:
            page=r.read().decode('utf8');self.assertIn('TTF 다운로드',page)
            self.assertEqual(r.status,200)

    def test_invalid_json(self):
        req=urllib.request.Request('http://127.0.0.1:18766/api/build',data=b'{}',method='POST')
        with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code,400)

    def test_build_real_ttf(self):
        payload=json.dumps({'project':default_project(),'name':'방문자폰트','format':'ttf'},ensure_ascii=False).encode()
        req=urllib.request.Request('http://127.0.0.1:18766/api/build',data=payload,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read();self.assertEqual(r.headers['X-Font-Hangul-Count'],'11172')
        f=TTFont(BytesIO(b));self.assertIn(0xAC00,f.getBestCmap())

if __name__=='__main__':unittest.main()
