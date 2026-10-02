# Build the GitHub deploy set: index.html without the game's Quran data and font (loaded on demand),
# plus qz-data.txt and hafs.woff2 next to it.
import re,sys,base64,os
src,out=sys.argv[1],sys.argv[2];os.makedirs(out,exist_ok=True)
s=open(src,encoding="utf-8").read()
m=re.search(r'\n?<script type="text/plain" id="qzdata">(.*?)</script>',s,re.S);assert m
open(os.path.join(out,"qz-data.txt"),"w").write(m.group(1).strip());s=s[:m.start()]+s[m.end():]
f=re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)',s);assert f
open(os.path.join(out,"hafs.woff2"),"wb").write(base64.b64decode(f.group(1)));s=s[:f.start()]+'url("hafs.woff2?v=18")'+s[f.end():]
open(os.path.join(out,"index.html"),"w",encoding="utf-8").write(s)
for n in ("index.html","qz-data.txt","hafs.woff2"):print(n,os.path.getsize(os.path.join(out,n))//1024,"KB")
