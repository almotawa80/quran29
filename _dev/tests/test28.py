# own passwords + admin reset + reminders for entities without candidates (offline copy)
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
        pg.goto(U);pg.wait_for_timeout(500);ev=pg.evaluate;L=lambda s:pg.locator(".pt-host").locator(s)
        app=lambda:ev(f"{SR}.querySelector('#app').innerText")
        toast=lambda:ev(f"[...{SR}.querySelectorAll('.toast')].map(t=>t.textContent).join(' | ')")
        def login(u,pw):
            if ev("!!document.querySelector('.pt-host')"):ev(f"{SR}.querySelector('#abOut')&&{SR}.querySelector('#abOut').click()");pg.wait_for_timeout(400)
            if pg.is_visible("#ptBye"):pg.click("#ptBye .x")
            pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU",u);pg.fill("#lgP",pw);pg.click("#lgGo");pg.wait_for_timeout(600)
        login("admin","admin123")
        ev(f"{SR}.querySelector('[data-at=ents]').click()");pg.wait_for_timeout(300)
        sel=f"[...{SR}.querySelectorAll('#app .row')].find(r=>r.innerText.includes('huda')).querySelector('[data-rp]:not([data-rev])')"
        ev(f"{sel}.click()");pg.wait_for_timeout(100);ok("اضغط للتأكيد" in ev(f"{sel}.textContent"),th+": reset asks to confirm")
        ev(f"{sel}.click()");pg.wait_for_timeout(400)
        t=app();ok("كلمة مرور جديدة لـ" in t,th+": new password shown to admin")
        npw=ev(f"{SR}.querySelector('.ok-note code').textContent");ok(len(npw)==8,th+": 8-character password")
        href=ev(f"{SR}.querySelector('.ok-note a.btn.wa').href");import urllib.parse as up
        ok("سيُطلب منك اختيار كلمة مرور خاصة بك" in up.unquote(href) and npw in up.unquote(href),th+": WhatsApp message has the new password and the note")
        # reminders tab
        ev(f"{SR}.querySelector('[data-at=stats]').click()");pg.wait_for_timeout(300);t=app()
        ok("جهات تحتاج متابعة" in t,th+": follow-up card title")
        none_n=ev("__PTS.ENT.filter(e=>e.active!==false&&!__PTS.CANDS.some(c=>c.ent===e.id&&c.status!=='cancelled')).length")
        ok(none_n==0 or "لم تسجّل أي مرشح بعد" in t,th+f": entities without candidates listed ({none_n})")
        a=f"{SR}.querySelector('#app a[data-rmid]')"
        if ev(f"!!{a}"):
            ev(f"{a}.addEventListener('click',e=>e.preventDefault())");ev(f"{a}.click()");pg.wait_for_timeout(700)
            ok("ذُكِّرت اليوم" in app(),th+": reminded today marker")
        if none_n:
            hs=ev(f"[...{SR}.querySelectorAll('#app a[data-rmid]')].map(a=>decodeURIComponent(a.href)).join('\\n')")
            ok("لم يُسجَّل في" in hs,th+": message for entity with no candidates")
        # coordinator forced to choose a password
        login("huda",npw)
        ok("اختر كلمة مرور خاصة بك" in app() and ev(f"!!{SR}.querySelector('#pwOut')") and not ev(f"!!{SR}.querySelector('#pwBack')"),th+": forced password screen after reset")
        L("#pw0").fill("wrongpass");L("#pw1").fill("NewPass2026");L("#pw2").fill("NewPass2026");ev(f"{SR}.querySelector('#pwSave').click()");pg.wait_for_timeout(300)
        ok("غير صحيحة" in ev(f"{SR}.querySelector('#pwE').textContent"),th+": wrong current password rejected")
        L("#pw0").fill(npw);L("#pw2").fill("Other2026x");ev(f"{SR}.querySelector('#pwSave').click()");pg.wait_for_timeout(300)
        ok("لا يطابق" in ev(f"{SR}.querySelector('#pwE').textContent"),th+": mismatch rejected")
        L("#pw1").fill("short");L("#pw2").fill("short");ev(f"{SR}.querySelector('#pwSave').click()");pg.wait_for_timeout(300)
        ok("8 أحرف" in ev(f"{SR}.querySelector('#pwE').textContent"),th+": short password rejected")
        L("#pw1").fill("NewPass2026");L("#pw2").fill("NewPass2026");ev(f"{SR}.querySelector('#pwSave').click()");pg.wait_for_timeout(400)
        ok("قائمة مرشحي الجهة" in app() and "حُفظت كلمة المرور" in toast(),th+": password saved, list opens")
        login("huda","NewPass2026");ok("قائمة مرشحي الجهة" in app(),th+": signs in with own password, not asked again")
        ev(f"{SR}.querySelector('#pwGo').click()");pg.wait_for_timeout(300)
        ok("تغيير كلمة المرور" in app() and ev(f"!!{SR}.querySelector('#pwBack')"),th+": optional change from the list")
        L("#pw1").fill("abc");ev(f"{SR}.querySelector('#pw1').dispatchEvent(new Event('input'))");ok("قصيرة" in ev(f"{SR}.querySelector('#pwH').textContent"),th+": live strength hint")
        ev(f"{SR}.querySelector('#pwBack').click()");pg.wait_for_timeout(300);ok("قائمة مرشحي الجهة" in app(),th+": back to list")
        pg.screenshot(path=f"/tmp/pw_{th}.png")
        ok(not errs,th+": no errors "+str(errs));ctx.close()
    b.close()
print("FAILS:",fails)
