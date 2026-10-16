// Layout regression check for the scroll scene: no photo/card/caption overlaps at 11 screen sizes and 7 scroll stages.
// Usage: cd frontend && node e2e/layout-overlap.mjs [baseUrl]   (needs the app running; exits non-zero on overlap)
import { webkit } from "playwright";
const sizes=[[390,844],[390,664],[360,640],[430,932],[768,1024],[820,1180],[1024,768],[1280,720],[1440,900],[1536,864],[1920,1080]];
const b=await webkit.launch(); let bad=0;
const hit=(a,c)=>!(a.right<=c.left+1||c.right<=a.left+1||a.bottom<=c.top+1||c.bottom<=a.top+1);
for(const [w,h] of sizes){
  const p=await (await b.newContext({viewport:{width:w,height:h},isMobile:w<600,hasTouch:w<600})).newPage();
  await p.goto(`${process.argv[2] ?? "http://localhost:3100"}/`,{waitUntil:"networkidle"});
  const info=await p.evaluate(()=>{const s=document.querySelector('.tf');const r=s.getBoundingClientRect();return {top:r.top+scrollY,h:r.height};});
  const out=[];
  for(const prog of [0.05,0.2,0.4,0.5,0.6,0.8,0.86]){
    await p.evaluate(([t,hh,pp])=>scrollTo(0,t+(hh-innerHeight)*pp),[info.top,info.h,prog]); await p.waitForTimeout(350);
    const r=await p.evaluate(()=>{const q=(sel)=>[...document.querySelectorAll(sel)].map(e=>{const b=e.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,op:+getComputedStyle(e.closest('.tf-tile,.tf-list,.tf-out')||e).opacity,t:(e.textContent||'').slice(0,18)}});
      const ph=q('.tf-ph')[0]; const cap=[...document.querySelectorAll('.tf-caption > div')].map(e=>{const b=e.querySelector('.tf-cap').getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,op:+getComputedStyle(e).opacity}}).filter(c=>c.op>0.5);
      return {ph, cap, tiles:q('.tf-tile .panel'), list:q('.tf-list .panel'), out:q('.tf-out .panel')};});
    const vis=(a)=>a.filter(x=>x.op>0.5);
    const issues=[];
    if(r.ph){ for(const c of r.cap) if(hit(r.ph,c)) issues.push('photo/caption');
      for(const t of vis(r.tiles)) if(hit(r.ph,t)) issues.push('photo/tile:'+t.t);
      for(const t of vis(r.list)) if(hit(r.ph,t)) issues.push('photo/list');
      if(prog>=0.05&&prog<=0.2){ /* phase A: outer cards intentionally float around the photo */ }
    }
    for(const t of vis(r.tiles)) for(const c of r.cap) if(hit(t,c)) issues.push('tile/caption');
    for(const t of vis(r.list)) for(const c of r.cap) if(hit(t,c)) issues.push('list/caption');
    if(issues.length){bad++; out.push(`  p=${prog}: ${[...new Set(issues)].join(', ')}`);}
  }
  console.log(`${w}x${h}`, out.length?'\n'+out.join('\n'):'ok');
}
console.log(bad ? `${bad} problem spots` : "no overlaps found"); await b.close(); process.exit(bad ? 1 : 0);
