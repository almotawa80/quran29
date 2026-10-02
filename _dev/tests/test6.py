import sys, os, urllib.parse
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath("index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors = []
PNG = "/tmp/t6.png"
open(PNG, "wb").write(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da6364f8ff1f0003030200efa1b8a50000000049454e44ae426082"))
ROWS = f"""()=>[...{SR}.querySelectorAll('#app .row, #app .mrow')].map(r=>({{name:(r.querySelector('.nm,b')||{{}}).textContent,st:r.innerText,req:[...r.querySelectorAll('a.btn.wareq')].map(a=>decodeURIComponent(a.href.split('text=')[1]))}}))"""
def ok(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)
    print("OK  ", msg)
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(viewport={"width": 900, "height": 1000})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PATH); page.wait_for_timeout(300)
    def login(u, pw):
        page.click("#coordBtn"); page.wait_for_timeout(200); page.fill("#lgU", u); page.fill("#lgP", pw); page.click("#lgGo"); page.wait_for_timeout(400)
    def setdate(v): page.evaluate(f"()=>{{const d={SR}.querySelector('#simDate');d.value='{v}';d.dispatchEvent(new Event('change'))}}")
    def out(): page.evaluate(f"{SR}.querySelector('#abOut').click()"); page.wait_for_timeout(300)

    login("huda", "huda123")
    rows = page.evaluate(ROWS)
    with_btn = [r for r in rows if r["req"]]
    ok(len(with_btn) >= 1, f"request button shown for incomplete candidates ({len(with_btn)} rows incl. the 'needs completing' box)")
    ok(all("معتمد" not in r["st"].split("\n")[0] or "مسودة" in r["st"] for r in with_btn), "never shown on approved rows")
    ok(not any(r["req"] for r in rows if "بانتظار المراجعة" in r["st"] or "مُعاد للتصحيح" in r["st"]), "not shown for complete pending/corrected forms")
    msg = with_btn[0]["req"][0]
    print("---- message ----\n" + msg + "\n-----------------")
    ok("السلام عليكم مريم عبدالعزيز الفيلكاوي،" in msg and "ولي أمر المتسابق" not in msg, "greeting uses the candidate name only")
    ok("صورة واضحة للبطاقة المدنية" in msg and "29 أكتوبر" in msg and "مركز الهدى" in msg, "message lists missing item, deadline and entity")
    page.screenshot(path="s21_entry.png")

    # attach the civil ID -> form becomes complete -> button disappears
    page.evaluate(f"""()=>{{const r={SR};[...r.querySelectorAll('.row')].find(x=>x.innerText.includes('مريم عبدالعزيز')).querySelector('[data-edit]').click()}}""")
    page.wait_for_timeout(300)
    page.locator("input[data-doc='cid']").first.set_input_files(PNG); page.wait_for_timeout(400)
    page.evaluate(f"{SR}.querySelector('#cf button[type=submit]').click()"); page.wait_for_timeout(400)
    rows = page.evaluate(ROWS)
    maryam = [r for r in rows if r["name"] and "مريم عبدالعزيز" in r["name"]]
    ok(maryam and not any(r["req"] for r in maryam), "button disappears once the missing document is attached")
    ok(any("بانتظار المراجعة" in r["st"] for r in maryam), "completed form went to the reviewer (pending)")

    # edit period: deadline switches to 12 November
    setdate("2026-11-05"); page.wait_for_timeout(300)
    out(); login("furqan", "furqan123")
    setdate("2026-11-05"); page.wait_for_timeout(300)
    rows = page.evaluate(ROWS); reqs = [m for r in rows for m in r["req"]]
    ok(reqs and "12 نوفمبر" in reqs[0] and "موافقة ولي الأمر" in reqs[0], "edit period: deadline 12 Nov, guardian consent requested")
    # closed: no button
    setdate("2026-11-14"); page.wait_for_timeout(300)
    ok(not any(r["req"] for r in page.evaluate(ROWS)), "closed period: no request button")
    setdate("2026-10-10"); page.wait_for_timeout(300)
    out()

    login("sara.rev", "sara123")
    ok(not any(r["req"] for r in page.evaluate(ROWS)), "reviewer does not get the button")
    out()
    b.close()
print("PAGE ERRORS:", errors)
if errors: sys.exit(1)
print("ALL MISSING-ITEMS REQUEST TESTS PASSED")
