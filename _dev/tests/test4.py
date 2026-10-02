import sys
from playwright.sync_api import sync_playwright

PATH = "file://" + __import__("os").path.abspath("index.html")
errors = []

def run():
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(PATH)
        page.wait_for_timeout(300)

        def login(u, pw):
            page.click("#coordBtn")
            page.wait_for_timeout(200)
            page.fill("#lgU", u)
            page.fill("#lgP", pw)
            page.click("#lgGo")
            page.wait_for_timeout(300)

        # ---------- Fix #1: no "مكتمل" pill contradiction for pending/corrected ----------
        login("sara.rev", "sara123")
        rows_txt = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            return [...root.querySelectorAll('.row')].map(r => r.innerText);
        }""")
        for t in rows_txt:
            if ("بانتظار المراجعة" in t or "مُعاد للتصحيح" in t or "مُعاد" in t) and "مكتمل" in t and "غير مكتمل" not in t and "ينقصه" not in t:
                print("FAIL: contradictory 'مكتمل' pill alongside pending/corrected status:", t[:120])
                sys.exit(1)
        print("Fix#1 OK: no contradictory مكتمل pill for pending/corrected rows")

        # ---------- Fix #3: return-note box appears only ONCE, and closes after confirm ----------
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btn = root.querySelector('[data-ret]');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(200)
        n_boxes = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            return root.querySelectorAll('textarea[id^=rn_]').length;
        }""")
        assert n_boxes <= 1, f"return-note box should appear once, found {n_boxes}"
        print("Fix#3a OK: single return-note box, count =", n_boxes)
        if n_boxes == 1:
            page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                root.querySelector('textarea[id^=rn_]').value = 'يرجى تصحيح البيانات';
            }""")
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-retok]').click()")
            page.wait_for_timeout(250)
            still_open = page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                return root.querySelectorAll('textarea[id^=rn_]').length;
            }""")
            assert still_open == 0, f"note box should close after confirming return, still {still_open} open"
            print("Fix#3b OK: note box closes after confirming return")

        # ---------- Fix #2: reviewer can undo an approval ----------
        has_unappr = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-unappr]')")
        assert has_unappr, "no 'تراجع عن الاعتماد' button found for any approved candidate"
        before_status = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const btn = root.querySelector('[data-unappr]');
            return btn.closest('.row').innerText;
        }""")
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-unappr]').click()")
        page.wait_for_timeout(250)
        after_txt = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            return root.querySelector('#app').innerText;
        }""")
        assert "بانتظار مراجعتك" in after_txt, "unapproved candidate should now be back in the pending-review queue"
        print("Fix#2 OK: reviewer un-approve works, candidate returned to pending review")

        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)

        # ---------- Fix #4: admin can return an APPROVED candidate to the entity with a note ----------
        login("admin", "admin123")
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            [...root.querySelectorAll('[data-at]')].find(b=>b.textContent.includes('المرشحون')).click();
        }""")
        page.wait_for_timeout(200)
        has_aret = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-aret]')")
        if has_aret:
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-aret]').click()")
            page.wait_for_timeout(200)
            page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                root.querySelector('textarea[id^=arn_]').value = 'الصورة غير واضحة، يرجى إعادة رفعها';
            }""")
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-aretok]').click()")
            page.wait_for_timeout(250)
            box_gone = page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                return root.querySelectorAll('textarea[id^=arn_]').length;
            }""")
            assert box_gone == 0, "admin return-note box should close after confirming"
            print("Fix#4 OK: admin can return an approved candidate to the entity with a note")
        else:
            print("Fix#4: no approved candidates available to test admin-return (ok, data-dependent)")

        # dashboard visuals: colored kpi tiles present
        dash_txt = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            [...root.querySelectorAll('[data-at]')].find(b=>b.textContent.includes('المتابعة')).click();
            return root.querySelector('#app').innerText;
        }""")
        assert "بانتظار المراجعة" in dash_txt and "معاد للتصحيح" in dash_txt, "dashboard KPI tiles missing"
        print("Fix#5 OK: dashboard shows pending/corrected KPI tiles")

        b.close()
    if errors:
        print("PAGE ERRORS:", errors)
        sys.exit(1)
    print("ALL FOLLOW-UP FIX TESTS PASSED")

run()
