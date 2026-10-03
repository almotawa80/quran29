// Offline support for the guide (GitHub Pages copy only; copied to the repo root as sw.js).
// Pages: network first, so every visit online gets the latest build; offline falls back to the saved copy.
// Files (data, Quran font, icons): saved copy first, refreshed in the background.
// Other sites (Google fonts, the entities portal database) are left to the browser.
const CACHE="q29-v1";
const CORE=["./","manifest.webmanifest","qz-data.txt?v=18","hafs.woff2?v=18","icon-192.png","icon-512.png","apple-touch-icon.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>Promise.all(CORE.map(u=>c.add(u).catch(()=>{})))).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("q29-")&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  if(new URL(r.url).origin!==self.location.origin)return;
  if(r.mode==="navigate"){
    e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(CACHE).then(c=>c.put("./",cp))}return res}).catch(()=>caches.match("./",{ignoreSearch:true})));
    return;
  }
  e.respondWith(caches.open(CACHE).then(c=>c.match(r).then(hit=>{
    const net=fetch(r).then(res=>{if(res.ok)c.put(r,res.clone());return res}).catch(()=>hit);
    if(hit){e.waitUntil(net.catch(()=>{}));return hit}
    return net;
  })));
});
