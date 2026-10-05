# welcome screen: first visit only, not for direct links or automated browsers
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
HUMAN="Object.defineProperty(Navigator.prototype,'webdriver',{get:()=>false})"
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw in [(390,844),(1280,800)]:
        ctx=b.new_context(viewport={"width":vw[0],"height":vw[1]});ctx.add_init_script(HUMAN);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        w=vw[0];pg.goto(U);pg.wait_for_timeout(900)
        ok(pg.is_visible(".wl"),f"{w}: welcome on first visit")
        ok("مسابقة الكويت الكبرى" in pg.inner_text(".wl") and "29" in pg.inner_text(".wl"),f"{w}: welcome content")
        ok(pg.evaluate("document.activeElement.classList.contains('wl-go')"),f"{w}: focus on the enter button")
        pg.click(".wl-go");pg.wait_for_timeout(500)
        ok(pg.evaluate("!document.querySelector('.wl')") and pg.evaluate("document.documentElement.style.overflow")=="",f"{w}: enter closes and unlocks scroll")
        pg.reload();pg.wait_for_timeout(900)
        ok(pg.evaluate("!document.querySelector('.wl')"),f"{w}: not shown again")
        ok(not errs,f"{w}: no errors "+str(errs));ctx.close()
    # Escape, direct links, automated browser
    ctx=b.new_context();ctx.add_init_script(HUMAN);pg=ctx.new_page();pg.goto(U);pg.wait_for_timeout(900);pg.keyboard.press("Escape");pg.wait_for_timeout(500)
    ok(pg.evaluate("!document.querySelector('.wl')"),"Escape closes");ctx.close()
    for q in ["?src=quiz","#branches"]:
        ctx=b.new_context();ctx.add_init_script(HUMAN);pg=ctx.new_page();pg.goto(U+q);pg.wait_for_timeout(900)
        ok(pg.evaluate("!document.querySelector('.wl')"),f"direct link {q}: no welcome");ctx.close()
    pg=b.new_page();pg.goto(U);pg.wait_for_timeout(900);ok(pg.evaluate("!document.querySelector('.wl')"),"automated browser: no welcome")
    b.close()
print("FAILS:",fails)
