import sys, os, json
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
    pg.add_init_script("""window.__shared=null;window.__opened=null;window.open=(u)=>{window.__opened=u;return null};
    navigator.canShare=(d)=>!!(d&&d.files&&d.files.length);navigator.share=async(d)=>{window.__shared={n:d.files[0].name,t:d.files[0].type,s:d.files[0].size,text:d.text}};
    Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{window.__clip=t}}});""")
    pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(500);ev=pg.evaluate
    ok(ev("!!document.querySelector('#shareOpen')"),"share chip exists")
    ok(ev("document.querySelector('#shareOpen').getBoundingClientRect().height")>=32,"chip size")
    pg.click("#shareOpen");pg.wait_for_timeout(600)
    ok(ev("!document.querySelector('.sh-dlg').hidden"),"dialog opens")
    ok(ev("document.querySelector('#shCv').width")==1080 and ev("document.querySelector('#shCv').height")==1920,"story canvas 1080x1920")
    pg.screenshot(path="/tmp/sh_a.png")
    pg.fill("#shName","خالد بن عبدالله المطيري");pg.wait_for_timeout(400)
    ok(ev("document.querySelector('#shCv').toDataURL().length")>20000,"canvas has content")
    pg.click("[data-t=cream]");pg.click("[data-m=child]");pg.wait_for_timeout(300);pg.evaluate("document.querySelector('#shCv').toBlob(b=>{})")
    open("/tmp/sh_cream.png","wb").write(__import__("base64").b64decode(ev("document.querySelector('#shCv').toDataURL().split(',')[1]")))
    pg.click("[data-t=night]");pg.click("[data-m=invite]");pg.click("[data-f=square]");pg.wait_for_timeout(300)
    ok(ev("document.querySelector('#shCv').height")==1080,"square canvas")
    open("/tmp/sh_night.png","wb").write(__import__("base64").b64decode(ev("document.querySelector('#shCv').toDataURL().split(',')[1]")))
    pg.click("[data-t=green]");pg.click("[data-m=me]");pg.click("[data-f=story]");pg.wait_for_timeout(300)
    open("/tmp/sh_green.png","wb").write(__import__("base64").b64decode(ev("document.querySelector('#shCv').toDataURL().split(',')[1]")))
    pg.click("#shShare");pg.wait_for_timeout(600);sh=ev("window.__shared");print(sh)
    ok(sh and sh["n"]=="quran29-invite.png" and sh["t"]=="image/png" and sh["s"]>10000,"system share gets a PNG file")
    ok("خالد بن عبدالله المطيري" in sh["text"] and "29 أكتوبر" in sh["text"],"share text has name + deadline")
    ok(ev("document.querySelector('#shWa').tagName")=="A" and ev("document.querySelector('#shWa').href").startswith("https://wa.me/?text="),"WhatsApp is a real link (works even where popups from scripts are blocked)")
    ok("29" in __import__("urllib.parse",fromlist=["x"]).unquote(ev("document.querySelector('#shWa').href")),"WhatsApp link carries the text")
    ok(ev("document.querySelector('#shPv').src.startsWith('data:image/png')"),"preview is a long-press-savable <img>")
    ok(ev("document.querySelector('#shPv').naturalWidth")==1080,"preview image is the full card")
    ok("29 أكتوبر" in ev("document.querySelector('#shTxt').value"),"ready text box is filled")
    ok("مطولًا" in ev("document.querySelector('#shTip').innerText"),"long-press tip shown on phones")
    pg.click("#shCopy");pg.wait_for_timeout(300);ok("29 أكتوبر" in (ev("window.__clip||''")),"copy text")
    pg.keyboard.press("Escape");pg.wait_for_timeout(200);ok(ev("document.querySelector('.sh-dlg').hidden"),"Escape closes")
    ok(ev("document.documentElement.style.overflow")=="","page scroll restored")
    print("PAGE ERRORS:",errors);ok(not errors,"no page errors")
