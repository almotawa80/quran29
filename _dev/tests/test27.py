# split GitHub build: game data + font load only when the game opens
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ghsplit/index.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":844});reqs=[];errs=[]
    pg.on("request",lambda r:reqs.append(r.url));pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(1500)
    ok(not any("qz-data" in u or "hafs.woff2" in u for u in reqs),"home page does not download the Quran data or font")
    pg.click("[data-qz-open]");pg.wait_for_timeout(1500)
    ok(any("qz-data" in u for u in reqs),"opening the game downloads the data")
    st=pg.query_selector(".qz-dlg button.btn.pri, .qz-dlg [data-start], .qz-dlg #qzStart")
    pg.evaluate("(()=>{const b=[...document.querySelectorAll('.qz-dlg button')].find(x=>/ابدأ/.test(x.textContent));b&&b.click()})()");pg.wait_for_timeout(2000)
    t=pg.evaluate("document.querySelector('.qz-dlg').innerText")
    ok("السؤال" in t or "سؤال" in t,"a question is shown")
    ok(pg.evaluate("document.fonts.check('24px \"KFGQPC Hafs\"')"),"Quran font loaded")
    ok(any("hafs.woff2" in u for u in reqs),"font file downloaded when needed")
    ok(not errs,"no errors "+str(errs))
    b.close()
print("FAILS:",fails)
