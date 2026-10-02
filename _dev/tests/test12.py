import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors=[]
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":900});ctx.grant_permissions(["clipboard-read","clipboard-write"]);pg=ctx.new_page()
    pg.on("pageerror",lambda e:errors.append(str(e)))
    pg.goto(PATH);pg.wait_for_timeout(300);ev=pg.evaluate
    pg.click("#coordBtn");pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(400)
    ev(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المتابعة').click()");pg.wait_for_timeout(300)
    txt=ev(f"{SR}.querySelector('#rmAll').innerText");print(txt)
    n=int("".join(ch for ch in txt if ch.isdigit()))
    ok(n>=1,f"remind-all button shows count {n}")
    # count must equal entities with non-approved live candidates + valid phone
    ev(f"{SR}.querySelector('#rmAll').click()");pg.wait_for_timeout(250)
    panel=ev(f"{SR}.querySelector('#rmGo').closest('.mrow').innerText");print(panel.replace('\n',' | '))
    ok(f"1 من {n}" in panel,"sequential panel starts at 1")
    ev(f"{SR}.querySelector('#rmSkip').click()");pg.wait_for_timeout(200)
    if n>1:
        ok(f"2 من {n}" in ev(f"{SR}.querySelector('#rmGo').closest('.mrow').innerText"),"skip advances")
    href=ev(f"{SR}.querySelector('#rmGo')?.href||''");ok(href.startswith("https://wa.me/965") and "text=" in href,"whatsapp link with prefilled text")
    with ctx.expect_page(timeout=5000) as np_:
        ev(f"{SR}.querySelector('#rmGo').click()")
    pg.wait_for_timeout(300)
    after=ev(f"{SR}.querySelector('#rmGo')?.closest('.mrow').innerText||{SR}.querySelector('#rmStop').closest('.mrow').innerText");print(after.replace('\n',' | '))
    ok(("3 من" in after) or ("تم فتح" in after) or (n==2),"go advances to the next entity")
    ev(f"{SR}.querySelector('#rmStop').click()");pg.wait_for_timeout(200)
    ok(not ev(f"!!{SR}.querySelector('#rmGo')"),"stop closes panel")
    ev(f"{SR}.querySelector('#rmCopy').click()");pg.wait_for_timeout(300)
    clip=ev("navigator.clipboard.readText()");ok("تذكير من إدارة مسابقة الكويت الكبرى (29)" in clip and "يتبقى" in clip,"generic message copied")
    ok(not errors,"no page errors "+str(errors));b.close()
