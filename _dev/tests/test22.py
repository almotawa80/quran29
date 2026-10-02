from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    def sess(ctx):
        pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U,wait_until="domcontentloaded");pg.wait_for_timeout(400);return pg,errs
    # A: dismiss
    ctx=b.new_context(viewport={"width":390,"height":844});pg,errs=sess(ctx)
    ok(pg.is_visible(".qz-promo .qz-gcard"),"promo shown on first visit")
    bb=pg.eval_on_selector(".qz-pclose","e=>{const r=e.getBoundingClientRect();return [r.width,r.height]}");ok(bb[0]>=44 and bb[1]>=44,"close button is 44px")
    pg.click(".qz-pclose");pg.wait_for_timeout(200)
    ok(pg.query_selector(".qz-promo") is None,"promo hidden after ×")
    ok(pg.is_visible(".game-chip"),"header game button still available")
    pg.close();pg,errs=sess(ctx);ok(pg.query_selector(".qz-promo") is None,"stays hidden on next visit")
    ok(not errs,"no errors "+str(errs))
    # B: shows only 3 sessions
    ctx=b.new_context(viewport={"width":390,"height":844});seen=[]
    for i in range(5):
        pg,errs=sess(ctx);seen.append(pg.query_selector(".qz-promo") is not None);pg.close()
    ok(seen==[True,True,True,False,False],"shown for first 3 visits only "+str(seen))
    # C: opening the game hides it next time; reload in same session keeps counting once
    ctx=b.new_context(viewport={"width":390,"height":844});pg,errs=sess(ctx)
    pg.reload(wait_until="domcontentloaded");pg.wait_for_timeout(300);ok(pg.query_selector(".qz-promo") is not None,"reload in same session still shows it")
    pg.click(".qz-promo .qz-gcard");pg.wait_for_timeout(400);ok(pg.is_visible(".qz-dlg"),"card still opens the game")
    pg.close();pg,errs=sess(ctx);ok(pg.query_selector(".qz-promo") is None,"hidden next visit after opening the game")
print("FAILS",fails)
