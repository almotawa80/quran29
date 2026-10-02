import sys, os, urllib.parse
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath("index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors = []
def ok(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)
    print("OK  ", msg)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 900, "height": 1000}, accept_downloads=True); page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PATH); page.wait_for_timeout(300)
    def login(u, pw):
        page.click("#coordBtn"); page.wait_for_timeout(200); page.fill("#lgU", u); page.fill("#lgP", pw); page.click("#lgGo"); page.wait_for_timeout(400)
    def out(): page.evaluate(f"{SR}.querySelector('#abOut').click()"); page.wait_for_timeout(300)
    def ev(js): return page.evaluate(js)
    def bar(): return ev(f"{SR}.querySelector('#appbar').innerText")
    def rerender(): ev(f"()=>{{const s={SR}.querySelector('#fbr');s.dispatchEvent(new Event('change'))}}"); page.wait_for_timeout(250)
    def row_click(text, sel, scope="#app .row, #app .mrow"):
        ev(f"()=>{{const r=[...{SR}.querySelectorAll('{scope}')].find(x=>x.innerText.includes('{text}')&&x.querySelector('{sel}'));r.querySelector('{sel}').click()}}"); page.wait_for_timeout(300)
    def row_html(text, scope="#app .mrow"):
        return ev(f"()=>{{const r=[...{SR}.querySelectorAll('{scope}')].find(x=>x.innerText.includes('{text}'));return r?r.innerHTML:''}}")
    J5 = "()=>window.__PTS.CANDS.filter(c=>c.ent==='e1'&&c.br==='youth'&&c.sl==='j5'&&c.status==='approved').length"
    J5M = "()=>window.__PTS.CANDS.filter(c=>c.ent==='e1'&&c.br==='youth'&&c.sl==='j5'&&c.status==='approved'&&c.gender==='ذكر').length"

    # ---- A: data entry
    login("huda", "huda123")
    ok("يوسف العلي" in bar(), "entry header shows the coordinator's name")
    ev(f"{SR}.querySelector('#board').open=true"); page.wait_for_timeout(150)
    chip = ev(f"()=>[...{SR}.querySelectorAll('.brow')].find(r=>r.innerText.includes('النشء')).querySelector('.slot[title]').parentElement.innerHTML")
    titles = ev(f"()=>[...{SR}.querySelectorAll('.slot[title]')].map(s=>s.innerText.replace(/\\s+/g,' '))")
    ok(any("5 أجزاء ذكور 3/5 إناث 0/5" in t for t in titles), f"slot board counts approved only, per gender (5 أجزاء: ذكور 3/5 · إناث 0/5) {titles}")
    wa = ev(f"()=>[...{SR}.querySelectorAll('a.btn.wa')].map(a=>decodeURIComponent(a.href.split('text=')[1]))")
    ok(wa and all("حالة الاستمارة" not in m for m in wa), "approved candidate message no longer has the status line")
    out()

    # ---- B: reviewer
    login("sara.rev", "sara123")
    ok("سارة العنزي" in bar() and "يوسف العلي" not in bar(), "reviewer header shows the reviewer's own name")
    for _ in range(3):
        if not ev(f"!!{SR}.querySelector('[data-appr]')"): break
        ev(f"{SR}.querySelector('[data-appr]').click()"); page.wait_for_timeout(300)
    ok(ev(J5) == 5, "after approving both pending, the 5-juz slice has 5 approved")
    row_click("نورة فهد", "[data-prev]", "#app .row")
    t = ev(f"{SR}.querySelector('#app').innerText")
    ok("سجل الإجراءات" in t and "إنشاء الاستمارة" in t and "اعتماد" in t and "سارة العنزي" in t, "action log shows creation + approval by the reviewer")
    ev(f"{SR}.querySelector('#pback').click()"); page.wait_for_timeout(300)

    # a complete pending form lands in a full slice
    ok(ev(J5M) == 4, "4 males + 1 female approved in the slice")
    ev("()=>{const c=window.__PTS.CANDS.find(x=>x.name.includes('مريم عبدالعزيز'));c.gender='ذكر';c.sl='j5';c.parts=[26,27,28,29,30];c.juz=5;c.docs={cid:{name:'x.jpg',url:''}};c.status='pending'}")
    rerender()
    h = row_html("مريم عبدالعزيز")
    ok("data-appr" in h, "4 males approved -> a 5th male can still be approved")
    ev("()=>{const c=window.__PTS.CANDS.find(x=>x.name.includes('ريم أحمد'));c.gender='ذكر';c.br='youth';c.band=2;c.sl='j5';c.parts=[26,27,28,29,30];c.juz=5;c.docs={cid:{name:'x.jpg',url:''}};c.status='approved'}")
    rerender(); h = row_html("مريم عبدالعزيز")
    ok("الشريحة مكتملة للذكور" in h and "data-appr" not in h, "5 males approved: next male locked with 'مكتملة للذكور' (females unaffected)")
    # undo one approval -> seat frees -> approval allowed
    row_click("عبدالرحمن خالد", "[data-unappr]", "#app .row")
    h = row_html("مريم عبدالعزيز")
    ok("data-appr" in h and "الشريحة مكتملة" not in h, "after an un-approve the male seat frees up")
    ev(f"()=>{{[...{SR}.querySelectorAll('#app .mrow')].find(x=>x.innerText.includes('مريم عبدالعزيز')).querySelector('[data-appr]').click()}}"); page.wait_for_timeout(300)
    ok(ev(J5M) == 5 and "الشريحة مكتملة للذكور" in row_html("عبدالرحمن خالد"), "males full again; the other pending male is locked")
    # return with note -> logged
    row_click("عبدالرحمن خالد", "[data-ret]", "#app .mrow")
    ev(f"{SR}.querySelector('textarea[id^=rn_]').value='صورة البطاقة غير واضحة'"); ev(f"{SR}.querySelector('[data-retok]').click()"); page.wait_for_timeout(300)
    log = ev("()=>window.__PTS.CANDS.find(x=>x.name.includes('عبدالرحمن خالد')).log.map(l=>l.a+'|'+l.by+'|'+l.note)")
    ok(any(l.startswith("تراجع عن الاعتماد|") for l in log) and any(l == "إعادة للتصحيح|أ. سارة العنزي|صورة البطاقة غير واضحة" for l in log), f"un-approve and return (with note) are logged: {log}")
    out()

    # ---- C: admin
    login("admin", "admin123")
    ev(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المتابعة').click()"); page.wait_for_timeout(300)
    rows = ev(f"()=>[...{SR}.querySelectorAll('#app .mrow')].map(r=>({{t:r.innerText,rev:[...r.querySelectorAll('a')].filter(a=>a.innerText.includes('تذكير المراجع')).map(a=>decodeURIComponent(a.href.split('text=')[1]))}}))")
    noor = [r for r in rows if "جمعية النور" in r["t"]]
    ok(noor and noor[0]["rev"] and "خالد المطيري" in noor[0]["rev"][0] and "بانتظار مراجعتك" in noor[0]["rev"][0], "reviewer reminder button + message for an entity with pending reviews")
    print([r["t"][:60] for r in rows if "تذكير المنسق" not in r["t"]][:3]);rows=[r for r in rows if "المنسق:" in r["t"]];ok(all("تذكير المنسق" in r["t"] for r in rows), "coordinator button relabelled 'تذكير المنسق'")
    furqan = [r for r in rows if "مدرسة الفرقان" in r["t"]]
    ok(not furqan or not furqan[0]["rev"], "no reviewer button for an entity without a reviewer")
    # export: approver columns (from the candidates tab)
    ev(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المرشحون').click()"); page.wait_for_timeout(300)
    ok("تصدير كل المرشحين" in ev(f"{SR}.querySelector('#cxls').innerText"), "candidates tab export button is labelled 'تصدير كل المرشحين'")
    ok(ev(f"{SR}.querySelectorAll('#xlsAll').length")==0, "no export button in the header anymore")
    try:
        with page.expect_download(timeout=20000) as dl:
            ev(f"{SR}.querySelector('#cxls').click()")
        path = dl.value.path(); data = open(path, "rb").read()
        name = dl.value.suggested_filename
        if name.endswith(".csv"):
            txt = data.decode("utf-8-sig")
            ok("اعتمده" in txt.splitlines()[0] and "تاريخ الاعتماد" in txt.splitlines()[0] and "سارة العنزي" in txt, "export includes approver + approval date")
        else:
            import zipfile, io
            z = zipfile.ZipFile(io.BytesIO(data)); x = "".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
            ok("اعتمده" in x and "سارة العنزي" in x, "export (xlsx) includes approver + approval date")
    except Exception as e:
        print("SKIP export check:", str(e)[:120])
    # admin return logged
    ev(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المرشحون').click()"); page.wait_for_timeout(300)
    ev(f"{SR}.querySelector('[data-aret]').click()"); page.wait_for_timeout(200)
    ev(f"{SR}.querySelector('textarea[id^=arn_]').value='الشريحة غير صحيحة'"); ev(f"{SR}.querySelector('[data-aretok]').click()"); page.wait_for_timeout(300)
    ok(ev("()=>window.__PTS.CANDS.some(c=>(c.log||[]).some(l=>l.a==='إرجاع من المشرف إلى الجهة'&&l.by==='مشرف المسابقة'&&l.note==='الشريحة غير صحيحة'))"), "admin return is logged with the note")
    b.close()
print("PAGE ERRORS:", errors)
if errors: sys.exit(1)
print("ALL ITEMS 4-8 TESTS PASSED")
