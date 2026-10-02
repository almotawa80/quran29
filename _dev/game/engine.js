  // ---------- data + question engine ----------
  const MARK=/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
  const sk=t=>t.replace(MARK,"").replace(/[ٱأإآ]/g,"ا").replace(/ى/g,"ي");
  const JUZ=[[1,1],[2,142],[2,253],[3,92],[4,24],[4,148],[5,82],[6,111],[7,88],[8,41],[9,94],[11,6],[12,53],[15,1],[17,1],[18,75],[21,1],[23,1],[25,21],[27,56],[29,46],[33,31],[36,28],[39,32],[41,47],[46,1],[51,31],[58,1],[67,1],[78,1]];
  const R=n=>Math.floor(Math.random()*n),pick=a=>a[R(a.length)];
  const shuf=a=>{a=a.slice();for(let i=a.length-1;i>0;i--){const j=R(i+1);[a[i],a[j]]=[a[j],a[i]]}return a};
  const LV={easy:{n:"سهل",max:13,nx:14,sx:16,base:10,d:"آيات قصيرة وخيارات متباعدة"},medium:{n:"متوسط",max:24,nx:24,sx:28,base:15,d:"خيارات قريبة من السورة نفسها"},hard:{n:"صعب",max:70,nx:45,sx:60,base:20,d:"متشابهات لفظية تحتاج إتقانًا"}};
  const TYPES={complete:"أكمل الآية",next:"الآية التالية",surah:"من أي سورة؟",word:"الكلمة الناقصة"};
  let D=null;
  function build(j){
    const A=[],sStart=[];
    j.a.forEach((arr,si)=>{sStart.push(A.length);arr.forEach((t,ai)=>{const w=t.split(" "),kw=w.map(sk);A.push({i:A.length,s:si+1,a:ai+1,t,w,kw,k:kw.join(" ")})})});
    const cnt=new Map(),inv=new Map(),vocab=new Map();
    A.forEach(x=>{cnt.set(x.k,(cnt.get(x.k)||0)+1);new Set(x.kw).forEach(w=>{let l=inv.get(w);if(!l)inv.set(w,l=[]);l.push(x.i)});x.w.forEach((w,p)=>{const k=x.kw[p];if(!vocab.has(k))vocab.set(k,w)})});
    const juzOf=new Array(A.length);let cur=0;const starts=JUZ.map(([s,a])=>sStart[s-1]+a-1);
    for(let i=0;i<A.length;i++){while(cur<29&&i>=starts[cur+1])cur++;juzOf[i]=cur+1}
    const lens=[...vocab.keys()];
    D={A,names:j.n,sStart,cnt,inv,vocab,juzOf,starts,lens,N:A.length};
    return D}
  async function load(){
    if(D)return D;
    const el=document.getElementById("qzdata");if(!el)throw new Error("nodata");
    if(typeof DecompressionStream==="undefined")throw new Error("nodecomp");
    const b=atob(el.textContent.trim()),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);
    const txt=await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("gzip"))).text();
    return build(JSON.parse(txt))}
  function similar(i,n){
    const x=D.A[i],sc=new Map();
    new Set(x.kw).forEach(w=>{const l=D.inv.get(w);if(!l||l.length>500)return;const wt=Math.log(D.N/l.length);l.forEach(j=>{if(j!==i)sc.set(j,(sc.get(j)||0)+wt)})});
    return [...sc.entries()].filter(([j])=>D.A[j].k!==x.k).sort((a,b)=>b[1]-a[1]).slice(0,n).map(e=>e[0])}
  const poolOf=juz=>{const s=new Set(juz);const p=[];for(let i=0;i<D.N;i++)if(s.has(D.juzOf[i]))p.push(i);return p};
  const ref=x=>"سورة "+D.names[x.s-1]+" · الآية "+x.a;
  const tail=(b,len)=>{len=Math.max(2,Math.min(len,b.w.length-2));return {t:b.w.slice(b.w.length-len).join(" "),k:b.kw.slice(b.kw.length-len).join(" ")}};
  function uniq(list,keyf,n){const seen=new Set(),o=[];for(const x of list){const k=keyf(x);if(seen.has(k))continue;seen.add(k);o.push(x);if(o.length>=n)break}return o}
  function mk(type,lv,stem,choices,ans,x,extra){return Object.assign({type,lv,stem,choices:choices.map(c=>c.t),ans,s:x.s,a:x.a,ref:ref(x),full:x.t},extra||{})}
  const rnd=(n,f)=>{const o=[];for(let k=0;k<n;k++)o.push(f())};
  function gComplete(pool,lv){
    const P=LV[lv];
    for(let tr=0;tr<80;tr++){
      const x=D.A[pick(pool)],wc=x.w.length;if(wc<6||wc>P.max)continue;
      let cut=Math.max(3,Math.round(wc*(lv==="hard"?0.4:0.5))),ok=false;
      for(;cut<=wc-2;cut++){const pk=x.kw.slice(0,cut).join(" ")+" ";let amb=false;for(let j=0;j<D.N;j++){if(j!==x.i&&(D.A[j].k+" ").startsWith(pk)){amb=true;break}}if(!amb){ok=true;break}}
      if(!ok)continue;
      const len=wc-cut,cor={t:x.w.slice(cut).join(" "),k:x.kw.slice(cut).join(" ")};
      let cand=[];
      if(lv==="hard")similar(x.i,14).forEach(j=>cand.push(D.A[j]));
      if(lv==="medium"){for(let j=D.sStart[x.s-1];j<(D.sStart[x.s]||D.N);j++)if(j!==x.i)cand.push(D.A[j]);cand=shuf(cand).slice(0,30)}
      const rest=[];for(let q=0;q<60;q++)rest.push(D.A[R(D.N)]);
      cand=cand.concat(rest).filter(b=>b.i!==x.i&&b.w.length>=len+2||b.i!==x.i&&b.w.length>=4);
      const opts=[];const seen=new Set([cor.k]);
      for(const b of cand){const t=tail(b,len);if(seen.has(t.k))continue;seen.add(t.k);opts.push(t);if(opts.length>=3)break}
      if(opts.length<3)continue;
      const all=shuf([cor].concat(opts));
      return mk("complete",lv,x.w.slice(0,cut).join(" "),all,all.indexOf(cor),x,{cut,done:cor.t})}
    return null}
  function gNext(pool,lv){
    const P=LV[lv];
    for(let tr=0;tr<80;tr++){
      const i=pick(pool),x=D.A[i],n=D.A[i+1];if(!n||n.s!==x.s)continue;
      if(x.w.length<4||x.w.length>P.sx||n.w.length>P.nx||n.w.length<3)continue;
      if(D.cnt.get(x.k)!==1)continue;
      let cand=[];
      if(lv==="hard"){similar(i,12).forEach(j=>{const nn=D.A[j+1];if(nn)cand.push(nn)});similar(i+1,8).forEach(j=>cand.push(D.A[j]))}
      if(lv==="medium"){for(let j=D.sStart[x.s-1];j<(D.sStart[x.s]||D.N);j++)if(Math.abs(j-i)>1)cand.push(D.A[j]);cand=shuf(cand)}
      for(let q=0;q<80;q++)cand.push(D.A[R(D.N)]);
      const seen=new Set([n.k,x.k]),opts=[];
      for(const b of cand){if(seen.has(b.k)||b.i===n.i||b.i===x.i)continue;if(b.w.length>P.nx+4||Math.abs(b.w.length-n.w.length)>(lv==="easy"?4:8))continue;seen.add(b.k);opts.push({t:b.t,k:b.k});if(opts.length>=3)break}
      if(opts.length<3)continue;
      const cor={t:n.t,k:n.k},all=shuf([cor].concat(opts));
      return mk("next",lv,x.t,all,all.indexOf(cor),x,{nextRef:ref(n),nextT:n.t})}
    return null}
  function gSurah(pool,lv){
    const P=LV[lv];
    for(let tr=0;tr<80;tr++){
      const x=D.A[pick(pool)];if(x.w.length<5||x.w.length>P.sx||D.cnt.get(x.k)!==1)continue;
      let nums=[];
      if(lv==="hard"){similar(x.i,20).forEach(j=>nums.push(D.A[j].s));for(let d=-3;d<=3;d++)nums.push(x.s+d)}
      else if(lv==="medium"){for(let d=-10;d<=10;d++)nums.push(x.s+d)}
      nums=shuf(nums.filter(n=>n>=1&&n<=114&&n!==x.s));
      for(let q=0;q<40;q++)nums.push(1+R(114));
      const seen=new Set([x.s]),opts=[];
      for(const n of nums){if(seen.has(n)||n<1||n>114)continue;seen.add(n);opts.push({t:"سورة "+D.names[n-1],n});if(opts.length>=3)break}
      const cor={t:"سورة "+D.names[x.s-1],n:x.s},all=shuf([cor].concat(opts));
      return mk("surah",lv,x.t,all,all.indexOf(cor),x,{})}
    return null}
  function lev(a,b,mx){if(Math.abs(a.length-b.length)>mx)return 9;const m=a.length,n=b.length;let p=new Array(n+1),c;for(let j=0;j<=n;j++)p[j]=j;for(let i=1;i<=m;i++){c=[i];let lo=i;for(let j=1;j<=n;j++){const v=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));c[j]=v;if(v<lo)lo=v}if(lo>mx)return 9;p=c}return p[n]}
  function gWord(pool,lv){
    const P=LV[lv];
    for(let tr=0;tr<80;tr++){
      const x=D.A[pick(pool)],wc=x.w.length;if(wc<5||wc>P.max||D.cnt.get(x.k)!==1)continue;
      const idx=[];for(let p=1;p<wc;p++)if(x.kw[p].length>=3)idx.push(p);if(!idx.length)continue;
      const p=pick(idx),target=x.kw[p],surf=x.w[p];
      const valid=w=>{if(w===target)return false;const nk=x.kw.slice();nk[p]=w;return !D.cnt.has(nk.join(" "))};
      let keys=[];
      if(lv==="hard"){for(const k of D.lens){if(k!==target&&lev(k,target,2)<=2)keys.push(k)}keys=shuf(keys).slice(0,40)}
      else if(lv==="medium"){for(let j=D.sStart[x.s-1];j<(D.sStart[x.s]||D.N);j++)D.A[j].kw.forEach(k=>{if(Math.abs(k.length-target.length)<=1)keys.push(k)});keys=shuf(keys)}
      for(let q=0;q<200&&keys.length<80;q++){const k=D.lens[R(D.lens.length)];if(lv==="easy"?Math.abs(k.length-target.length)<=2:true)keys.push(k)}
      const seen=new Set([target]),opts=[];
      for(const k of keys){if(seen.has(k)||!valid(k))continue;seen.add(k);opts.push({t:D.vocab.get(k)});if(opts.length>=3)break}
      if(opts.length<3)continue;
      const cor={t:surf},all=shuf([cor].concat(opts)),ws=x.w.slice();ws[p]="ـــــــ";
      return mk("word",lv,ws.join(" "),all,all.indexOf(cor),x,{pos:p})}
    return null}
  const GEN={complete:gComplete,next:gNext,surah:gSurah,word:gWord};
  function makeQuiz(o){
    load_ok();
    const pool=poolOf(o.juz);if(pool.length<20)return {err:"pool"};
    const types=o.types.length?o.types:Object.keys(TYPES),qs=[],used=new Set();
    const order=[];while(order.length<o.n){shuf(types).forEach(t=>order.length<o.n&&order.push(t))}
    for(const t of order){
      let q=null;
      for(let tr=0;tr<12&&!q;tr++){const c=GEN[t](pool,o.lv);if(c&&!used.has(c.s+":"+c.a)){q=c}}
      if(!q){for(const t2 of shuf(types)){for(let tr=0;tr<12&&!q;tr++){const c=GEN[t2](pool,o.lv);if(c&&!used.has(c.s+":"+c.a))q=c}if(q)break}}
      if(!q){for(const t2 of Object.keys(TYPES)){const c=GEN[t2](pool,"easy");if(c&&!used.has(c.s+":"+c.a)){q=c;break}}}
      if(!q)continue;used.add(q.s+":"+q.a);qs.push(q)}
    return {qs}}
  function load_ok(){if(!D)throw new Error("noload")}
