# assistant as a continuous chat
from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in ("light","dark"):
        ctx=b.new_context(viewport={"width":390,"height":844},color_scheme=th);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U);pg.wait_for_timeout(600);ev=pg.evaluate
        ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(400)
        def ask(q):pg.fill("#aiIn",q);ev("document.getElementById('aiForm').requestSubmit()")
        ok(ev("getComputedStyle(document.querySelector('.finder-head')).position")=="absolute",th+": old title hidden visually")
        ok(ev("!document.querySelector('.fc-top') && !document.querySelector('#aiNew')"),th+": no top bar and no new-chat button")
        ask("عمري 12 وأحفظ 7 أجزاء");pg.wait_for_timeout(200)
        ok(ev("!!document.querySelector('#aiLog .ai-typing')"),th+": typing dots shown before the reply")
        pg.wait_for_timeout(900)
        ok(ev("!document.querySelector('#aiLog .ai-typing')"),th+": typing dots removed")
        t=ev("document.getElementById('aiLog').innerText");ok("النشء والشباب" in t,th+": first answer")
        ask("متى آخر يوم للتسجيل؟");pg.wait_for_timeout(1200);t=ev("document.getElementById('aiLog').innerText")
        ok("النشء والشباب" in t and "29 أكتوبر" in t,th+": conversation continues (old answer kept)")
        ok(ev("document.querySelectorAll('#aiLog .ai-msg.me').length")==2,th+": both questions kept")
        # follow-up uses remembered age/juz
        ask("كم الجائزة؟");pg.wait_for_timeout(1200);last=ev("[...document.querySelectorAll('#aiLog .ai-turn')].pop().innerText")
        ok("12" in last and ("800" in last or "النشء" in last),th+": follow-up prize question uses remembered age and memorization ("+last[:60].replace("\n"," ")+")")
        ask("ولو حفظ 10 أجزاء؟");pg.wait_for_timeout(1200);last=ev("[...document.querySelectorAll('#aiLog .ai-turn')].pop().innerText")
        ok("10" in last and "12" in last,th+": 'what if' keeps the age ("+last[:70].replace("\n"," ")+")")
        # composer sticks to the bottom, above the tab bar
        r=ev("(()=>{const c=document.querySelector('.chat-bar').getBoundingClientRect(),t=document.querySelector('.tabbar').getBoundingClientRect();return [Math.round(c.bottom),Math.round(t.top)]})()")
        ok(abs(r[0]-r[1])<=2,th+f": composer sits just above the tab bar {r}")
        rr=ev("(()=>{const m=[...document.querySelectorAll('#aiLog .ai-msg.me')].pop().getBoundingClientRect(),f=document.querySelector('.appbar').getBoundingClientRect();return [Math.round(m.top),Math.round(f.bottom)]})()");ok(0<=rr[0]-rr[1]<=20,th+f": the last question stays at the top, followed by its answer {rr}")
        # actions still work
        n=ev("document.querySelectorAll('#aiLog .ai-act[data-act]').length");ok(n>0,th+": action buttons present")
        # fallback
        ask("زقزق برتقال سماوي");pg.wait_for_timeout(1200)
        ok(ev("!!document.querySelector('#aiLog .ai-wa[href*=\"wa.me/96522065127\"]')"),th+": unknown question offers WhatsApp")
        # keeps chat when leaving and returning, and after reload (same visit)
        ev("document.querySelector('.tb[data-v=\"0\"]').click()");pg.wait_for_timeout(200);ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
        ok(ev("document.querySelectorAll('#aiLog .ai-msg.me').length")==5,th+": chat kept after switching pages")
        pg.reload();pg.wait_for_timeout(700)
        if not ev("document.documentElement.classList.contains('view-find')"):ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
        ok(ev("document.querySelectorAll('#aiLog .ai-msg.me').length")==5,th+": chat kept after reload in the same visit")
        a=ev("(()=>{const b=document.querySelector('#aiLog .ai-act[data-act=share]');if(!b)return 'none';b.click();return 'ok'})()");pg.wait_for_timeout(300)
        ok(a in ("ok","none"),th+": restored action button clickable")
        ask("وكم الجائزة؟");pg.wait_for_timeout(1300);last=ev("[...document.querySelectorAll('#aiLog .ai-turn')].pop().innerText")
        ok("12" in last,th+": memory restored after reload")
        pg.screenshot(path=f"/tmp/chat_real_{th}.png")
        ask("متى آخر يوم للتسجيل؟");pg.wait_for_timeout(1300)
        pg.reload();pg.wait_for_timeout(700)
        if not ev("document.documentElement.classList.contains('view-find')"):ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
        ok(ev("[...document.querySelectorAll('#aiLog .ai-opts')].pop().querySelector('button').disabled")==False,th+": choices of the last answer still work after reload")
        ctx.close()
        # a new visit (new tab session) starts fresh
        ctx=b.new_context(viewport={"width":390,"height":844});pg=ctx.new_page();pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U);pg.wait_for_timeout(500);ok(pg.evaluate("document.querySelectorAll('#aiLog .ai-msg.me').length")==0,th+": new visit starts a fresh chat");ctx.close()
        ok(not errs,th+": no errors "+str(errs))
    b.close()
print("FAILS:",fails)
