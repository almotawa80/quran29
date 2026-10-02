import sys,os
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
with sync_playwright() as p:
    b=p.chromium.launch();errs=[]
    # sandbox-like: clipboard API throws, share missing, popups irrelevant
    ctx=b.new_context(viewport={"width":390,"height":844},has_touch=True,is_mobile=True);pg=ctx.new_page()
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_());pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('blocked')}}});navigator.canShare=undefined;")
    pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(400);ev=pg.evaluate
    pg.click("#shareOpen");pg.wait_for_timeout(500)
    pg.click("#shCopy");pg.wait_for_timeout(400)
    m=ev("document.querySelector('#shMsg').textContent");print(m)
    ok("نسخ" in m,"copy: message shown even when Clipboard API is blocked")
    sel=ev("(()=>{const t=document.querySelector('#shTxt');return t.selectionEnd-t.selectionStart})()");ok(sel>20 or "تم" in m,"text selected for manual copy (or copied via execCommand)")
    # name typed -> preview & text update
    pg.fill("#shName","خالد");pg.wait_for_timeout(500)
    ok("خالد" in ev("document.querySelector('#shTxt').value"),"text updates with the name")
    a=ev("document.querySelector('#shPv').src.length");pg.click("[data-t=cream]");pg.wait_for_timeout(300);b2=ev("document.querySelector('#shPv').src.length")
    ok(a!=b2,"preview image updates when the design changes")
    pg.click("#shShare");pg.wait_for_timeout(600)
    ok(not ev("document.querySelector('#shView').hidden"),"no Web Share on phone -> enlarged image for saving")
    print("errors",errs);ok(not errs,"no page errors")
