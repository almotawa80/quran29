# assistant answers about the permanent committee
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
CASES=[("من هم أعضاء اللجنة الدائمة؟","committee"),("مين رئيس اللجنة","committee"),("اللجنة الدائمة","committee"),("من يشرف على المسابقة","committee"),("نائب رئيس اللجنة","committee"),
       ("كيف أعترض على قرار لجنة التحكيم؟","objection"),("متى اللجان الصباحية؟","morning"),("موعد لجنة رياض الأطفال","morning")]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":844});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(700);pg.evaluate("document.querySelector('.tb[data-v=\"2\"]').click()")
    names=pg.evaluate("[...new Set([...document.querySelectorAll('.team .tm-card b')].map(x=>x.textContent))]")
    ok(len(names)==6,f"six members on the page {len(names)}")
    for q,kind in CASES:
        pg.fill("#aiIn",q);pg.evaluate("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(1100)
        t=pg.evaluate("[...document.querySelectorAll('#aiLog .ai-msg.bot')].pop().innerText")
        if kind=="committee":ok(all(n in t for n in names) and "رئيس اللجنة" in t,f"'{q}' lists the committee")
        elif kind=="objection":ok("بكتاب رسمي" in t,f"'{q}' still answers objections")
        else:ok("اللجان الصباحية" in t or "صباح" in t,f"'{q}' still answers morning committees")
    pg.fill("#aiIn","اللجنة الدائمة");pg.evaluate("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(1100)
    pg.evaluate("[...document.querySelectorAll('#aiLog .ai-act[data-act=committee]')].pop().click()");pg.wait_for_timeout(900)
    ok(pg.evaluate("(()=>{const p=[...document.querySelectorAll('.about-view .sub-pane')].find(x=>x.dataset.st==='اللجنة الدائمة');return !!p&&!p.hidden&&!!p.offsetParent})()"),"button opens the committee tab")
    ok(not errs,"no errors "+str(errs));b.close()
print("FAILS:",fails)
