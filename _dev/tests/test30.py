# assistant look: welcome, prize card, pills, identity, highlights, copy/share
from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
CR="""(sel)=>{const L=c=>{const m=c.match(/[\\d.]+/g).map(Number);const f=v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4};return [.2126*f(m[0])+.7152*f(m[1])+.0722*f(m[2]),m[3]==null?1:m[3]]};
 const bgOf=e=>{while(e){const c=getComputedStyle(e).backgroundColor;if(c&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c)&&!/, 0\\)$/.test(c))return c;e=e.parentElement}return 'rgb(255,255,255)'};
 const out=[];document.querySelectorAll(sel).forEach(e=>{if(!e.offsetParent)return;const a=L(getComputedStyle(e).color)[0],b=L(bgOf(e))[0];out.push(+((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2))});return out}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in ("light","dark"):
        ctx=b.new_context(viewport={"width":390,"height":844},color_scheme=th);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U);pg.wait_for_timeout(600);ev=pg.evaluate
        ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(400)
        ok(ev("!document.getElementById('aiWelcome').hidden && document.querySelectorAll('.aw-card').length===4"),th+": welcome screen with 4 cards")
        ok(ev("document.querySelectorAll('#aiLog .ai-msg').length")==0,th+": no greeting messages under the welcome")
        ok("svg" in ev("getComputedStyle(document.querySelector('.aw-logo')).backgroundImage"),th+": ornament logo shown")
        c=ev(CR,".aw-card b, .aw-card small, .ai-welcome p, .ai-welcome h3");ok(min(c)>=4.5,th+f": welcome text contrast {min(c)}")
        pg.click(".aw-card.pri");pg.wait_for_timeout(1000)
        ok(ev("document.getElementById('aiWelcome').hidden"),th+": welcome hides once the chat starts")
        ok(ev("getComputedStyle(document.querySelector('#aiLog .ai-opt')).borderRadius").startswith("9"),th+": choices are pills")
        ok("svg" in ev("getComputedStyle(document.querySelector('#aiLog .ai-msg.bot'),'::before').backgroundImage"),th+": bot avatar is the ornament")
        c=ev(CR,"#aiLog .ai-opt");ok(min(c)>=4.5,th+f": pill contrast {min(c)}")
        def ask(q):pg.fill("#aiIn",q);ev("document.getElementById('aiForm').requestSubmit()")
        ask("عمري 12 وأحفظ 7 أجزاء");pg.wait_for_timeout(1300)
        ok(ev("!!document.querySelector('#aiLog .pz .pz-amt strong')"),th+": prize card shown")
        ok(ev("document.querySelector('#aiLog .pz .pz-amt strong').textContent")=="800",th+": first prize 800")
        m=ev("[...document.querySelectorAll('#aiLog .pz .pz-med b')].map(x=>x.textContent)");ok(len(m)==2 and "700" in m[0] and "600" in m[1],th+f": medals {m}")
        c=ev(CR,"#aiLog .pz-h span, #aiLog .pz-t, #aiLog .pz-amt strong, #aiLog .pz-amt small, #aiLog .pz-med b, #aiLog .pz-med small");ok(min(c)>=4.5,th+f": prize card contrast {min(c)}")
        ok(ev("!!document.querySelector('#aiLog .ai-act[data-act=share] svg')"),th+": copy icon button")
        h=ev("document.querySelector('#aiLog a.ai-act.wa').href");ok(h.startswith("https://wa.me/?text=") and "800" not in h or "%" in h,th+": whatsapp share link")
        c=ev(CR,"#aiLog .ai-act");ok(min(c)>=4.5,th+f": action contrast {min(c)}")
        ask("متى آخر يوم للتسجيل؟");pg.wait_for_timeout(1300)
        hl=ev("[...document.querySelectorAll('#aiLog .ai-hl')].map(x=>x.textContent)");ok(any("أكتوبر" in x for x in hl),th+f": dates highlighted {hl[:3]}")
        c=ev(CR,"#aiLog .ai-hl");ok(min(c)>=4.5,th+f": highlight contrast {min(c)}")
        ok(ev("!document.querySelector('#aiLog .ai-msg a .ai-hl, #aiLog .ai-time .ai-hl')"),th+": no highlight inside links or times")
        pg.reload();pg.wait_for_timeout(700)
        if not ev("document.documentElement.classList.contains('view-find')"):ev("document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
        ok(ev("document.getElementById('aiWelcome').hidden"),th+": welcome stays hidden after reload of an ongoing chat")
        ok(not errs,th+": no errors "+str(errs));ctx.close()
    # reduced motion: no entrance animation
    ctx=b.new_context(viewport={"width":390,"height":844},reduced_motion="reduce");pg=ctx.new_page();pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(500);pg.evaluate("document.querySelector('.tb[data-v=\"2\"]').click()");pg.click(".aw-card >> nth=1");pg.wait_for_timeout(250)
    ok(pg.evaluate("[...document.querySelectorAll('#aiLog .ai-row')].every(r=>getComputedStyle(r).animationName==='none')"),"reduced motion: no entrance animation");ctx.close()
    # large font
    ctx=b.new_context(viewport={"width":360,"height":740});pg=ctx.new_page();pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(500);pg.evaluate("document.documentElement.style.fontSize='130%';document.querySelector('.tb[data-v=\"2\"]').click()");pg.wait_for_timeout(300)
    ok(pg.evaluate("[...document.querySelectorAll('.aw-card')].every(c=>c.scrollWidth<=c.clientWidth+1) && document.documentElement.scrollWidth<=innerWidth"),"large font: welcome cards fit");ctx.close()
    b.close()
print("FAILS:",fails)
