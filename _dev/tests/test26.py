from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";SR="document.querySelector('.pt-host').shadowRoot";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in ("light","dark"):
        pg=b.new_page(viewport={"width":390,"height":844},color_scheme=th);errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U);pg.wait_for_timeout(500);ev=pg.evaluate
        pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(600)
        ev(f"{SR}.querySelector('#abOut').click()");pg.wait_for_timeout(500)
        ok(ev("!document.querySelector('.pt-host')"),th+": logout returns to the guide")
        ok(pg.is_visible("#ptBye") and "تم تسجيل الخروج" in pg.inner_text("#ptBye"),th+": logout message shown")
        bb=ev("[...document.querySelectorAll('#ptBye button')].map(b=>{const r=b.getBoundingClientRect();return [r.width,r.height]})");ok(all(w>=44 and h>=44 for w,h in bb),th+": buttons are 44px")
        r=ev("(()=>{const e=document.querySelector('#ptBye').getBoundingClientRect();return [e.left,e.right,innerWidth]})()");ok(r[0]>=0 and r[1]<=r[2],th+": fits the screen")
        pg.screenshot(path=f"/tmp/bye_{th}.png")
        pg.click("#ptBye .go");pg.wait_for_timeout(300)
        ok(pg.is_visible("#lgU") and pg.input_value("#lgU")=="",th+": 'another account' opens an empty sign-in")
        pg.keyboard.press("Escape");pg.wait_for_timeout(200)
        pg.fill("#lgU","admin") if pg.is_visible("#lgU") else pg.click("#coordBtn")
        pg.wait_for_timeout(200)
        if not pg.is_visible("#lgU"): pg.click("#coordBtn");pg.wait_for_timeout(200)
        pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(600)
        ev(f"{SR}.querySelector('#abOut').click()");pg.wait_for_timeout(400)
        pg.click("#ptBye .x");pg.wait_for_timeout(200);ok(not pg.is_visible("#ptBye"),th+": × closes the message")
        ev(f"document.querySelector('#coordBtn').click()");pg.wait_for_timeout(200)
        ev(f"document.querySelector('#lgU')")
        pg.keyboard.press("Escape");pg.wait_for_timeout(200)
        ok(not errs,th+": no errors "+str(errs));pg.close()
    b.close()
print("FAILS:",fails)
