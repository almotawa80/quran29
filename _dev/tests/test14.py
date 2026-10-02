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
    def login(u,w):
        pg.click("#coordBtn");pg.wait_for_timeout(200);pg.fill("#lgU",u);pg.fill("#lgP",w);pg.click("#lgGo");pg.wait_for_timeout(400)
    def out():ev(f"{SR}.querySelector('#abOut').click()");pg.wait_for_timeout(300)
    def q(s):return f"{SR}.querySelector('{s}')"
    def app():return ev(f"{SR}.querySelector('#app').innerText")
    def clk(s):ev(f"{q(s)}.click()");pg.wait_for_timeout(250)
    def setv(s,v):ev(f"()=>{{const e={q(s)};e.value={v!r};e.dispatchEvent(new Event('input',{{bubbles:true}}));e.dispatchEvent(new Event('change',{{bubbles:true}}))}}")
    login("huda","huda123");ok("إعلان من إدارة" not in app(),"no announcement initially");out()
    login("admin","admin123");
    ev(f"{SR}.querySelector('[data-at=ann]').click()");pg.wait_for_timeout(250)
    ok("مركز الإعلانات" in app() and "الإعلانات (2)" in app(),"admin announcements tab with the 2 sample items")
    for _ in range(2):
        ev(f"{SR}.querySelector('[data-annd]').click()");ev(f"{SR}.querySelector('[data-annd]').click()");pg.wait_for_timeout(250)
    ok("لا توجد إعلانات" in app(),"samples removed, empty list")
    clk("#annAdd");ok(ev(f"{SR}.querySelectorAll('.toast').length")>=1,"empty text rejected")
    setv("#annT","تم تمديد التسجيل حتى 31 أكتوبر <b>x</b>");setv("#annL","warn")
    clk("#annAdd");t=app();ok("نُشر" in t or "تم تمديد" in t,"published");ok("تنبيه هام" in t and "تم تمديد التسجيل" in t,"listed as warn")
    ok(ev(f"{SR}.querySelectorAll('.ann-t b').length")==0,"html escaped")
    setv("#annT","اجتماع المنسقين غدًا");setv("#annL","info");setv("#annE","2020-01-01");clk("#annAdd");ok("لا يمكن" in app() or ev(f"{SR}.querySelectorAll('.ann-it').length")==1,"past end date rejected")
    setv("#annT","اجتماع المنسقين غدًا");setv("#annE","");clk("#annAdd");ok(ev(f"{SR}.querySelectorAll('.ann-it').length")==2,"second announcement")
    out();login("huda","huda123");t=app();print(t[:300].replace("\n"," | "))
    ok("تم تمديد التسجيل" in t and "اجتماع المنسقين" in t,"entity sees both announcements")
    ok(ev(f"{SR}.querySelectorAll('.note.warn[data-ann]').length")==1,"warn styled")
    ev(f"{SR}.querySelector('[data-annx]').click()");pg.wait_for_timeout(250);ok(ev(f"{SR}.querySelectorAll('[data-ann]').length")==1,"dismiss hides one")
    out();login("admin","admin123");ev(f"{SR}.querySelector('[data-at=ann]').click()");pg.wait_for_timeout(250)
    ev(f"{SR}.querySelector('[data-annt]').click()");pg.wait_for_timeout(250)  # stop first item (newest)
    ev(f"{SR}.querySelector('[data-annd]').click()");pg.wait_for_timeout(200);ok("تأكيد الحذف" in app(),"delete asks to confirm")
    ev(f"{SR}.querySelector('[data-annd]').click()");pg.wait_for_timeout(250);ok(ev(f"{SR}.querySelectorAll('.ann-it').length")==1,"deleted after confirm")
    out();login("huda","huda123");ok(ev(f"{SR}.querySelectorAll('[data-ann]').length")==0,"dismissed announcement stays hidden (default: does not come back)") 
    out();login("huda2" if False else "huda","huda123")
    print("PAGE ERRORS:",errors);ok(not errors,"no page errors")
