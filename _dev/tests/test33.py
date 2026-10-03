# home: «اعرف فرعك وجائزتك» two-question finder
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
def pick(pg,label):
    pg.evaluate("l=>[...document.querySelectorAll('.kf-ov .kf-g button')].find(b=>b.textContent===l).click()",label);pg.wait_for_timeout(150)
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw in [(390,844),(1280,800)]:
        pg=b.new_page(viewport={"width":vw[0],"height":vw[1]});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U);pg.wait_for_timeout(700);w=vw[0]
        ok(pg.is_visible(".kf"),f"{w}: button on home")
        pg.click(".kf");pg.wait_for_timeout(300)
        ok(pg.is_visible(".kf-ov .kf-sh"),f"{w}: panel opens")
        ok(pg.evaluate("document.querySelectorAll('.kf-ov .kf-g button').length")==8,f"{w}: 8 age choices")
        pick(pg,"11 إلى 14 سنة");ok(pg.evaluate("document.querySelectorAll('.kf-ov .kf-g button').length")==11,f"{w}: 11 juz choices")
        pick(pg,"10 أجزاء");t=pg.inner_text(".kf-ov .kf-res")
        ok("النشء والشباب (من 11 إلى ما دون 15)" in t and "1,000" in t and "800" in t,f"{w}: result 11-14 / 10 juz")
        ok("10%20%D8%A3%D8%AC%D8%B2%D8%A7%D8%A1" in pg.get_attribute(".kf-wa","href"),f"{w}: whatsapp text has the memorisation")
        pg.click(".kf-p");pg.wait_for_timeout(400)
        ok(pg.evaluate("document.querySelector('.kf-ov').hidden"),f"{w}: details closes the panel")
        ok(pg.evaluate("document.querySelector('.tb.active').dataset.v")=="1" and pg.evaluate("[...document.querySelectorAll('[role=tab]')].find(x=>x.getAttribute('aria-selected')==='true').textContent.includes('العامة')"),f"{w}: details opens the general branch tab")
        # under 6: no second question
        pg.evaluate("document.querySelector('.tb[data-v=\"0\"]').click()");pg.wait_for_timeout(200)
        pg.click(".kf");pg.wait_for_timeout(200);pick(pg,"أقل من 6 سنوات")
        ok("3 إلى ما دون 6" in pg.inner_text(".kf-ov .kf-res"),f"{w}: under 6 goes straight to result")
        pg.click(".kf-lk");pg.wait_for_timeout(150);pick(pg,"25 إلى 59 سنة");pick(pg,"القرآن كاملاً");pick(pg,"نعم")
        ok("فرع القراءات" in pg.inner_text(".kf-ov .kf-res"),f"{w}: whole Quran + qiraat")
        pg.keyboard.press("Escape");pg.wait_for_timeout(150)
        ok(pg.evaluate("document.querySelector('.kf-ov').hidden"),f"{w}: Escape closes")
        pg.click(".kf");pg.wait_for_timeout(200);pick(pg,"ذوو الاحتياجات وغيرها");pg.wait_for_timeout(1500)
        ok(pg.evaluate("document.querySelector('.tb.active').dataset.v")=="2" and "لمن المشاركة" in pg.inner_text("#aiLog"),f"{w}: special categories open the assistant guide")
        ok(not errs,f"{w}: no errors "+str(errs));pg.close()
    b.close()
print("FAILS:",fails)
