  // ---------- UI ----------
  const ST_KEY="q29g",QFONT='"Amiri Quran","Noto Naskh Arabic","Scheherazade New","Traditional Arabic",serif';
  const store={get(){try{return JSON.parse(localStorage.getItem(ST_KEY)||"{}")}catch(e){return{}}},set(o){try{localStorage.setItem(ST_KEY,JSON.stringify(o))}catch(e){}}};
  const saved=store.get();
  const G={juz:Array.isArray(saved.juz)&&saved.juz.length?saved.juz:[30],n:[5,10,15,20].includes(saved.n)?saved.n:10,lv:LV[saved.lv]?saved.lv:"easy",types:Array.isArray(saved.types)&&saved.types.length?saved.types.filter(t=>TYPES[t]):Object.keys(TYPES),timer:!!saved.timer};
  if(!G.types.length)G.types=Object.keys(TYPES);
  let dlg,body,scr="setup",Rn=null,tm=null,lastFocus=null,confirmExit=false;
  const esc=t=>String(t).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const ar=n=>String(n).replace(/\d/g,d=>"٠١٢٣٤٥٦٧٨٩"[d]);
  const LET=["أ","ب","ج","د"];
  const OKM=["أحسنت!","ما شاء الله!","بارك الله فيك!","إجابة صحيحة!","ثبّتك الله!"];
  const NOM=["لا بأس، كل محاولة تقرّبك.","قريب! راجع الآية جيدًا.","المراجعة طريق الإتقان.","حاول مع السؤال التالي."];
  const BADGES=[[100,"حافظ متقن","أنت في القمة، أتقنت كل الأسئلة."],[80,"متمكّن","حفظ قوي، اقتربت من الإتقان."],[60,"على الطريق","بداية طيبة، والمراجعة ترفعك."],[40,"مجتهد","استمر، فالتكرار أساس الحفظ."],[0,"بداية موفقة","كل حافظ بدأ من هنا، جرّب مرة أخرى."]];
  const badgeOf=p=>BADGES.find(b=>p>=b[0]);
  const icon={flame:'<path d="M12 3c1 3.2 4.5 5 4.5 9.2A4.5 4.5 0 0 1 12 17a4.5 4.5 0 0 1-4.5-4.8c0-1.8.9-3 2-4 .3 1.4 1 2 1.8 2.2C11 8.6 11 5.4 12 3z"/>',bulb:'<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1.1 1.3 1.1 2.2h5c0-.9.5-1.7 1.1-2.2A6 6 0 0 0 12 3z"/>',x:'<path d="M6 6l12 12M18 6L6 18"/>',star:'<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.4 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z"/>'};
  const svg=(n,s=20)=>`<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icon[n]}</svg>`;
  function persist(){store.set(Object.assign({},store.get(),{juz:G.juz,n:G.n,lv:G.lv,types:G.types,timer:G.timer}))}
  function bestGet(lv){const b=store.get().best||{};return b[lv]||0}
  function bestSet(lv,v){const s=store.get();s.best=s.best||{};s.best[lv]=v;store.set(s)}
  function juzTxt(){if(G.juz.length===30)return "كل القرآن";const j=G.juz.slice().sort((a,b)=>a-b);return (j.length===1?"الجزء ":"الأجزاء ")+j.map(ar).join("، ")}
  function head(title,sub,x=true){return `<div class="qz-h"><div><b>${title}</b>${sub?`<small>${sub}</small>`:""}</div>${x?`<button type="button" class="qz-x" data-a="close" aria-label="إغلاق">${svg("x",22)}</button>`:""}</div>`}
  function vSetup(msg){
    scr="setup";
    body.innerHTML=head("اختبر حفظي","لعبة تدريبية بأسئلة متعددة الخيارات")+
    `<div class="qz-sec"><h3>المستوى</h3><div class="qz-row" role="radiogroup" aria-label="المستوى">${Object.entries(LV).map(([k,v])=>`<button type="button" class="qz-c" role="radio" aria-checked="${G.lv===k}" data-lv="${k}">${v.n}</button>`).join("")}</div><p class="qz-d">${LV[G.lv].d}</p></div>
    <div class="qz-sec"><h3>عدد الأسئلة</h3><div class="qz-row" role="radiogroup" aria-label="عدد الأسئلة">${[5,10,15,20].map(n=>`<button type="button" class="qz-c" role="radio" aria-checked="${G.n===n}" data-n="${n}">${ar(n)}</button>`).join("")}</div></div>
    <div class="qz-sec"><h3>الأجزاء <small>(${juzTxt()})</small></h3><div class="qz-row qz-pre"><button type="button" class="qz-c s" data-pre="all">كل القرآن</button><button type="button" class="qz-c s" data-pre="amma">جزء عمّ</button><button type="button" class="qz-c s" data-pre="last5">آخر 5 أجزاء</button><button type="button" class="qz-c s" data-pre="clear">مسح</button></div>
      <div class="qz-juz" role="group" aria-label="اختيار الأجزاء">${Array.from({length:30},(_,i)=>i+1).map(j=>`<button type="button" class="qz-j" data-j="${j}" aria-pressed="${G.juz.includes(j)}" aria-label="الجزء ${j}">${ar(j)}</button>`).join("")}</div></div>
    <div class="qz-sec"><h3>أنواع الأسئلة</h3><div class="qz-row">${Object.entries(TYPES).map(([k,v])=>`<button type="button" class="qz-c" data-t="${k}" aria-pressed="${G.types.includes(k)}">${v}</button>`).join("")}</div></div>
    <label class="qz-chk"><input type="checkbox" id="qzTm" ${G.timer?"checked":""}> مؤقت ٢٥ ثانية لكل سؤال، مع نقاط سرعة</label>
    ${msg?`<div class="qz-err" role="alert">${msg}</div>`:""}
    <button type="button" class="qz-go" data-a="start" ${G.juz.length&&G.types.length?"":"disabled"}>ابدأ الاختبار</button>
    <p class="qz-note">لعبة للتدريب فقط، وليست جزءًا من تقييم المسابقة الرسمي. تقسيم الأجزاء وفق المصحف المدني. نص المصحف من «موسوعة القرآن الكريم» (quranenc.com) برخصة CC BY 4.0.</p>`}
  function clr(){clearInterval(tm);tm=null}
  function points(q){const base=LV[q.lv].base,mult=1+Math.min(2,Math.floor(Rn.streak/3))*0.5;let p=Math.round(base*mult);if(Rn.hintUsed)p=Math.round(p/2);return p}
  function vQ(){
    scr="quiz";clr();confirmExit=false;const q=Rn.qs[Rn.i];Rn.hintUsed=false;Rn.done=false;Rn.qStart=Date.now();
    const mult=1+Math.min(2,Math.floor(Rn.streak/3))*0.5;
    body.innerHTML=`<div class="qz-top"><div class="qz-prog"><span>سؤال ${ar(Rn.i+1)} من ${ar(Rn.qs.length)}</span><i><u style="width:${Rn.i/Rn.qs.length*100}%"></u></i></div>
      <div class="qz-stat"><span class="qz-pts" title="النقاط">${svg("star",18)}<b id="qzPts">${ar(Rn.score)}</b></span><span class="qz-fire ${Rn.streak>=3?"on":""}" title="سلسلة الإجابات الصحيحة">${svg("flame",18)}<b>${mult>1?"×"+ar(mult):ar(Rn.streak)}</b></span>
      <button type="button" class="qz-hint" data-a="hint" ${Rn.hints?"":"disabled"} aria-label="تلميح: حذف خيارين">${svg("bulb",18)}<span>${ar(Rn.hints)}</span></button>
      <button type="button" class="qz-x" data-a="exit" aria-label="إنهاء الاختبار">${svg("x",22)}</button></div></div>
      ${G.timer?`<div class="qz-time" aria-hidden="true"><u id="qzT"></u></div>`:""}
      <div id="qzExit"></div>
      <div class="qz-card"><div class="qz-type">${TYPES[q.type]}${q.type==="complete"?" — اختر تتمّة الآية":q.type==="next"?" — ما الآية التي تليها؟":q.type==="surah"?" — ما السورة التي وردت فيها الآية؟":" — اختر الكلمة المناسبة"}</div>
      <div class="qz-q" lang="ar" dir="rtl">${esc(q.stem)}${q.type==="complete"?" <span class=\"qz-dots\">…</span>":""}</div></div>
      <div class="qz-ch" role="group" aria-label="الخيارات">${q.choices.map((c,i)=>`<button type="button" class="qz-o${q.type==="surah"||q.type==="word"?" short":""}" data-o="${i}"><span class="qz-l">${LET[i]}</span><span class="qz-t" lang="ar" dir="rtl">${esc(q.type==="complete"?"… "+c:c)}</span></button>`).join("")}</div>
      <div id="qzFb" role="status" aria-live="polite"></div>`;
    if(G.timer){const t0=Date.now(),T=25000,bar=body.querySelector("#qzT");tm=setInterval(()=>{const r=Math.max(0,1-(Date.now()-t0)/T);bar.style.width=r*100+"%";bar.classList.toggle("low",r<.3);if(r<=0){clr();answer(-1)}},100)}
  }
  function fullHtml(q){
    if(q.type==="complete")return `<div class="qz-full" lang="ar" dir="rtl">${esc(q.stem)} <b>${esc(q.done)}</b></div><div class="qz-ref">${q.ref}</div>`;
    if(q.type==="next")return `<div class="qz-full" lang="ar" dir="rtl">${esc(q.stem)}</div><div class="qz-ref">${q.ref}</div><div class="qz-full nx" lang="ar" dir="rtl"><b>${esc(q.nextT)}</b></div><div class="qz-ref">${q.nextRef}</div>`;
    if(q.type==="word"){const ws=q.full.split(" ");return `<div class="qz-full" lang="ar" dir="rtl">${ws.map((w,i)=>i===q.pos?`<b>${esc(w)}</b>`:esc(w)).join(" ")}</div><div class="qz-ref">${q.ref}</div>`}
    return `<div class="qz-full" lang="ar" dir="rtl">${esc(q.full)}</div><div class="qz-ref"><b>${q.ref}</b></div>`}
  function answer(i){
    if(Rn.done)return;Rn.done=true;clr();const q=Rn.qs[Rn.i],good=i===q.ans;let pts=0;
    if(good){pts=points(q);if(G.timer&&Date.now()-Rn.qStart<10000)pts+=5;Rn.score+=pts;Rn.ok++;Rn.streak++;Rn.bestStreak=Math.max(Rn.bestStreak,Rn.streak)}else Rn.streak=0;
    Rn.log.push({q,pick:i,good,pts});
    body.querySelectorAll(".qz-o").forEach((b,k)=>{b.disabled=true;b.classList.toggle("ok",k===q.ans);b.classList.toggle("no",k===i&&!good)});
    const last=Rn.i===Rn.qs.length-1;
    body.querySelector("#qzFb").innerHTML=`<div class="qz-fb ${good?"g":"b"}"><div class="qz-fh"><b>${good?pick(OKM):(i<0?"انتهى الوقت.":pick(NOM))}</b>${good?`<span class="qz-add">+${ar(pts)}</span>`:""}</div>${good&&Rn.streak>=3?`<p class="qz-s">سلسلة ${ar(Rn.streak)} إجابات متتالية${Rn.streak%3===0&&Rn.streak<9?"، ارتفع مضاعف النقاط!":""}</p>`:""}${good?"":`<p class="qz-s">الإجابة الصحيحة: <b lang="ar">${esc(q.type==="complete"?q.choices[q.ans]:q.choices[q.ans].slice(0,120))}</b></p>`}${fullHtml(q)}<button type="button" class="qz-go" data-a="next" id="qzNext">${last?"عرض النتيجة":"السؤال التالي"}</button></div>`;
    const p=body.querySelector("#qzPts");if(p)p.textContent=ar(Rn.score);
    setTimeout(()=>{const n=body.querySelector("#qzNext");if(n){n.focus({preventScroll:true});n.scrollIntoView({block:"nearest",behavior:"smooth"})}},60)}
  function hint(){
    if(Rn.done||!Rn.hints||Rn.hintUsed)return;const q=Rn.qs[Rn.i];Rn.hints--;Rn.hintUsed=true;
    const wrong=shuf([0,1,2,3].filter(k=>k!==q.ans)).slice(0,2);
    body.querySelectorAll(".qz-o").forEach((b,k)=>{if(wrong.includes(k)){b.disabled=true;b.classList.add("gone")}});
    const h=body.querySelector(".qz-hint");h.disabled=true;h.querySelector("span").textContent=ar(Rn.hints)}
  function vResult(){
    scr="result";clr();const n=Rn.qs.length,pct=Math.round(Rn.ok/n*100),b=badgeOf(pct),prev=bestGet(G.lv),rec=Rn.score>prev&&prev>0;
    if(Rn.score>prev)bestSet(G.lv,Rn.score);
    Rn.res={score:Rn.score,ok:Rn.ok,n,badge:b[1],pct};
    const wr=Rn.log.filter(x=>!x.good),C=2*Math.PI*52;
    body.innerHTML=head("النتيجة","",true)+`<div class="qz-res"><div class="qz-ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="52" class="bg"/><circle cx="60" cy="60" r="52" class="fg" stroke-dasharray="${C}" stroke-dashoffset="${C*(1-pct/100)}" transform="rotate(-90 60 60)"/></svg><div><b>${ar(Rn.ok)}/${ar(n)}</b><small>${ar(pct)}٪</small></div></div>
      <div class="qz-badge">${svg("star",22)}<b>${b[1]}</b></div><p class="qz-bm">${b[2]}</p>
      <div class="qz-kpis"><div><b>${ar(Rn.score)}</b><span>نقطة</span></div><div><b>${ar(Rn.bestStreak)}</b><span>أطول سلسلة</span></div><div><b>${ar(prev>Rn.score?prev:Rn.score)}</b><span>أفضل نتيجة (${LV[G.lv].n})</span></div></div>
      ${rec?`<div class="qz-rec">رقم قياسي جديد لك في المستوى ${LV[G.lv].n}!</div>`:""}
      <div class="qz-acts"><button type="button" class="qz-go" data-a="again">لعبة جديدة</button><button type="button" class="qz-sec2" data-a="share">شارك نتيجتك</button><button type="button" class="qz-sec2" data-a="setup">تغيير الإعدادات</button></div>
      ${wr.length?`<h3 class="qz-rh">راجع ما أخطأت فيه (${ar(wr.length)})</h3><div class="qz-rv">${wr.map(x=>`<details><summary><span>${TYPES[x.q.type]} · ${x.q.ref}</span></summary><div class="qz-in">${fullHtml(x.q)}<p class="qz-s">${x.pick<0?"لم تُجب في الوقت المحدد.":"اخترت: <span lang=\"ar\">"+esc(x.q.choices[x.pick].slice(0,120))+"</span>"}</p></div></details>`).join("")}</div>`:`<p class="qz-bm">لا أخطاء، ما شاء الله! جرّب مستوى أعلى.</p>`}`}
  function start(){
    const q=makeQuiz({juz:G.juz,n:G.n,lv:G.lv,types:G.types});
    if(q.err||!q.qs.length){vSetup("عدد الآيات في الأجزاء المختارة قليل، اختر جزءًا إضافيًا.");return}
    Rn={qs:q.qs,i:0,score:0,ok:0,streak:0,bestStreak:0,hints:3,log:[]};persist();vQ()}
  async function go(){
    const b=body.querySelector(".qz-go");b.disabled=true;b.textContent="جارٍ تجهيز الأسئلة…";
    try{await load()}catch(e){vSetup(e.message==="nodecomp"?"متصفحك لا يدعم تحميل اللعبة، حدّثه أو جرّب متصفحًا آخر.":"تعذّر تحميل نص المصحف. أعد تحميل الصفحة.");return}
    start()}
  function close(){if(!dlg)return;clr();dlg.hidden=true;document.documentElement.style.overflow="";if(lastFocus&&lastFocus.focus)lastFocus.focus()}
  function onClick(e){
    const t=e.target;if(t===dlg){if(scr!=="quiz")close();return}
    const b=t.closest("button");if(!b)return;
    if(b.dataset.lv){G.lv=b.dataset.lv;persist();vSetup();return}
    if(b.dataset.n){G.n=+b.dataset.n;persist();vSetup();return}
    if(b.dataset.j){const j=+b.dataset.j;G.juz=G.juz.includes(j)?G.juz.filter(x=>x!==j):G.juz.concat(j);persist();vSetup();return}
    if(b.dataset.pre){const p=b.dataset.pre;G.juz=p==="all"?Array.from({length:30},(_,i)=>i+1):p==="amma"?[30]:p==="last5"?[26,27,28,29,30]:[];persist();vSetup();return}
    if(b.dataset.t){const k=b.dataset.t;G.types=G.types.includes(k)?G.types.filter(x=>x!==k):G.types.concat(k);persist();vSetup();return}
    if(b.dataset.o!==undefined){answer(+b.dataset.o);return}
    const a=b.dataset.a;
    if(a==="close")close();
    else if(a==="start")go();
    else if(a==="next"){if(Rn.i>=Rn.qs.length-1)vResult();else{Rn.i++;vQ();dlg.querySelector(".qz-box").scrollTop=0}}
    else if(a==="hint")hint();
    else if(a==="exit"){const c=body.querySelector("#qzExit");c.innerHTML=`<div class="qz-conf">إنهاء الاختبار الآن؟ <button type="button" data-a="yes">إنهاء</button><button type="button" data-a="no">متابعة</button></div>`;c.querySelector("button").focus()}
    else if(a==="yes"){clr();vResult_or_setup()}
    else if(a==="no"){body.querySelector("#qzExit").innerHTML=""}
    else if(a==="again"){start()}
    else if(a==="setup")vSetup();
    else if(a==="share"){if(window.Q29Share)window.Q29Share.open({quiz:Rn.res})}}
  function vResult_or_setup(){if(Rn&&Rn.log.length){Rn.qs=Rn.qs.slice(0,Rn.log.length);vResult()}else vSetup()}
  function build_dlg(){
    dlg=document.createElement("div");dlg.className="qz-dlg";dlg.hidden=true;dlg.setAttribute("role","dialog");dlg.setAttribute("aria-modal","true");dlg.setAttribute("aria-label","اختبر حفظي");
    dlg.innerHTML=`<div class="qz-box"><div id="qzBody"></div></div>`;document.body.appendChild(dlg);body=dlg.querySelector("#qzBody");
    dlg.addEventListener("click",onClick);
    dlg.addEventListener("change",e=>{if(e.target.id==="qzTm"){G.timer=e.target.checked;persist()}});
    document.addEventListener("keydown",e=>{const sh=document.querySelector(".sh-dlg");if(!dlg||dlg.hidden||(sh&&!sh.hidden))return;
      if(e.key==="Escape"){if(scr==="quiz"){const c=body.querySelector("#qzExit");if(c&&!c.innerHTML){e.preventDefault();body.querySelector("[data-a=exit]").click()}}else close();return}
      if(scr==="quiz"&&/^[1-4]$/.test(e.key)&&!Rn.done&&!e.ctrlKey&&!e.metaKey){const b=body.querySelector('[data-o="'+(+e.key-1)+'"]');if(b&&!b.disabled)b.click();return}
      if(e.key==="Tab"){const f=[...dlg.querySelectorAll("button:not([disabled]),input")].filter(x=>x.offsetParent!==null);if(!f.length)return;const a=f[0],z=f[f.length-1];if(e.shiftKey&&document.activeElement===a){e.preventDefault();z.focus()}else if(!e.shiftKey&&document.activeElement===z){e.preventDefault();a.focus()}}})}
  function open(){lastFocus=document.activeElement;if(!dlg)build_dlg();dlg.hidden=false;document.documentElement.style.overflow="hidden";vSetup();dlg.querySelector(".qz-box").scrollTop=0;load().catch(()=>{});setTimeout(()=>{const f=dlg.querySelector(".qz-x");if(f)f.focus()},30)}
  document.addEventListener("click",e=>{if(e.target.closest("[data-qz-open]")){e.preventDefault();open()}});
  window.Q29Game={open,_t:{load,build,makeQuiz,G,state:()=>Rn}};
