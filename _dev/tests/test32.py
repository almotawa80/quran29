# assistant knows the guide's own features and the statement sections
import sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8765/ix.html";fails=[]
def ok(c,m):
    print(("PASS " if c else "FAIL ")+m)
    if not c: fails.append(m)
C=[("ما هي لعبة اختبر حفظي؟","لعبة تدريبية"),("كيف أختبر حفظي","لعبة تدريبية"),("أبي أراجع حفظي","لعبة تدريبية"),
 ("شارك دعوتك","بطاقة جاهزة"),("كيف أشارك الدليل مع أصدقائي","بطاقة جاهزة"),("أبي أرسل رابط الدليل","بطاقة جاهزة"),
 ("بوابة الجهات","بوابة الجهات خاصة"),("كيف يدخل المنسق للبوابة","بوابة الجهات خاصة"),("نسيت كلمة المرور","بوابة الجهات خاصة"),
 ("حاسبة نقاط الجهات","حاسبة نقاط الجهة"),("كيف أحسب النقاط","حاسبة نقاط الجهة"),
 ("كيف أكبر الخط","حجم الخط"),("الوضع الداكن","الخلفية"),("أبي أغير الألوان","الخلفية"),
 ("أين الإعلانات","إعلانات المسابقة"),
 ("ما هي الفروع؟","6 فروع"),("كم عدد الفروع","6 فروع"),
 ("جائزة أفضل منسق","500 د.ك"),
 ("أهداف المسابقة","أهداف المسابقة"),("نبذة عن المسابقة","الأمانة العامة للأوقاف"),("سياسات المسابقة","سياسات المسابقة"),
 ("ماذا يوجد في الدليل","في هذا الدليل"),("ماذا تستطيع أن تفعل","في هذا الدليل"),
 # older answers must stay right
 ("متى آخر يوم للتسجيل؟","29 أكتوبر"),("كيف أسجّل؟","الجهات"),("ما هي الدروع؟","التفوق العام"),("متى النتائج؟","16 ديسمبر"),
 ("متى إعلان النتائج","16 ديسمبر"),("كيف أعترض على قرار لجنة التحكيم؟","بكتاب رسمي"),("متى اللجان الصباحية؟","اللجان الصباحية"),
 ("من هم أعضاء اللجنة الدائمة؟","رئيس اللجنة"),("رقم جمعية النجاة","النجاة"),("ابني عمره 8 ويحفظ جزأين","النشء")]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={"width":390,"height":844});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") and "localhost" not in r.request.url else r.continue_())
    pg.goto(U);pg.wait_for_timeout(700);ev=pg.evaluate;ev("document.querySelector('.tb[data-v=\"2\"]').click()")
    for q,want in C:
        pg.fill("#aiIn",q);ev("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(950)
        t=ev("[...document.querySelectorAll('#aiLog .ai-turn')].pop().innerText")
        ok(want in t,f"'{q}' -> {want}" + ("" if want in t else " | got: "+t.replace(chr(10),' ')[:120]))
    # buttons open the right thing
    def act(q,k,check,label):
        pg.goto(U);pg.wait_for_timeout(600);ev("sessionStorage.clear()");pg.reload();pg.wait_for_timeout(600);ev("document.querySelector('.tb[data-v=\"2\"]').click()")
        pg.fill("#aiIn",q);ev("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(1000)
        ev(f"[...document.querySelectorAll('#aiLog .ai-act[data-act={k}]')].pop().click()");pg.wait_for_timeout(900)
        ok(ev(check),label)
    act("اختبر حفظي","game","(()=>{const d=document.querySelector('.qz-dlg');return !!d&&!d.hidden&&getComputedStyle(d).display!=='none'})()","game button opens the game")
    act("شارك دعوتك","invite","(()=>{const d=document.querySelector('.sh-dlg');return !!d&&!d.hidden&&getComputedStyle(d).display!=='none'&&/شارك دعوتك/.test(d.textContent)})()","invite button opens the invitation card")
    act("الوضع الداكن","settings","(()=>{const e=document.getElementById('settings');return !!e&&!!e.offsetParent})()","settings button opens display settings")
    act("أهداف المسابقة","goals","(()=>{const p=[...document.querySelectorAll('.about-view .sub-pane')].find(x=>x.dataset.st==='الأهداف');return !!p&&!p.hidden&&!!p.offsetParent})()","goals button opens the goals tab")
    # follow-up suggestion that is not a chip still answers
    pg.goto(U);pg.wait_for_timeout(600);ev("document.querySelector('.tb[data-v=\"2\"]').click()")
    pg.fill("#aiIn","اختبر حفظي");ev("document.getElementById('aiForm').requestSubmit()");pg.wait_for_timeout(1000)
    ev("[...document.querySelectorAll('#aiLog .ai-opt')].find(b=>b.textContent==='شارك دعوتك').click()");pg.wait_for_timeout(1200)
    ok("بطاقة جاهزة" in ev("[...document.querySelectorAll('#aiLog .ai-turn')].pop().innerText"),"follow-up 'شارك دعوتك' answers")
    ok(not errs,"no errors "+str(errs));b.close()
print("FAILS:",fails)
