import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors=[]
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
H2C=open("/tmp/h2c/package/dist/html2canvas.js",encoding="utf-8").read()
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":900},accept_downloads=True);pg=ctx.new_page()
    pg.on("pageerror",lambda e:errors.append(str(e)))
    pg.route("**/html2canvas*",lambda r:r.fulfill(status=200,content_type="application/javascript",body=H2C))
    pg.goto(PATH);pg.wait_for_timeout(300);ev=pg.evaluate
    pg.click("#coordBtn");pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(400)
    def prev(name):
        ev(f"()=>{{const r=[...{SR}.querySelectorAll('#app .row')].find(x=>x.innerText.includes('{name}'));r.querySelector('[data-prev]').click()}}");pg.wait_for_timeout(300)
    prev("محمد سالم الرشيدي")   # approved
    ok(ev(f"!!{SR}.querySelector('#cardBtn')"),"card button for approved candidate")
    with pg.expect_download(timeout=20000) as d: ev(f"{SR}.querySelector('#cardBtn').click()")
    dl=d.value;data=open(dl.path(),'rb').read()
    ok(data[:8]==b'\x89PNG\r\n\x1a\n' and len(data)>5000,f"PNG downloaded ({dl.suggested_filename}, {len(data)} bytes)")
    open("/tmp/card.png","wb").write(data)
    ev(f"{SR}.querySelector('#pback').click()");pg.wait_for_timeout(300)
    prev("نورة فهد المطيري")   # pending
    ok(not ev(f"!!{SR}.querySelector('#cardBtn')"),"no card button for pending candidate")
    ok(not errors,"no page errors "+str(errors))
    b.close()
