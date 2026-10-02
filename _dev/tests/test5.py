import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath("index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors = []
def app_text(page): return page.evaluate(f"{SR}.querySelector('#app').innerText")
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(viewport={"width":900,"height":1000})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PATH); page.wait_for_timeout(300)
    def login(u, pw):
        page.click("#coordBtn"); page.wait_for_timeout(200)
        page.fill("#lgU", u); page.fill("#lgP", pw); page.click("#lgGo"); page.wait_for_timeout(400)
    def logout():
        page.evaluate(f"{SR}.querySelector('#abOut').click()"); page.wait_for_timeout(300)

    # 1) admin baseline: every approved candidate is complete (no "ينقصه" anywhere in المرشحون)
    login("admin", "admin123")
    page.evaluate(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المرشحون').click()"); page.wait_for_timeout(300)
    t = app_text(page)
    assert "ينقصه" not in t, "admin sees an approved candidate with missing items"
    assert "غير مكتملة" not in t, "incomplete tile/filter should be gone from المرشحون"
    base = page.evaluate(f"{SR}.querySelectorAll('[data-cprev]').length")
    print("admin approved count:", base)
    logout()

    # 2) entity without reviewer (furqan): remove the civil-ID attachment from its approved candidate and save
    login("furqan", "furqan123")
    page.evaluate(f"()=>[...{SR}.querySelectorAll('.row')].find(r=>r.innerText.includes('علي حسين الصفار')).querySelector('[data-edit]').click()"); page.wait_for_timeout(300)
    hint = app_text(page)
    assert "إلا بعد اكتمالها" in hint, "save hint missing"
    page.evaluate(f"{SR}.querySelector('[data-rm]').click()"); page.wait_for_timeout(300)
    page.evaluate(f"{SR}.querySelector('#cf button[type=submit]').click()"); page.wait_for_timeout(400)
    t = app_text(page)
    assert "مسودة" in t, "incomplete candidate should be saved as draft"
    print("entity: incomplete save -> draft OK")
    logout()

    # 3) admin no longer sees him; المتابعة shows the draft
    login("admin", "admin123")
    page.evaluate(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المرشحون').click()"); page.wait_for_timeout(300)
    after = page.evaluate(f"{SR}.querySelectorAll('[data-cprev]').length")
    assert after == base - 1, f"admin approved count should drop by 1 ({base} -> {after})"
    page.evaluate(f"()=>[...{SR}.querySelectorAll('[data-at]')].find(b=>b.textContent.trim()==='المتابعة').click()"); page.wait_for_timeout(300)
    t = app_text(page)
    assert "مسودة غير مكتملة" in t and "نسبة الاعتماد" in t and "مسودات" in t, "tracking tiles/columns missing"
    page.screenshot(path="s18_track.png")
    print("admin: draft excluded from approved, tracking shows drafts OK")
    b.close()
print("PAGE ERRORS:", errors)
if errors: sys.exit(1)
print("ALL COMPLETENESS-RULE TESTS PASSED")
