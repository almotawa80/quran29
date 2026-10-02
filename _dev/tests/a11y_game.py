import os,sys
from playwright.sync_api import sync_playwright
sys.argv=[sys.argv[0]]
src=open('a11y.py').read();JS=src[src.index('JS=r"""')+7:src.index('"""\nwith')]
P="file://"+os.path.abspath("index.html")
with sync_playwright() as p:
    b=p.chromium.launch()
    for scheme in ("light","dark"):
        c=b.new_context(viewport={"width":390,"height":844},color_scheme=scheme);pg=c.new_page();pg.set_default_timeout(4000)
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_())
        pg.goto(P,wait_until="domcontentloaded");pg.wait_for_timeout(400);res=[]
        def scan(l):
            for x in pg.evaluate(JS,"DOC"):
                if x['ex'] and ('qz' in x['ex'] or 'sh-' in x['ex'] or 'game' in x['ex'] or l!='home'):res.append((l,x))
        scan("home");pg.click(".game-chip");pg.wait_for_timeout(300);scan("setup")
        pg.click("[data-lv=medium]");pg.click("[data-a=start]");pg.wait_for_selector(".qz-o",timeout=15000);scan("quiz")
        a=pg.evaluate("window.Q29Game._t.state().qs[0].ans");pg.click(f"[data-o='{(a+1)%4}']");pg.wait_for_timeout(200);scan("wrong")
        pg.click("#qzNext");a=pg.evaluate("window.Q29Game._t.state().qs[1].ans");pg.click(f"[data-o='{a}']");pg.wait_for_timeout(200);scan("right")
        pg.click("[data-a=exit]");pg.click("[data-a=yes]");pg.wait_for_timeout(300);scan("result")
        print("==",scheme,len(res))
        seen=set()
        for l,x in res:
            k=(x['fg'],x['bg']);
            if k in seen:continue
            seen.add(k);print(l,x['cr'],x['fg'],'on',x['bg'],x['px'],x['ex'][:50])
