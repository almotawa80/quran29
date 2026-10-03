# assistant: «هل أفادتك الإجابة؟» under answers, and its card in the visitors dashboard
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ix.html";fails=[]
SR="document.querySelector('.pt-host').shadowRoot"
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":844});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(700);ev=pg.evaluate
    ev("window.__fb=[];{const o=Q29T.fb;Q29T.fb=(t,u)=>{__fb.push([t,u]);o(t,u)}};0")
    ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
    pg.fill("#aiIn","كم جائزة المسابقة العامة؟");ev("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(1300)
    ok(ev("document.querySelectorAll('#aiLog .ai-fb').length")==1,"one feedback row under the answer")
    ok(ev("document.querySelector('#aiLog .ai-fb').dataset.t")=="prizes","topic is prizes")
    ev("document.querySelector('#aiLog .ai-fb button[data-fb=\"1\"]').click()");pg.wait_for_timeout(200)
    ok(ev("__fb")==[["prizes",True]],"thumbs up sent "+str(ev("__fb")))
    ok("شكرًا لك" in ev("document.querySelector('#aiLog .ai-fb').innerText") and ev("document.querySelectorAll('#aiLog .ai-fb button').length")==0,"thanks shown, buttons gone")
    # guided flow: questions have no feedback, the result has it
    ev("[...document.querySelectorAll('#aiLog .ai-opt:not(:disabled)')].find(b=>b.textContent==='حدّد شريحتي').click()");pg.wait_for_timeout(1300)
    n0=ev("document.querySelectorAll('#aiLog .ai-fb').length")
    for l in ["عامة (حسب العمر والحفظ)","11 إلى 14 سنة","10 أجزاء"]:
        ev("l=>[...document.querySelectorAll('#aiLog .ai-opt:not(:disabled)')].find(b=>b.textContent===l).click()",l);pg.wait_for_timeout(1100)
    fbs=ev("[...document.querySelectorAll('#aiLog .ai-fb')].map(x=>x.dataset.t)")
    ok(n0==1 and fbs==["prizes","branches"],"no feedback on guided questions, result rated as branches "+str(fbs))
    ev("[...document.querySelectorAll('#aiLog .ai-fb button[data-fb=\"0\"]')].pop().click()");pg.wait_for_timeout(200)
    ok(ev("__fb")[-1]==["branches",False],"thumbs down sent")
    # dashboard card (sample data in the offline copy)
    ev("document.querySelector('.tb[data-v=\"0\"]').click()");pg.wait_for_timeout(200)
    pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(600)
    ev(f"{SR}.querySelector('.btn[data-at=vis]').click()");pg.wait_for_timeout(500)
    t=ev(f"{SR}.querySelector('#app').innerText")
    ok("تقييم إجابات المساعد" in t and "من التقييمات «أفادتني»" in t,"dashboard has the rating card")
    ok("نسبة رضا" in t,"story mentions satisfaction")
    pg.screenshot(path="/tmp/t34.png",full_page=False)
    ok(not errs,"no errors "+str(errs));b.close()
print("FAILS:",fails)
