import sys,os
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
errs=[]
def ok(c,m):
    if not c: print("FAIL:",m); sys.exit(1)
    print("OK  ",m)
P=sync_playwright().start()
def run(name,init,ua=None):
    if True:
        p=P;b=p.chromium.launch();ctx=b.new_context(viewport={"width":390,"height":844},has_touch=True,is_mobile=True,**({"user_agent":ua} if ua else {}));pg=ctx.new_page()
        pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_());pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.add_init_script(init);pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(400);ev=pg.evaluate
        pg.click("#shareOpen");pg.wait_for_timeout(500);return b,pg,ev
IOS="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
# 1 iOS: share gets files only (no text)
b,pg,ev=run("ios","window.__s=null;navigator.canShare=()=>true;navigator.share=async d=>{window.__s=d};",IOS)
pg.click("#shShare");pg.wait_for_timeout(500);s=ev("window.__s?{f:window.__s.files.length,t:('text' in window.__s)}:null");print(s)
ok(s and s["f"]==1 and s["t"] is False,"iOS: image only is shared (WhatsApp keeps the image)");b.close()
# 2 Android: image + text
b,pg,ev=run("and","window.__s=null;navigator.canShare=()=>true;navigator.share=async d=>{window.__s=d};")
pg.click("#shShare");pg.wait_for_timeout(500);ok(ev("!!(window.__s&&window.__s.files.length===1&&window.__s.text)"),"Android: image + caption text");b.close()
# 3 share throws (blocked in sandbox) -> viewer opens, not a silent download
b,pg,ev=run("blocked","navigator.canShare=()=>true;navigator.share=async d=>{const e=new Error('x');e.name='NotAllowedError';throw e};")
pg.click("#shShare");pg.wait_for_timeout(700)
ok(ev("!document.querySelector('#shView').hidden"),"share blocked -> save-to-album viewer opens")
ok(ev("document.querySelector('#shImg').src.startsWith('data:image/png')"),"viewer has image (data URL)")
pg.wait_for_timeout(300);ok(ev("document.querySelector('#shImg').naturalWidth")==1080,"viewer image is the 1080px card")
ok("مطولًا" in ev("document.querySelector('#shVp').innerText"),"long-press instruction shown")
pg.keyboard.press("Escape");pg.wait_for_timeout(200);ok(ev("document.querySelector('#shView').hidden")and ev("!document.querySelector('.sh-dlg').hidden"),"Esc closes viewer only");b.close()
# 4 AbortError (user cancelled) -> nothing else opens
b,pg,ev=run("abort","navigator.canShare=()=>true;navigator.share=async d=>{const e=new Error('x');e.name='AbortError';throw e};")
pg.click("#shShare");pg.wait_for_timeout(500);ok(ev("document.querySelector('#shView').hidden"),"cancelled share does nothing");b.close()
# 5 no share support on touch device -> viewer; explicit album button -> viewer (iOS text)
b,pg,ev=run("noshare","navigator.canShare=undefined;",IOS)
pg.click("#shShare");pg.wait_for_timeout(600);ok(not ev("document.querySelector('#shView').hidden"),"no Web Share on a phone -> viewer");ok("حفظ في الصور" in ev("document.querySelector('#shVp').innerText"),"iOS wording: حفظ في الصور")
pg.click("#shVx");pg.wait_for_timeout(200);ok(ev("document.querySelector('#shView').hidden")and not ev("document.querySelector('#shImg').getAttribute('src')"),"done closes viewer and frees image")
pg.click("#shPhotos");pg.wait_for_timeout(600);ok(not ev("document.querySelector('#shView').hidden"),"album button opens viewer");b.close()
print("ERRORS",errs);ok(not errs,"no page errors")
