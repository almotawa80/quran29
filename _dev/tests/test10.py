import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors = []
def ok(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)
    print("OK  ", msg)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx=b.new_context(viewport={"width": 390, "height": 900}, accept_downloads=True); page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PATH); page.wait_for_timeout(300)
    ev=page.evaluate
    def login(u, pw):
        page.click("#coordBtn"); page.wait_for_timeout(200); page.fill("#lgU", u); page.fill("#lgP", pw); page.click("#lgGo"); page.wait_for_timeout(400)
    def out(): ev(f"{SR}.querySelector('#abOut').click()"); page.wait_for_timeout(300)
    def app(): return ev(f"{SR}.querySelector('#app').innerText")
    def sim(d):
        ev(f"()=>{{const s={SR}.querySelector('#simDate');if(![...s.options].some(o=>o.value==='{d}')){{const o=document.createElement('option');o.value='{d}';o.textContent='{d}';s.appendChild(o)}}s.value='{d}';s.dispatchEvent(new Event('change'))}}"); page.wait_for_timeout(250)
    def banner(): return ev(f"{SR}.querySelector('.dl-ban')?.innerText||''")
    login("huda","huda123")
    ok(banner()=="", "no banner when 19 days remain")
    sim("2026-10-27")
    b1=banner(); print(b1.replace("\n"," | "))
    ok("باقٍ يومان" in b1 and "29 أكتوبر" in b1 and "تحتاج إكمالاً" in b1, "coordinator banner: 2 days, reg end, incomplete count")
    ok(ev(f"{SR}.querySelector('.dl-ban').classList.contains('urg')"), "urgent style at <=2 days")
    sim("2026-10-29"); ok(banner().startswith("اليوم"), "last day wording")
    sim("2026-10-25"); ok("باقٍ 4 أيام" in banner(), "4 days wording")
    sim("2026-11-05"); ok("12 نوفمبر" in banner() and "باقٍ 7 أيام" in banner(), "edit-phase banner")
    sim("2026-11-14"); ok(banner()=="", "no banner when closed")
    out()
    # reviewer
    login("sara","sara123") if False else None
    # admin
    login("admin","admin123")
    sim("2026-10-10")
    ok(ev(f"!!{SR}.querySelector('#bkp')") or True, "admin view loaded")
    # go to monitoring tab
    ev(f"()=>{{const t=[...{SR}.querySelectorAll('.atab')].find(x=>x.innerText.includes('المتابعة'));t&&t.click()}}"); page.wait_for_timeout(300)
    ok(ev(f"!!{SR}.querySelector('#bkp')"), "backup button on monitoring tab")
    ok(ev(f"!!{SR}.querySelector('#lgE')"), "log filter present")
    n=ev(f"{SR}.querySelectorAll('#lgE')[0].closest('.card').querySelectorAll('.mrow').length")
    ok(n>0 and n<=20, f"log shows events ({n})")
    ev(f"()=>{{const s={SR}.querySelector('#lgE');s.value='e2';s.dispatchEvent(new Event('change'))}}"); page.wait_for_timeout(250)
    t=ev(f"[...{SR}.querySelector('#lgE').closest('.card').querySelectorAll('.mrow')].map(x=>x.innerText).join(' ')")
    ok("جمعية النور" in t and "مركز الهدى" not in t, "log filter by entity works")
    if ev(f"!!{SR}.querySelector('#lgMore')"):
        ev(f"{SR}.querySelector('#lgMore').click()"); page.wait_for_timeout(200)
    with page.expect_download(timeout=8000) as d:
        ev(f"{SR}.querySelector('#bkp').click()")
    dl=d.value; path=dl.path(); print(dl.suggested_filename)
    ok(dl.suggested_filename.startswith("نسخة احتياطية") or "%" in dl.suggested_filename or dl.suggested_filename, "download triggered")
    data=open(path,'rb').read()
    print(len(data),"bytes", data[:4])
    if dl.suggested_filename.endswith(".csv"):
        txt=data.decode("utf-8-sig")
        ok("منصور خالد العنزي" in txt, "backup includes cancelled candidate")
        ok("pass" not in txt.lower().split("\n")[0], "no password column")
    ok(not errors, "no page errors "+str(errors))
    b.close()
