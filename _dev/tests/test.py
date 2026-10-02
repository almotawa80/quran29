import sys, time
from playwright.sync_api import sync_playwright

PATH = "file://" + __import__("os").path.abspath("index.html")

def log(msg):
    print("== " + msg)

errors = []

def run():
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(PATH)
        page.wait_for_timeout(300)

        # open portal
        page.click("#coordBtn")
        page.wait_for_timeout(200)

        def portal():
            return page.locator(".pt-host")

        def login(u, pw):
            page.fill("#lgU", u)
            page.fill("#lgP", pw)
            page.click("#lgGo")
            page.wait_for_timeout(300)

        # --- SCENARIO 1: entry with reviewer (huda) ---
        log("Login as huda (entry, has reviewer)")
        login("huda", "huda123")
        host = page.locator(".pt-host")
        assert host.count() == 1, "portal did not open for huda"
        txt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "بانتظار المراجعة" in txt or "مسودة" in txt, "status labels not visible in huda list"
        log("huda list OK, contains status labels")

        # open an existing candidate that's status=corrected to see reviewer note
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btns = [...root.querySelectorAll('[data-edit]')];
            const target = btns.find(b => b.closest('.row') && b.closest('.row').innerText.includes('عبدالله يوسف الكندري'));
            if (target) target.click();
        }""")
        page.wait_for_timeout(200)
        formtxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "ملاحظة المراجع" in formtxt, "corrected candidate should show reviewer note"
        log("corrected candidate shows reviewer note banner OK")
        # check save button label (has reviewer -> should say send for review)
        btntxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#cf button[type=submit]').textContent")
        assert "إرسال للمراجعة" in btntxt, f"expected submit-for-review label, got {btntxt}"
        log("save button label correct for entity with reviewer: " + btntxt)
        # cancel back
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#cancel').click()")
        page.wait_for_timeout(200)

        # logout
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)

        # --- SCENARIO 2: reviewer login (sara.rev) ---
        log("Login as sara.rev (reviewer for huda's entity)")
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        login("sara.rev", "sara123")
        txt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "بانتظار مراجعتك" in txt, "reviewer should see 'بانتظار مراجعتك' box"
        assert "مراجع" in page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('.ab-right').innerText"), "role chip missing for reviewer"
        log("reviewer sees pending review box + role chip OK")

        # approve one pending candidate
        approved_before = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btn = root.querySelector('[data-appr]');
            return !!btn;
        }""")
        assert approved_before, "no approve button found for reviewer"
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-appr]').click()")
        page.wait_for_timeout(300)
        log("reviewer approve action executed OK")

        # return with note flow
        has_ret = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-ret]')")
        if has_ret:
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-ret]').click()")
            page.wait_for_timeout(200)
            page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                const ta = root.querySelector('textarea[id^=rn_]');
                ta.value = 'يرجى تصحيح رقم الهاتف';
            }""")
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-retok]').click()")
            page.wait_for_timeout(300)
            log("reviewer return-with-note flow executed OK")
        else:
            log("no more pending candidates to test return flow (ok)")

        # reviewer should NOT have an edit button anywhere
        has_edit = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-edit]')")
        assert not has_edit, "reviewer must not have edit access to candidate data"
        log("confirmed reviewer has no edit buttons")

        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)

        # --- SCENARIO 3: entry without reviewer (furqan) ---
        log("Login as furqan (entry, NO reviewer)")
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        login("furqan", "furqan123")
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#add').click()")
        page.wait_for_timeout(200)
        btntxt2 = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#cf button[type=submit]').textContent")
        assert "اعتماد" in btntxt2 and "إرسال" not in btntxt2, f"expected self-approve label, got {btntxt2}"
        log("save button label correct for entity WITHOUT reviewer: " + btntxt2)
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#cancel').click()")
        page.wait_for_timeout(200)
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)

        # --- SCENARIO 4: admin ---
        log("Login as admin")
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        login("admin", "admin123")
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            [...root.querySelectorAll('[data-at]')].find(b=>b.textContent.includes('المتابعة')).click();
        }""")
        page.wait_for_timeout(200)
        atxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "بانتظار المراجعة" in atxt and "معاد للتصحيح" in atxt, "admin dashboard missing pending/corrected columns"
        log("admin dashboard shows pending/corrected counts OK")
        # go to entities tab, check reviewer chip
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btn = [...root.querySelectorAll('[data-at]')].find(b => b.textContent.includes('الجهات'));
            btn.click();
        }""")
        page.wait_for_timeout(200)
        etxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "له مراجع" in etxt and "بلا مراجع" in etxt, "entities tab missing reviewer indicator"
        log("entities tab shows reviewer indicator OK")

        # candidates tab should only show approved
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btn = [...root.querySelectorAll('[data-at]')].find(b => b.textContent.includes('المرشحون'));
            btn.click();
        }""")
        page.wait_for_timeout(200)
        ctxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "مسودة" not in ctxt, "admin candidates tab should not show draft-status labels/rows text leaking"
        log("admin candidates tab OK (approved-only view)")

        # --- SCENARIO 5: date simulation (3 dates) ---
        log("Testing date simulation")
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        login("admin", "admin123")
        page.evaluate("""() => {
            const sel = document.querySelector('.pt-host').shadowRoot.querySelector('#simDate');
            sel.value = '2026-11-05';
            sel.dispatchEvent(new Event('change'));
        }""")
        page.wait_for_timeout(200)
        page.evaluate("""() => {
            const sel = document.querySelector('.pt-host').shadowRoot.querySelector('#simDate');
            sel.value = '2026-11-14';
            sel.dispatchEvent(new Event('change'));
        }""")
        page.wait_for_timeout(200)
        log("date simulation changes did not error")

        b.close()

    if errors:
        print("CONSOLE/PAGE ERRORS:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("ALL TESTS PASSED")

run()
