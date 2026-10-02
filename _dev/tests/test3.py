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

        # --- reviewer: open a pending candidate's documents from "بانتظار مراجعتك" ---
        login("sara.rev", "sara123")
        has_prev_in_reviewbox = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            return !!root.querySelector('[data-prev]');
        }""")
        assert has_prev_in_reviewbox, "reviewer's pending-review box missing preview/document link"
        print("reviewer has preview link in pending-review box OK")

        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-prev]').click()")
        page.wait_for_timeout(200)
        has_docsec = page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            return root.querySelector('#app').innerText.includes('المستندات والإقرار');
        }""")
        assert has_docsec, "preview page missing documents section"
        print("reviewer can open candidate preview with documents OK")

        # click a zoom trigger if present (candidate may or may not have an image doc)
        has_zoom_btn = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-zoom]')")
        if has_zoom_btn:
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-zoom]').click()")
            page.wait_for_timeout(200)
            ov_visible = page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                const ov = root.querySelector('#docZoom');
                return ov && !ov.hidden;
            }""")
            assert ov_visible, "document zoom overlay did not open"
            print("document zoom overlay opens OK")
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-zx]').click()")
            page.wait_for_timeout(150)
            ov_hidden = page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                const ov = root.querySelector('#docZoom');
                return ov && ov.hidden;
            }""")
            assert ov_hidden, "document zoom overlay did not close"
            print("document zoom overlay closes OK")
        else:
            print("no zoom-able doc on this candidate (ok, no image attached)")

        page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#abOut').click()")
        page.wait_for_timeout(300)

        # --- admin: can only preview APPROVED candidates' documents (المرشحون tab) ---
        login("admin", "admin123")
        page.evaluate("""() => {
            const root = document.querySelector('.pt-host').shadowRoot;
            [...root.querySelectorAll('[data-at]')].find(b=>b.textContent.includes('المرشحون')).click();
        }""")
        page.wait_for_timeout(200)
        cand_txt = page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#app').innerText")
        assert "مسودة" not in cand_txt and "بانتظار المراجعة" not in cand_txt, "admin candidates tab leaking non-approved statuses"
        has_cprev = page.evaluate("!!document.querySelector('.pt-host').shadowRoot.querySelector('[data-cprev]')")
        if has_cprev:
            page.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('[data-cprev]').click()")
            page.wait_for_timeout(200)
            has_docsec2 = page.evaluate("""() => {
                const root = document.querySelector('.pt-host').shadowRoot;
                return root.querySelector('#app').innerText.includes('المستندات والإقرار');
            }""")
            assert has_docsec2, "admin preview missing documents section"
            print("admin can open an APPROVED candidate's documents OK")
        else:
            print("no approved candidates listed for admin to preview (ok)")

        b.close()
    if errors:
        print("PAGE ERRORS:", errors)
        sys.exit(1)
    print("ALL DOC-VIEWER TESTS PASSED")

run()
