import json,os
from playwright.sync_api import sync_playwright
F="http://localhost:8765/gh.html"
calls=[];fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={"width":390,"height":844},user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",has_touch=True,is_mobile=True)
    ctx.add_init_script('window.Q29_DB={url:"https://x.test",key:"k"}')
    pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    def route(r):
        u=r.request.url
        if "x.test/rest/v1/rpc/" in u:
            calls.append((u.split("/rpc/")[1],r.request.post_data));return r.fulfill(status=200,body="null",headers={"content-type":"application/json"})
        if u.startswith("http") and "localhost" not in u:return r.abort()
        r.continue_()
    pg.route("**/*",route)
    pg.goto(F,wait_until="domcontentloaded");pg.wait_for_timeout(2500)
    tr=[json.loads(d)["items"] for n,d in calls if n=="q29_track"]
    flat=[(i["k"],i["v"]) for t in tr for i in t]
    print(flat)
    ok(any(n=="q29_hit" for n,_ in calls),"old counter still fires")
    ok(("device","mobile") in flat and ("os","ios") in flat and ("browser","safari") in flat,"device/os/browser")
    ok(("src","direct") in flat and ("ret","new") in flat and any(k=="hour" for k,_ in flat),"src direct / new / hour")
    ok(("sec","home") in flat,"home section")
    # tab clicks
    for v in (1,2,3):
        pg.click(f'.tb[data-v="{v}"]');pg.wait_for_timeout(200)
    pg.click(f'.tb[data-v="2"]');pg.wait_for_timeout(200)
    pg.wait_for_timeout(1800)
    flat=[(i["k"],i["v"]) for n,d in calls if n=="q29_track" for i in json.loads(d)["items"]]
    ok(("sec","branches") in flat and ("sec","ai") in flat and ("sec","shields") in flat,"tab sections")
    ok(sum(1 for x in flat if x==("sec","ai"))==1,"section counted once per session")
    # assistant question
    pg.click('.tb[data-v="2"]');pg.wait_for_timeout(300)
    inp=pg.query_selector('.nl-in input, .nl-in textarea, #nlQ, input[type=search]')
    print("assistant input", bool(inp))
    n0=len(calls)
    pg.evaluate("Q29T.ask('كم قيمة الجائزة للفرع العام؟')");pg.evaluate("Q29T.ask('12')");pg.evaluate("Q29T.ask('متى آخر موعد للتسجيل')")
    pg.wait_for_timeout(1800)
    ask=[i["v"] for n,d in calls[n0:] if n=="q29_track" for i in json.loads(d)["items"] if i["k"]=="ask"]
    print(ask);ok(ask==["prizes","dates"] or ask==["prizes","register"] ,"ask topics (numeric ignored)")
    # topic classifier
    T=pg.evaluate("['ما هي شروط المشاركة؟','كيف اتواصل معكم','ما هو درع الجهات','هل يحق لي المشاركة وأنا مقيم','ما فروع المسابقة','مرحبا','أين تقام التصفيات'].map(Q29T._t)")
    print(T);ok(T==["rules","contact","shields","rules","branches","other","dates"],"classifier")
    # game
    pg.evaluate("document.querySelector('.game-chip').click()");pg.wait_for_timeout(400)
    ok("game_start" not in str(calls),"no game_start before start")
    ok(not errs,"no page errors "+str(errs))
    # payload has no free text
    body=" ".join(d for n,d in calls if n=="q29_track")
    ok("الجائزة" not in body and "التسجيل" not in body,"no typed text in payload")
    # second load same day: no new visit
    n1=len([1 for n,_ in calls if n=="q29_hit"])
    pg.reload(wait_until="domcontentloaded");pg.wait_for_timeout(2200)
    ok(len([1 for n,_ in calls if n=="q29_hit"])==n1,"no second visit same day")
    pg2=ctx.new_page();pg2.route("**/*",route);pg2.goto(F+"?src=whatsapp",wait_until="domcontentloaded");pg2.wait_for_timeout(1500)
    print("done")
print("FAILS",fails)
