import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath("index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors = []
def ok(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)
    print("OK  ", msg)
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(viewport={"width": 900, "height": 1000})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PATH); page.wait_for_timeout(300)
    def login(u, pw):
        page.click("#coordBtn"); page.wait_for_timeout(200); page.fill("#lgU", u); page.fill("#lgP", pw); page.click("#lgGo"); page.wait_for_timeout(400)
    def out(): page.evaluate(f"{SR}.querySelector('#abOut').click()"); page.wait_for_timeout(300)
    def ev(js): return page.evaluate(js)
    BOX = f"()=>{{const h=[...{SR}.querySelectorAll('#app h2')].find(x=>x.innerText.includes('مُعادة للتصحيح'));if(!h)return null;const card=h.closest('.card');const top=[...{SR}.querySelectorAll('#app .card')].indexOf(card);return {{t:card.innerText,idx:top}}}}"

    # 1) reviewer-returned form shows at the top for the coordinator
    login("huda", "huda123")
    box = ev(BOX)
    ok(box and "عبدالله يوسف الكندري" in box["t"] and "ملاحظة المراجع" in box["t"] and "صورة أوضح" in box["t"] and "سارة العنزي" in box["t"], "returned form listed at the top with the reviewer's note and name")
    ok(box["idx"] == 0, "the returned-forms box is the first card under the tiles")
    page.screenshot(path="s23_corr.png")
    # open it -> form shows the note banner; save -> goes back to review and leaves the box
    ev(f"()=>{{const h=[...{SR}.querySelectorAll('#app h2')].find(x=>x.innerText.includes('مُعادة للتصحيح'));h.closest('.card').querySelector('[data-edit]').click()}}"); page.wait_for_timeout(300)
    t = ev(f"{SR}.querySelector('#app').innerText")
    ok("ملاحظة المراجع:" in t and "صورة أوضح" in t, "form opens with the reviewer's note banner")
    ev(f"{SR}.querySelector('#cf button[type=submit]').click()"); page.wait_for_timeout(400)
    ok(ev(BOX) is None, "after saving, the form leaves the returned box (re-sent for review)")
    ok(ev("()=>window.__PTS.CANDS.find(c=>c.name.includes('عبدالله يوسف')).status") == "pending", "status is back to pending review")
    out()

    # 2) admin returns an approved candidate of an entity WITHOUT a reviewer
    login("admin", "admin123")
    ev(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المرشحون').click()"); page.wait_for_timeout(300)
    ev(f"()=>[...{SR}.querySelectorAll('#app .row')].find(r=>r.innerText.includes('علي حسين الصفار')).querySelector('[data-aret]').click()"); page.wait_for_timeout(200)
    ev(f"{SR}.querySelector('textarea[id^=arn_]').value='الأجزاء المختارة غير صحيحة'"); ev(f"{SR}.querySelector('[data-aretok]').click()"); page.wait_for_timeout(300)
    out()
    login("furqan", "furqan123")
    box = ev(BOX)
    ok(box and "علي حسين الصفار" in box["t"] and "ملاحظة المشرف" in box["t"] and "الأجزاء المختارة غير صحيحة" in box["t"] and "لتُعتمد" in box["t"], "admin-returned form shows with 'ملاحظة المشرف' for an entity without a reviewer")
    t = ev(f"{SR}.querySelector('#app').innerText")
    ok("جميع استمارات جهتك مكتملة" not in t or box is None, "no misleading 'all complete' note while a returned form is waiting")
    out()

    # 3) reviewer and admin views are unaffected
    login("sara.rev", "sara123")
    ok(ev(BOX) is None, "reviewer does not get the coordinator's returned box")
    b.close()
print("PAGE ERRORS:", errors)
if errors: sys.exit(1)
print("ALL RETURNED-BOX TESTS PASSED")
