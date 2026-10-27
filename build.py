"""무가당 사이트 만들기: src/ 원본 → index.html(실제 사이트) · preview.html(기기별 미리보기) · tests/site/(시험용)
사용: python3 build.py
src/app.html 만 고치고, index.html·preview.html 은 직접 고치지 마세요(다시 만들 때 덮여요)."""
import base64, re, os
ROOT = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(ROOT, *a)
# 공개해도 되는 값(publishable key). 비밀 키(sb_secret_…, service_role)는 절대 여기에 넣지 않음
SB_URL = "https://idahhgtpawkrdikuvfbv.supabase.co"
SB_KEY = "sb_publishable_lRONSNzx0aDW360_AxJwBA_NgyvxkX0"
app = open(p("src", "app.html"), encoding="utf-8").read()
viewer = open(p("src", "viewer.src.html"), encoding="utf-8").read()
assert app.count("<head>") >= 1
# 1) 실제 사이트: 서버 연결 켬
cfg = f'<script src="vendor/supabase-2.110.1.js"></script><script>window.MGD_SB={{url:"{SB_URL}",key:"{SB_KEY}"}}</script>'
site = re.sub(r"<title>.*?</title>", "<title>무가당</title>", app.replace("<head>", "<head>" + cfg, 1), count=1)
open(p("index.html"), "w", encoding="utf-8").write(site)
# 2) 미리보기: 서버 없이 브라우저에만 저장
out = viewer.replace("@@APP@@", base64.b64encode(app.encode("utf-8")).decode())
if not out.lstrip().lower().startswith("<!doctype"):
    out = '<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>무가당 미리보기</title></head><body>\n' + out + "\n</body></html>"
open(p("preview.html"), "w", encoding="utf-8").write(out)
# 3) 시험용: 서버 없는 앱 + 가짜 서버 붙인 앱
os.makedirs(p("tests", "site"), exist_ok=True)
open(p("tests", "site", "app.html"), "w", encoding="utf-8").write(app)
mock = '<script src="mocksb.js"></script><script>window.MGD_SB={url:"https://x.supabase.co",key:"sb_publishable_x"}</script>'
open(p("tests", "site", "app_sb.html"), "w", encoding="utf-8").write(app.replace("<head>", "<head>" + mock, 1))
print("만들었어요: index.html, preview.html, tests/site/")
