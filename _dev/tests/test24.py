# after-hide behaviour of announcements (never / visits / days / pin) — offline copy
from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";SR="document.querySelector('.pt-host').shadowRoot";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":900});errs=[]
    def tabp():
        pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U,wait_until="domcontentloaded");pg.wait_for_timeout(500);return pg
    W1="مرحبًا بكم في دليل";W2="التسجيل في المسابقة عن طريق"
    g=lambda pg:pg.evaluate("document.querySelector('.gann-wrap').innerText")
    hide=lambda pg,txt:pg.evaluate(f"[...document.querySelectorAll('.gann')].find(x=>x.innerText.includes('{txt}')).querySelector('[data-gannx]').click()")
    # visits = 3
    pg=tabp();ok(W1 in g(pg),"visits: shown first time");hide(pg,W1);pg.wait_for_timeout(100);ok(W1 not in g(pg),"visits: hidden after ×")
    pg.reload();pg.wait_for_timeout(500);ok(W1 not in g(pg),"visits: stays hidden in the same visit");pg.close()
    seen=[]
    for i in range(3):
        pg=tabp();s=W1 in g(pg);seen.append(s)
        if s:hide(pg,W1)
        pg.close()
    ok(seen==[True,True,False],"visits=3: comes back on next 2 visits then gone for good "+str(seen))
    # days = 2
    pg=tabp();hide(pg,W2);pg.close()
    pg=tabp();ok(W2 not in g(pg),"days: hidden on the next visit before the days pass")
    pg.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('q29ax'));o['s-ann-2'].d='2020-01-01';localStorage.setItem('q29ax',JSON.stringify(o))})()");pg.close()
    pg=tabp();ok(W2 in g(pg),"days: comes back after the days pass");pg.close()
    # admin: form + pin + never
    pg=tabp();ev=pg.evaluate;app=lambda:ev(f"{SR}.querySelector('#app').innerText");sr=lambda s:pg.locator(".pt-host").locator(s)
    pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(500)
    ev(f"{SR}.querySelector('[data-at=ann]').click()");pg.wait_for_timeout(300)
    t=app();ok("يعود 3 مرات بعد الإخفاء" in t and "يعود بعد 2 يوم من الإخفاء" in t,"list shows after-hide setting")
    ok(ev(f"{SR}.querySelector('#annHNw').hidden"),"number hidden for 'لا يعود'")
    sr("#annH").select_option("visits");pg.wait_for_timeout(100)
    ok(not ev(f"{SR}.querySelector('#annHNw').hidden") and "كم مرة يعود" in app(),"number shown for visits")
    sr("#annH").select_option("days");pg.wait_for_timeout(100);ok("بعد كم يوم" in app(),"label switches for days")
    ev(f"{SR}.querySelector('[data-aud=public]').click()");pg.wait_for_timeout(100)
    ok(ev(f"{SR}.querySelector('#annH').value")=="days","choice kept after switching audience")
    sr("#annT").fill("إعلان أيام بلا عدد");sr("#annHN").fill("0");ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(200)
    ok("من 1 إلى 30" in ev(f"[...{SR}.querySelectorAll('.toast')].map(t=>t.textContent).join()"),"invalid number rejected")
    sr("#annH").select_option("pin");sr("#annT").fill("تنبيه مثبّت للجميع");ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(300)
    ok("مثبّت" in app(),"pin pill in list")
    pin=ev("(()=>{const x=[...document.querySelectorAll('.gann')].find(x=>x.innerText.includes('تنبيه مثبّت'));return x?!x.querySelector('[data-gannx]'):null})()")
    ok(pin is True,"pinned announcement has no × in the guide")
    sr("#annH").select_option("never");sr("#annT").fill("إعلان لا يعود");ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(300)
    ok(ev("__PTS.ANNS.find(a=>a.text==='إعلان لا يعود').hm")=="never","never saved")
    hide(pg,"إعلان لا يعود");pg.wait_for_timeout(100)
    ok(ev("(()=>{sessionStorage.clear();Q29ANN._m=[];return Q29ANN.isHidden(__PTS.ANNS.find(a=>a.text==='إعلان لا يعود'))})()"),"never: stays hidden on later visits")
    pg.close()
    # entity banner follows the setting (days for s-ann-3)
    ctx=b.new_context(viewport={"width":390,"height":900})
    pg=tabp();ev=pg.evaluate
    pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(500)
    ok(ev(f"{SR}.querySelectorAll('[data-ann]').length")==1,"entity sees its announcement")
    ev(f"{SR}.querySelector('[data-annx]').click()");pg.wait_for_timeout(200);ok(ev(f"{SR}.querySelectorAll('[data-ann]').length")==0,"entity can hide it")
    pg.close();pg=tabp();ev=pg.evaluate
    if ev("!document.querySelector('.pt-host')"):
        pg.click("#coordBtn");pg.wait_for_timeout(200)
    if pg.is_visible("#lgU"):
        pg.fill("#lgP","huda123");pg.click("#lgGo")
    pg.wait_for_timeout(600)
    ok(ev(f"{SR}.querySelectorAll('[data-ann]').length")==0,"entity: hidden until the days pass")
    ok(not errs,"no page errors "+str(errs))
    b.close()
print("FAILS:",fails)
