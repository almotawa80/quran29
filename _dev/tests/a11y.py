import sys, os, json
from playwright.sync_api import sync_playwright
PATH="file://"+os.path.abspath(sys.argv[1] if len(sys.argv)>1 else "index.html")
JS=r"""(rootSel)=>{
const root=rootSel==='SHADOW'?document.querySelector('.pt-host').shadowRoot:document;
function parse(c){const m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[ ,\/]+/).map(Number);return{r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}}
function lum(c){const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)}
function blend(f,b){return{r:f.r*f.a+b.r*(1-f.a),g:f.g*f.a+b.g*(1-f.a),b:f.b*f.a+b.b*(1-f.a),a:1}}
function bgOf(el){let stack=[];let e=el;while(e){const cs=getComputedStyle(e);const c=parse(cs.backgroundColor);if(c&&c.a>0){stack.push(c);if(c.a>=1)break}
 e=e.parentElement||(e.getRootNode&&e.getRootNode().host)||null}
 let base={r:255,g:255,b:255,a:1};if(!stack.length||stack[stack.length-1].a<1){const bg=parse(getComputedStyle(document.body).backgroundColor);if(bg&&bg.a>0)base=bg}
 for(let i=stack.length-1;i>=0;i--){base=stack[i].a>=1?stack[i]:blend(stack[i],base)}return base}
const out={};const all=root.querySelectorAll('*');
for(const el of all){
 if(!el.offsetParent&&getComputedStyle(el).position!=='fixed')continue;
 const t=[...el.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim().length>1);if(!t.length)continue;
 const cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.opacity==='0')continue;
 let fg=parse(cs.color);if(!fg)continue;const bg=bgOf(el);fg=blend({...fg,a:fg.a*parseFloat(cs.opacity)},bg);
 const L1=lum(fg),L2=lum(bg);const cr=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 const px=parseFloat(cs.fontSize),bold=parseInt(cs.fontWeight)>=700;const large=px>=24||(px>=18.66&&bold);
 const need=large?3:4.5;if(cr<need){
  const k=cs.color+'|'+`rgb(${bg.r|0},${bg.g|0},${bg.b|0})`+'|'+px;
  if(!out[k])out[k]={fg:cs.color,bg:`rgb(${bg.r|0},${bg.g|0},${bg.b|0})`,cr:+cr.toFixed(2),px,n:0,ex:''};out[k].n++;if(!out[k].ex)out[k].ex=(el.className||el.tagName)+': '+t[0].textContent.trim().slice(0,30)}
}
return Object.values(out).sort((a,b)=>b.n-a.n)}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for scheme in ("light","dark"):
        ctx=b.new_context(viewport={"width":390,"height":900},color_scheme=scheme)
        pg=ctx.new_page();pg.route("**/*",lambda r:r.abort() if r.request.url.startswith("http") else r.continue_());pg.set_default_timeout(3000);pg.goto(PATH,wait_until="domcontentloaded");pg.wait_for_timeout(500)
        res={}
        tabs=pg.evaluate("[...document.querySelectorAll('nav button,.tabbar button,[data-v]')].map(e=>e.dataset.v||e.id||e.innerText.slice(0,10))")
        def scan(label,root="DOC"):
            r=pg.evaluate(JS,root)
            for x in r:res.setdefault(label,[]).append(x)
        scan("home")
        n=pg.evaluate("document.querySelectorAll('.tabbar button,nav.tabs button,#tabs button').length")
        print(scheme,"tabs",n)
        for i in range(n):
            pg.evaluate("i=>{const b=[...document.querySelectorAll('.tabbar button,nav.tabs button,#tabs button')][i];b&&b.click()}",i);pg.wait_for_timeout(250);scan("tab%d"%i)
        # portal
        try:
            pg.click("#coordBtn");pg.fill("#lgU","huda");pg.fill("#lgP","huda123");pg.click("#lgGo");pg.wait_for_timeout(500)
            scan("portal","SHADOW")
            pg.evaluate("document.querySelector('.pt-host').shadowRoot.querySelector('#add').click()");pg.wait_for_timeout(300);scan("portal-form","SHADOW")
        except Exception as e:print("portal err",e)
        print("=====",scheme)
        agg={}
        for lab,l in res.items():
            for x in l:
                k=(x['fg'],x['bg'],x['px']);a=agg.setdefault(k,dict(x,labs=set(),n=0));a['labs'].add(lab);a['n']+=x['n']
        for a in sorted(agg.values(),key=lambda x:-x['n'])[:25]:print(a['cr'],a['fg'],'on',a['bg'],a['px'],'px n=',a['n'],'|',a['ex'],'|',sorted(a['labs'])[:3])
        ctx.close()
