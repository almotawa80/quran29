import sys,os
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
SR="document.querySelector('.pt-host').shadowRoot"
fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for th in ("light","dark"):
        pg=b.new_page(viewport={"width":390,"height":900},color_scheme=th);errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_())
        pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(400);ev=pg.evaluate
        pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU","admin");pg.fill("#lgP","admin123");pg.click("#lgGo");pg.wait_for_timeout(500)
        app=lambda:ev(f"{SR}.querySelector('#app').innerText")
        ok("تفاصيل زوار الدليل" in app(),th+": dashboard has link to visitors tab")
        ev(f"{SR}.querySelector('.btn[data-at=vis]').click()");pg.wait_for_timeout(400)
        t=app()
        ok("ملخص الفترة بكلمات" in t and "رحلة التفاعل" in t and "خريطة ساعات الأسبوع" in t and "الأجهزة" in t,th+": all sections present")
        ok("(أرقام تجريبية)" in t,th+": demo numbers flagged")
        v7=ev(f"{SR}.querySelector('.vk-n').innerText")
        ev(f"{SR}.querySelector('[data-vr=\"30\"]').click()");pg.wait_for_timeout(300)
        v30=ev(f"{SR}.querySelector('.vk-n').innerText")
        ok(int(v30.replace(',',''))>int(v7.replace(',','')),th+f": 30-day visits ({v30}) > 7-day ({v7})")
        ok(ev(f"{SR}.querySelector('[data-vr=\"30\"]').getAttribute('aria-pressed')")=="true",th+": pressed state")
        ok(ev(f"{SR}.querySelectorAll('.vsvg rect').length")>=168+20,th+": heat map + bars drawn")
        ok(ev(f"{SR}.querySelectorAll('.spark').length")==3,th+": three sparklines")
        ok(ev(f"[...{SR}.querySelectorAll('.vsvg title')].every(t=>!/NaN|undefined/.test(t.textContent))"),th+": no NaN in chart tooltips")
        ok("NaN" not in app() and "undefined" not in app(),th+": no NaN/undefined in text")
        ev(f"{SR}.querySelector('[data-at=facts]').click()");pg.wait_for_timeout(300)
        ok("إجمالي الزيارات" in app(),th+": dashboard still shows visit tiles")
        ok(not errs,th+": no page errors "+str(errs))
        # contrast of new text (real computed colours)
        r=ev("""()=>{const R=document.querySelector('.pt-host').shadowRoot;const q=s=>R.querySelector(s);
          const lum=c=>{const m=c.match(/\\d+(\\.\\d+)?/g).map(Number);const f=[m[0],m[1],m[2]].map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*f[0]+.7152*f[1]+.0722*f[2]};
          const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
          const bg=getComputedStyle(q('.card')).backgroundColor;const out={};
          for(const s of ['.vstory li','.vsub','.vk-l']){const e=q(s);if(e)out[s]=+ratio(getComputedStyle(e).color,getComputedStyle(e.closest('.card')||e.closest('.vk')).backgroundColor||bg).toFixed(2)}
          return out}""")
        print(th,r)
    b.close()
print("FAILS",fails)
