import sys,os
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":844});errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)));pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(400)
    pg.evaluate("[...document.querySelectorAll('.tb')].find(b=>b.textContent.includes('المزيد')).click()");pg.wait_for_timeout(400)
    ok=pg.evaluate("!!document.querySelector('#moreNav [data-qz-open]')");print("more row exists",ok)
    pg.click("#moreNav [data-qz-open]");pg.wait_for_timeout(400)
    o=pg.evaluate("!document.querySelector('.qz-dlg').hidden");print("opens from More",o)
    pg.click("[data-a=close]");pg.wait_for_timeout(200)
    print("still on More view:",pg.evaluate("!!document.querySelector('#moreNav')&&document.querySelector('#moreNav').offsetParent!==null"))
    pg.screenshot(path="/tmp/g_more.png");print("errors",errs)
    import sys;sys.exit(0 if ok and o and not errs else 1)
