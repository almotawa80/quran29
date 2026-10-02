# announcements by audience — offline (Claude) copy
from playwright.sync_api import sync_playwright
U="http://localhost:8765/ix.html";SR="document.querySelector('.pt-host').shadowRoot";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in ("light","dark"):
        ctx=b.new_context(viewport={"width":390,"height":900},color_scheme=th);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U,wait_until="domcontentloaded");pg.wait_for_timeout(500);ev=pg.evaluate
        g=lambda:ev("document.querySelector('.gann-wrap').innerText")
        ok("مرحبًا بكم في دليل" in g() and "التسجيل في المسابقة عن طريق" in g(),th+": guide shows visitor announcements")
        ok("أكملوا بيانات المرشحين" not in g(),th+": entity-only text is not shown to visitors")
        ok(ev("document.querySelector('.gann-wrap .gann').classList.contains('warn')"),th+": important notice listed first")
        ok(ev("document.querySelector('header .gann-wrap+.hb-row')!==null"),th+": banner sits above the home buttons")
        bb=ev("(()=>{const r=document.querySelector('[data-gannx]').getBoundingClientRect();return [r.width,r.height]})()");ok(bb[0]>=44 and bb[1]>=44,th+": × is 44px")
        # contrast
        r=ev("""()=>{const lum=c=>{const m=c.match(/[\\d.]+/g).map(Number);const f=m.slice(0,3).map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*f[0]+.7152*f[1]+.0722*f[2]};
          const ra=(a,b)=>{const x=lum(a),y=lum(b);return +((Math.max(x,y)+.05)/(Math.min(x,y)+.05)).toFixed(2)};const o={};
          document.querySelectorAll('.gann').forEach((g,i)=>{const bg=getComputedStyle(g).backgroundColor;o['b'+i]=ra(getComputedStyle(g.querySelector('b')).color,bg);o['p'+i]=ra(getComputedStyle(g.querySelector('p')).color,bg);o['x'+i]=ra(getComputedStyle(g.querySelector('button')).color,bg)});return o}""")
        ok(all(v>=4.5 for v in r.values()),th+": banner contrast "+str(r))
        ev("document.querySelector('[data-gannx]').click()");pg.wait_for_timeout(200)
        ok("التسجيل في المسابقة عن طريق" not in g() and "مرحبًا بكم" in g(),th+": × hides one announcement")
        pg.reload(wait_until="domcontentloaded");pg.wait_for_timeout(500)
        ok("التسجيل في المسابقة عن طريق" not in g(),th+": stays hidden after reload")
        # entity sees only entity text
        pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(600)
        app=lambda:ev(f"{SR}.querySelector('#app').innerText")
        ok("أكملوا بيانات المرشحين" in app() and "مرحبًا بكم في دليل" not in app() and "التسجيل في المسابقة عن طريق" not in app(),th+": entity sees only entity announcements")
        ev(f"{SR}.querySelector('[data-act=logout],#lo,.logout')&&{SR}.querySelector('[data-act=logout],#lo,.logout').click()")
        pg.reload(wait_until="domcontentloaded");pg.wait_for_timeout(500)
        if ev(f"!!document.querySelector('.pt-host')&&!!{SR}.querySelector('#app')&&{SR}.querySelector('#app').innerText.includes('أكملوا')"):
            pass
        ctx.close()
        # admin
        ctx=b.new_context(viewport={"width":390,"height":900},color_scheme=th);pg=ctx.new_page();errs2=[];pg.on("pageerror",lambda e:errs2.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
        pg.goto(U,wait_until="domcontentloaded");pg.wait_for_timeout(400);ev=pg.evaluate;app=lambda:ev(f"{SR}.querySelector('#app').innerText")
        pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(500)
        ev(f"{SR}.querySelector('[data-at=ann]').click()");pg.wait_for_timeout(300)
        t=app()
        ok("لمن يظهر الإعلان؟" in t and "نص مختلف لكل جمهور" in t,th+": audience choice shown")
        ok("نص لكل جمهور" in t and "للزوار" in t and "ظهر للزوار" in t,th+": list shows audience pill and visitor stats")
        ok(t.count("للجهات")>=1 and "الإعلانات (2)" in t,th+": split item counted as one ("+t[t.find('الإعلانات ('):][:14]+")")
        # publish split
        ev(f"{SR}.querySelector('[data-aud=split]').click()");pg.wait_for_timeout(150)
        ok(ev(f"!!{SR}.querySelector('#annT2')"),th+": split shows a second text box")
        sr=lambda s:pg.locator(".pt-host").locator(s)
        sr("#annT").fill("زوارنا الكرام: تم تمديد التسجيل.");sr("#annT2").fill("للجهات: تم تمديد رفع الكشوف.")
        sr("#annU").fill("http://bad link");ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(200)
        ok("https://" in ev(f"{SR}.querySelector('.toast')?{SR}.querySelector('.toast').innerText:document.body.innerText"),th+": bad link rejected")
        sr("#annU").fill("https://example.org/news");sr("#annUL").fill("اقرأ المزيد")
        ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(300)
        t=app();ok("زوارنا الكرام" in t and "للجهات: تم تمديد" in t and "زر: اقرأ المزيد" in t and "الإعلانات (3)" in t,th+": split published as one item")
        g=lambda:ev("document.querySelector('.gann-wrap').innerText")
        ok("زوارنا الكرام" in g() and "للجهات: تم تمديد" not in g(),th+": guide updates live with visitor text only")
        ok(ev("document.querySelector('.gann-wrap a')?.getAttribute('rel')")=="noopener noreferrer",th+": link opens safely")
        # filter
        ev(f"{SR}.querySelector('[data-annf=public]').click()");pg.wait_for_timeout(150);t=app()
        ok("زوارنا الكرام" in t and "مرحبًا بكم" in t,th+": filter visitors")
        ev(f"{SR}.querySelector('[data-annf=ents]').click()");pg.wait_for_timeout(150);t=app()
        ok("مرحبًا بكم" not in t and "للجهات: تم تمديد" in t,th+": filter entities")
        ev(f"{SR}.querySelector('[data-annf=all]').click()");pg.wait_for_timeout(150)
        # stop group
        ev(f"[...{SR}.querySelectorAll('.ann-it')].find(x=>x.innerText.includes('زوارنا الكرام')).querySelector('[data-annt]').click()");pg.wait_for_timeout(300)
        ok("زوارنا الكرام" not in g(),th+": stopping hides it from the guide")
        ok(ev(f"__PTS.ANNS.filter(a=>a.text.includes('تم تمديد')).every(a=>a.active===false)"),th+": stop applies to both texts")
        # scheduled
        ev(f"{SR}.querySelector('[data-aud=public]').click()");pg.wait_for_timeout(100)
        sr("#annT").fill("إعلان مجدول للمستقبل");sr("#annS").fill("2099-01-01");ev(f"{SR}.querySelector('#annAdd').click()");pg.wait_for_timeout(300)
        ok("مجدول" in app() and "إعلان مجدول" not in g(),th+": scheduled announcement waits for its date")
        # layout: no horizontal overflow
        ok(ev(f"{SR}.querySelector('.pt-scroll')?{SR}.querySelector('.pt-scroll').scrollWidth<={SR}.querySelector('.pt-scroll').clientWidth+1:true"),th+": no horizontal scroll")
        pg.screenshot(path=f"/tmp/ann_{th}.png",full_page=False)
        ok(not errs and not errs2,th+": no page errors "+str(errs+errs2))
        ctx.close()
    b.close()
print("FAILS:",fails)
