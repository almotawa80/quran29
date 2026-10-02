import sys, os
from playwright.sync_api import sync_playwright
PATH = "file://" + os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
SR = "document.querySelector('.pt-host').shadowRoot"
errors=[]
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":900});pg.on("pageerror",lambda e:errors.append(str(e)))
    pg.goto(PATH);pg.wait_for_timeout(300);ev=pg.evaluate
    pg.click("#coordBtn");pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(400)
    ev(f"{SR}.querySelector('#add').click()");pg.wait_for_timeout(300)
    def val(sel):return ev(f"{SR}.querySelector('{sel}').value")
    def cid_for(y,m,d):return ("2" if y<2000 else "3")+f"{y%100:02d}{m:02d}{d:02d}"+"12345"
    def type_cid(c):
        ev(f"()=>{{const i={SR}.querySelector('#fc');i.value='{c}';i.dispatchEvent(new Event('input',{{bubbles:true}}))}}");pg.wait_for_timeout(300)
    ok(ev(f"{SR}.querySelector('#fbn')?.tagName")=="DIV" and "—" in ev(f"{SR}.querySelector('#fbn').innerText"),"before dob: band shows placeholder, not a full list")
    type_cid(cid_for(2020,5,10))   # ~6 years at 2026-11-22 => band 6-11
    d1=val("#fd");print("dob1",d1)
    ok(d1=="2020-05-10","dob filled from cid")
    t1=ev(f"{SR}.querySelector('#fbn').innerText");print(t1)
    ok("6" in t1 and "11" in t1,"band tied to dob (6-11)")
    ok(not ev(f"!!{SR}.querySelector('select#fbn')"),"no band dropdown listing all bands")
    type_cid(cid_for(2017,3,3))   # 9 years
    ok(val("#fd")=="2017-03-03","changing cid updates dob")
    type_cid(cid_for(2005,8,1))   # 21 years => band 18-25
    ok(val("#fd")=="2005-08-01","changing cid again updates dob")
    t3=ev(f"{SR}.querySelector('#fbn').innerText");print(t3);ok("18" in t3 and "25" in t3,"band follows new dob")
    # change dob directly
    ev(f"()=>{{const i={SR}.querySelector('#fd');i.value='2022-01-01';i.dispatchEvent(new Event('change',{{bubbles:true}}))}}");pg.wait_for_timeout(300)
    t4=ev(f"{SR}.querySelector('#fbn').innerText");print(t4);ok("3" in t4 and "6" in t4,"band follows manual dob change (3-6)")
    # Arabic-Indic digits
    ev(f"()=>{{const i={SR}.querySelector('#fc');i.value='٣٠٥٠٦١٠١٢٣٤٥';i.dispatchEvent(new Event('input',{{bubbles:true}}))}}");pg.wait_for_timeout(300)
    ok(val("#fc")=="305061012345","arabic-indic cid converted to ascii")
    ok(val("#fd")=="2005-06-10","dob extracted from arabic-digit cid")
    for sel,txt,exp in (("#fph","٥٥٥١٢٣٤٥","55512345"),("#fph2","۶۶۶۵۴۳۲۱","66654321")):
        ev(f"()=>{{const i={SR}.querySelector('{sel}');i.value='{txt}';i.dispatchEvent(new Event('input',{{bubbles:true}}))}}");pg.wait_for_timeout(150)
        ok(val(sel)==exp,f"{sel} converted ({exp})")
    ok(not errors,"no page errors "+str(errors));b.close()
