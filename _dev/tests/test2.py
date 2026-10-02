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
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        page.fill("#lgU", "huda")
        page.fill("#lgP", "huda123")
        page.click("#lgGo")
        page.wait_for_timeout(300)

        # WA button only for approved candidates
        res = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            const rows = [...root.querySelectorAll('.list > .row')];
            return rows.map(r => ({
                text: r.querySelector('.nm').textContent,
                hasWA: !!r.querySelector('a.btn.wa'),
                status: r.querySelector('.acts').textContent
            }));
        }""")
        for r in res:
            approved = "معتمد" in r["status"] and "مسودة" not in r["status"] and "بانتظار" not in r["status"] and "تصحيح" not in r["status"]
            if r["hasWA"] and not approved:
                print("FAIL: WA button shown for non-approved candidate:", r)
                sys.exit(1)
        print("WA-button-only-for-approved check OK")

        # logout, go to admin, open entity form, verify reviewer section present, save with reviewer data
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)
        page.click("#coordBtn")
        page.wait_for_timeout(200)
        page.fill("#lgU", "admin")
        page.fill("#lgP", "admin123")
        page.click("#lgGo")
        page.wait_for_timeout(300)
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            [...root.querySelectorAll('[data-at]')].find(b=>b.textContent.includes('الجهات')).click();
        }""")
        page.wait_for_timeout(200)
        # add new entity
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#addEnt').click()")
        page.wait_for_timeout(200)
        has_rev_fields = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('#rvn')")
        assert has_rev_fields, "reviewer fields missing in entity form"
        print("Entity form has reviewer fields OK")

        # fill required fields + reviewer fields and submit
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            root.querySelector('#en').value='جهة اختبار تجريبية';
            root.querySelector('#ec').value='أ. تجربة الاختبار';
            root.querySelector('#ep').value='55599911';
            root.querySelector('#eu').value='test.entry1';
            root.querySelector('#rvn').value='أ. مراجع الاختبار';
            root.querySelector('#rvp').value='66688822';
            root.querySelector('#rvu').value='test.rev1';
        }""")
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#rgen').click()")
        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#ef').requestSubmit()")
        page.wait_for_timeout(300)
        etxt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "جهة اختبار تجريبية" in etxt, "new entity not listed after save"
        assert "test.rev1" in etxt, "reviewer username not shown after save"
        print("New entity with reviewer saved and listed OK")

        b.close()
    if errors:
        print("PAGE ERRORS:", errors)
        sys.exit(1)
    print("ALL EXTRA TESTS PASSED")

run()
