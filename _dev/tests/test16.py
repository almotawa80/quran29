import sys, os
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
errors=[]
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":844},has_touch=True,is_mobile=True);pg=ctx.new_page()
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.on("pageerror",lambda e:errors.append(str(e)))
    pg.add_init_script("window.__shared=null;navigator.canShare=()=>true;navigator.share=async(d)=>{window.__shared=d};")
    pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(500);ev=pg.evaluate
    ok(ev("!!document.querySelector('.game-chip')")and ev("!!document.querySelector('.qz-gcard')"),"chip + home card exist")
    pg.click(".game-chip");pg.wait_for_timeout(400)
    ok(ev("!document.querySelector('.qz-dlg').hidden"),"game dialog opens")
    ok(ev("document.querySelectorAll('.qz-j').length")==30,"30 juz chips")
    ok(ev("document.querySelector('.qz-j[aria-pressed=true]').dataset.j")=="30","default juz 30 (amma)")
    pg.click("[data-pre=clear]");ok(ev("document.querySelector('.qz-go').disabled"),"start disabled with no juz")
    pg.click("[data-j='29']");pg.click("[data-j='30']");pg.click("[data-lv=easy]");pg.click("[data-n='5']")
    ok(ev("[...document.querySelectorAll('.qz-j[aria-pressed=true]')].map(x=>x.dataset.j).join()")=="29,30","two juz selected")
    pg.click("[data-a=start]");pg.wait_for_selector(".qz-o",timeout=15000)
    st=lambda:ev("(()=>{const r=window.Q29Game._t.state();return {i:r.i,score:r.score,ok:r.ok,streak:r.streak,n:r.qs.length,ans:r.qs[r.i].ans,lv:r.qs[r.i].lv}})()")
    s0=st();ok(s0["n"]==5 and s0["lv"]=="easy","5 easy questions")
    ok(ev("document.querySelectorAll('.qz-o').length")==4,"4 choices")
    # q1: use hint then answer right -> half points
    pg.click("[data-a=hint]");ok(ev("document.querySelectorAll('.qz-o.gone').length")==2,"hint removes 2 wrong choices")
    ok(ev("document.querySelector('.qz-hint span').textContent")=="٢","hint counter decremented")
    pg.click(f"[data-o='{s0['ans']}']");pg.wait_for_timeout(200)
    ok(ev("!!document.querySelector('.qz-fb.g')"),"correct feedback")
    ok(st()["score"]==5,"hint halves points (10 -> 5)")
    ok(ev("document.querySelectorAll('.qz-o.ok').length")==1,"correct option highlighted")
    pg.click("#qzNext");pg.wait_for_timeout(200)
    tot=5
    for k in range(2,6):
        s=st();ok(s["i"]==k-1,f"question {k}")
        pg.click(f"[data-o='{s['ans']}']");pg.wait_for_timeout(150)
        tot+=[10,10,15,15][k-2]  # streak: q2 streak1->x1 ; q3 x1(streak2) ; q4 streak3 ->1.5 ; q5 ->1.5
        if k<5:pg.click("#qzNext");pg.wait_for_timeout(150)
    print("expected",tot,"got",st()["score"])
    ok(st()["score"]==tot,"score with streak multiplier")
    pg.click("#qzNext");pg.wait_for_timeout(500)
    ok("حافظ متقن" in ev("document.querySelector('.qz-badge').innerText"),"100% badge")
    ok("5/5" in ev("document.querySelector('.qz-ring').innerText").replace("٥","5"),"5/5 shown")
    ok(ev("!!document.querySelector('.qz-rv')")==False,"no mistakes list")
    pg.click("[data-a=share]");pg.wait_for_timeout(500)
    ok(ev("!document.querySelector('.sh-dlg').hidden")and ev("document.querySelector('#shModes').hidden"),"share dialog opens in quiz mode (modes hidden)")
    ok(ev("document.querySelector('#shTitle').textContent")=="شارك نتيجتك","share title")
    pg.fill("#shName","خالد");pg.wait_for_timeout(300)
    pg.screenshot(path="/tmp/g_share.png")
    pg.click("#shShare");pg.wait_for_timeout(600);sh=ev("window.__shared");ok(sh and "اختبر حفظي" in sh["text"] and "5 من 5" in sh["text"],"share text has result")
    pg.click("#shX");pg.wait_for_timeout(200)
    # second run: all wrong
    pg.click("[data-a=setup]");pg.click("[data-lv=hard]");pg.click("[data-a=start]");pg.wait_for_selector(".qz-o",timeout=15000)
    for k in range(5):
        s=st();wrong=(s["ans"]+1)%4
        pg.click(f"[data-o='{wrong}']");pg.wait_for_timeout(120)
        ok(ev("!!document.querySelector('.qz-o.no')"),"wrong marked")
        pg.click("#qzNext");pg.wait_for_timeout(120)
    ok(ev("document.querySelectorAll('.qz-rv details').length")==5,"5 mistakes listed for review")
    pg.click(".qz-rv summary");ok(ev("document.querySelector('.qz-rv details').open"),"review item opens")
    pg.screenshot(path="/tmp/g_res.png")
    # exit flow
    pg.click("[data-a=again]");pg.wait_for_selector(".qz-o");pg.click("[data-a=exit]");ok(ev("!!document.querySelector('.qz-conf')"),"exit confirmation")
    pg.click("[data-a=no]");ok(ev("!document.querySelector('.qz-conf')"),"continue")
    pg.keyboard.press("1");pg.wait_for_timeout(200);ok(ev("!!document.querySelector('.qz-fb')"),"keyboard 1 answers")
    pg.keyboard.press("Escape");pg.wait_for_timeout(200);ok(ev("!!document.querySelector('.qz-conf')"),"Esc asks to exit while in quiz")
    pg.click("[data-a=yes]");pg.wait_for_timeout(300);ok(ev("!!document.querySelector('.qz-res')"),"early exit shows result")
    pg.click("[data-a=close]");ok(ev("document.querySelector('.qz-dlg').hidden"),"closes")
    ok(ev("document.documentElement.style.overflow")=="","scroll restored")
    # persistence
    pg.reload(wait_until="domcontentloaded");pg.wait_for_timeout(400);pg.click(".game-chip");pg.wait_for_timeout(300)
    ok(ev("document.querySelector('[data-lv][aria-checked=true]').dataset.lv")=="hard","level persisted")
    # timer variant
    pg.click("[data-lv=easy]");pg.check("#qzTm");pg.click("[data-a=start]");pg.wait_for_selector(".qz-o");ok(ev("!!document.querySelector('#qzT')"),"timer bar shown")
    pg.click("[data-a=exit]");pg.click("[data-a=yes]")
    print("PAGE ERRORS:",errors);ok(not errors,"no page errors")
