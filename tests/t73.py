# 알아서 모으기 AI: 지금은 보류(2026-11-02, 주인). 설정에 안 보이고, 예전에 켜 둔 계정도 발행할 때 AI를 부르지 않아야 함
# (켤 때 쓰던 시험은 git 기록의 이전 t73에 있어요. 쓰는 중 제안 방식은 ai-while-writing 브랜치)
from base import *
import json
U2='http://127.0.0.1:8820/app_sb.html'
AI='https://mugadang-ai.sigmund0530.workers.dev/**'
def ok(c,m,x=''):print(('OK  ' if c else 'FAIL'),m,x)
calls=[]
def fake(route):calls.append(route.request.url);route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body='{"items":[{"word":"망원시장","kind":"장소"}]}')
with sync_playwright() as p:
  b=p.chromium.launch()
  ctx=b.new_context(viewport={'width':1280,'height':800});pg=ctx.new_page();pg.set_default_timeout(6000);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  ctx.route(AI,fake)
  pg.goto(U2);pg.wait_for_timeout(600);pg.locator('[data-au-method="email"]').click();pg.locator('[data-au-all]').check();pg.locator('[data-au-next]').click();pg.wait_for_timeout(200)
  pg.fill('#au-mail','hold@x.com');pg.fill('#au-pw','password123');pg.fill('#au-pw2','password123');pg.fill('#au-sqa','a');pg.fill('#ob-name','하루');pg.fill('#ob-handle','hold1');pg.fill('#au-invite','MUGADANG-BETA')
  pg.locator('[data-au-make]').click();pg.wait_for_timeout(700);pg.locator('[data-aup-skip]').click();pg.wait_for_timeout(500);pg.locator('[data-au-enter]').click();pg.wait_for_timeout(1500)
  pg.evaluate("()=>{const r=JSON.parse(localStorage.getItem('mgd2.v1.records'));r.settings.aiCollect=true;localStorage.setItem('mgd2.v1.records',JSON.stringify(r))}");pg.reload();pg.wait_for_timeout(1500)
  pg.locator('[data-pn="acct"]').click();pg.wait_for_timeout(200);pg.locator('.pn-card [data-pc="acctset"]').click();pg.wait_for_timeout(300)
  ok(pg.locator('.set-ai').count()==0,'보류 중엔 설정에 안 보임');closeall(pg);pg.go_back();pg.wait_for_timeout(300)
  write(pg,False,'보류 글','망원시장에서 고로케를 샀다.');pg.wait_for_timeout(800)
  ok(len(calls)==0,'켜 둔 계정도 발행 때 AI 안 부름',calls);ok(pg.locator('.rte-area mark[data-pf]').count()==0,'단어 표시 안 붙음')
  ok(not errs,'ERR',errs);b.close()
