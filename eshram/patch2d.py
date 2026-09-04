"""Derive eshram.html from index.html's 2D engine per the design spec (anchored patches).
Each rep() asserts its anchor; failures are listed and the build stops."""
import re, json, sys
src=open("index.html").read(); h=src; ok=[]; bad=[]
def rep(tag,o,w,count=1):
    global h
    if o not in h: bad.append(tag); return
    h=h.replace(o,w,count); ok.append(tag)

# ---- page copy
rep("title","<title>Concrete Constellation</title>","<title>eShram Constellation</title>")
rep("eyebrow","Pahl&#233; India Foundation &#183; Sentiment Engineering","Pahl&#233; India Foundation &#183; eShram")
rep("h1","<h1>Concrete Constellation</h1>","<h1>eShram Constellation</h1>")
i=h.find('<div class="sub"><b>18,066 articles</b>'); j=h.find('</div>',i)
if i>0: h=h[:i]+'<div class="sub"><b id="mastN"></b> registrations of unorganised workers on eShram, as a constellation: states are anchors, districts are discs sized by registrations, <b>every mote is 10,000 people</b>, state-calibrated to the dashboard\'s <b id="mastCal"></b> distinct UANs. The belt is the difference.</div>'+h[j+6:]; ok.append("sub")
else: bad.append("sub")
rep("modeSeg",'<button data-mode="health" class="on" role="tab">Health</button><button data-mode="bucket" role="tab">Bucket</button><button data-mode="structure" role="tab">Structure</button>',
    '<button data-mode="women" class="on" role="tab">Women</button><button data-mode="work" role="tab">Work</button><button data-mode="literacy" role="tab">Literacy</button><button data-mode="corridors" role="tab">Corridors</button>')
rep("dockMain",'<span id="tdMain">Aug \'24 to Aug \'26 &#183; all 18,066</span>','<span id="tdMain">All trades</span>')
rep("dockSlider",'<input type="range" id="tdSlider" min="0" max="24" step="1" value="23" aria-label="Month">','<input type="range" id="tdSlider" min="0" max="6" step="1" value="0" aria-label="Trade group">')
rep("dockAvg",'<button id="tdAvg" class="on" title="24-month aggregate">&#931; 24-mo</button>','<button id="tdAvg" class="on" title="all trades">&#931; all</button>')
rep("satLabel",'<label class="tp-row"><input type="checkbox" id="fSat" checked> Satellites (44)</label>','<label class="tp-row"><input type="checkbox" id="fSat" checked> Districts</label>')
rep("dustLabel",'Article dust (18k)</label>','Motes (31,740)</label>')
rep("geoSlider",'<label class="tp-s">Node size <output>1.00</output>','<label class="tp-s">Map &#8596; force <output>1.00</output><input type="range" id="sGeo" min="0" max="1" step="0.05" value="1"></label>\n      <label class="tp-s">Node size <output>1.00</output>')
rep("textFadeDefault",'id="sFade" min="0.8" max="2.5" step="0.05" value="1.35"','id="sFade" min="1.0" max="3.0" step="0.05" value="1.6"')
rep("textFadeOut","Text fade <output>1.35</output>","Text fade <output>1.60</output>")

# ---- DATA payload
data=open("eshram/eshram_data.json").read()
i=h.index("const DATA = "); j=h.index(";\nconst REDUCED"); h=h[:i]+"const DATA = "+data+h[j:]; ok.append("data")

rep("topLevelHelpers","const REDUCED = ","const pct=v=>(v*100).toFixed(1)+'%';const GROUPS=DATA.axis,META=DATA.meta,TYPN=DATA.typ_names;\nconst REDUCED = ")
# ---- helpers: t-space, palettes
rep("healthColorDiv","const t=Math.max(-1,Math.min(1,v/0.7));","const t=Math.max(-1,Math.min(1,v));",2)
rep("hues","""const BUCKET_HUE={residential_realty:'#e18888',roads_highways:'#dc9064',epc_orders:'#c99d4e',
  policy_regulation:'#a9ab54',commercial_datacentre:'#7fb673',rail_metro:'#51bb9a',
  safety_legal:'#35b9c0',housing_credit:'#50b1dc',costs_macro:'#7ca5e9',
  airports_ports:'#a498e5',sector_macro:'#c38ecf',cement:'#d887ae'};""",
"""const WORK_RGB=DATA.work_hue.map(hex2rgb), AMBER=[240,180,41];
const litRGB=t=>toward([120,120,133],AMBER,Math.max(0,Math.min(1,t)));
const smallN=(c,n)=>n>=10000?c:n<1000?[120,120,133]:toward([120,120,133],c,(n-1000)/9000);
document.getElementById('mastN').textContent=DATA.total.toLocaleString();
document.getElementById('mastCal').textContent=(META.calibrated_total/1e6).toFixed(1)+'M';""")
rep("params","const P={nodeSize:1,linkWidth:1,textFade:1.35,repel:1,dist:1,center:1,satellites:true,simEdges:true,dust:true,dustDensity:1};",
    "const P={nodeSize:1,linkWidth:1,textFade:1.6,repel:1,dist:1,center:1,satellites:true,simEdges:true,dust:true,dustDensity:1,geo:1};")
rep("modeDefault","let colorMode='health', monthIdx=null;","let colorMode='women', monthIdx=null;")

# ---- nodes
rep("hubBuild","""  nodes.push({id:b.id,label:b.name,kind:'bucket',n:b.n,health:b.health,
    r:0.5*Math.sqrt(b.n), x:Math.cos(a)*260, y:Math.sin(a)*180, vx:0,vy:0});""",
"""  nodes.push({...b,label:b.name,kind:'bucket',r:5, x:b.gx, y:b.gy, fx:Math.cos(a)*260, fy:Math.sin(a)*180, vx:0,vy:0});""")
rep("clusterBuild","""  const node={id:c.id,label:c.terms[0]||('cluster '+c.cluster),kind:'cluster',
    n:c.n,health:c.health,terms:c.terms,parent:c.parent,
    r:0.5*Math.sqrt(c.n), x:p.x+Math.cos(a)*d, y:p.y+Math.sin(a)*d, vx:0,vy:0};""",
"""  const node={...c,label:c.terms[0],kind:'cluster', x:c.gx, y:c.gy, fx:p.fx+Math.cos(a)*d, fy:p.fy+Math.sin(a)*d, vx:0,vy:0};""")
rep("corridorLinks","""DATA.bucket_edges.filter(e=>e.sim>=0.78).forEach(e=>{
  links.push({s:nMap[e.a],t:nMap[e.b],kind:'sim',sim:e.sim,
    rest:150+(1-e.sim)*900,k:0.006});
});""",
"""DATA.bucket_edges.forEach(e=>{
  links.push({s:nMap[e.a],t:nMap[e.b],kind:'sim',w:e.w,n:e.n,back:e.back,forced:e.forced,rest:150+(1-e.w)*400,k:0.006});
});
const edgesIn=DATA.edges_in.map(e=>({s:nMap[e.a],t:nMap[e.b],n:e.n,w:e.w})).filter(e=>e.s&&e.t);""")
rep("nbrEdgesIn","links.forEach(l=>{nbr[l.s.id].add(l.t.id);nbr[l.t.id].add(l.s.id)});",
    "links.forEach(l=>{nbr[l.s.id].add(l.t.id);nbr[l.t.id].add(l.s.id)});\nedgesIn.forEach(e=>{nbr[e.s.id].add(e.t.id);nbr[e.t.id].add(e.s.id)});")
rep("simPartners","""const simPartners={};DATA.bucket_edges.forEach(e=>{
  (simPartners[e.a]=simPartners[e.a]||[]).push({id:e.b,sim:e.sim});
  (simPartners[e.b]=simPartners[e.b]||[]).push({id:e.a,sim:e.sim});});
for(const k in simPartners)simPartners[k].sort((a,b)=>b.sim-a.sim);""",
"""const simPartners={};""")

# ---- dust: radius cap in geo, spec sizes
rep("dustSpread","""    const base=parent.r+(key.startsWith('b:')?5:3);
    const spread=0.92*Math.sqrt(arr.length)+3;""",
"""    const base=parent.r+1.5;
    const kk=Math.min(0.92, (0.6*(parent.nn||40))/Math.sqrt(Math.max(arr.length,1)));
    const spread=(P.geo>0.5?kk:0.92)*Math.sqrt(arr.length)+2;""")
rep("dustSz","sz:1.4+Math.random()*1.0});","sz:1.2+Math.random()*0.8});")
# rEff must not include hub dust (hubs have none) -- unchanged logic works since no 'b:' keys

# ---- physics: skip at geo=1, blend toward geo targets
rep("tickHead","function tick(){\n  for(let i=0;i<nodes.length;i++){const a=nodes[i];",
    "function tick(){\n  if(P.geo>=1&&!dragN){nodes.forEach(n=>{n.x=n.gx;n.y=n.gy;});return;}\n  for(let i=0;i<nodes.length;i++){const a=nodes[i];")
rep("tickBlend","  alpha=Math.max(alpha*0.995,0.06);\n}","  if(P.geo>0){const g=P.geo;nodes.forEach(n=>{n.x=g*n.gx+(1-g)*n.x;n.y=g*n.gy+(1-g)*n.y;});}\n  alpha=Math.max(alpha*0.995,0.06);\n}")
rep("noDragInGeo","  moved=false;immersive(true);const n=pick(mx,my);\n  if(n){dragN=n;}","  moved=false;immersive(true);const n=(P.geo>=0.999)?null:pick(mx,my);\n  if(n){dragN=n;}")
rep("zoomClamp","const f=Math.exp(-e.deltaY*0.0012),ns=Math.min(4,Math.max(0.35,scale*f));","const f=Math.exp(-e.deltaY*0.0012),ns=Math.min(P.geo>0.5?8:4,Math.max(0.35,scale*f));")

# ---- colour resolution
rep("resolve","""  if(colorMode==='structure')return {rgb:STRUCT,hollow:false};
  if(colorMode==='bucket'){
    const key=n.kind==='bucket'?n.id:n.parent;
    return {rgb:lift(hex2rgb(BUCKET_HUE[key])),hollow:false};
  }
  if(monthIdx===null)return {rgb:lift(healthRGB(n.health)),hollow:false};
  const v=monthVal(n);
  if(!v||v[1]===0)return {rgb:MIDRGB,hollow:true};
  const [h,nn]=v, full=healthRGB(h);
  if(nn>=20)return {rgb:lift(full),hollow:false};
  if(nn<=5)return {rgb:MIDRGB,hollow:false};
  const sat=(nn-5)/15;
  return {rgb:lift(full.map((x,i)=>Math.round(lerp(MIDRGB[i],x,sat)))),hollow:false};""",
"""  if(colorMode==='corridors')return {rgb:STRUCT,hollow:false};
  if(colorMode==='literacy')return {rgb:lift(litRGB(n.litT)),hollow:false};
  if(colorMode==='work'){
    if(n.kind==='bucket')return {rgb:STRUCT,hollow:false};
    return n.typ<0?{rgb:MIDRGB,hollow:true}:{rgb:lift(WORK_RGB[DATA.typ_hue[n.typ]]),hollow:false};
  }
  if(monthIdx===null)return {rgb:lift(healthRGB(n.health)),hollow:false};
  const v=monthVal(n);
  if(!v||v[1]===0)return {rgb:MIDRGB,hollow:true};
  return {rgb:lift(smallN(healthRGB(v[0]),v[1])),hollow:false};""")
rep("dustColorsHealth","    else if(colorMode==='bucket')c=null;               // resolved per group\n    else c=lift(healthRGB(n10/10));",
    "    else if(colorMode==='work')c=null;\n    else if(colorMode==='literacy'||colorMode==='corridors')c=null;\n    else c=lift(healthRGB(n10/10));")
rep("spriteColour","""  const bucketRGB=colorMode==='bucket'
    ?lift(hex2rgb(BUCKET_HUE[g.parent.kind==='bucket'?g.parent.id:g.parent.parent])):null;""",
"""  const parentRGB=(colorMode==='literacy'||colorMode==='corridors')?(g.parent.cur||STRUCT):null;""")
rep("spriteCol2","    const col=bucketRGB||dustColors.get(Math.round(d.net*10))||MIDRGB;",
    "    const col=colorMode==='work'?lift(WORK_RGB[d.mi]):(parentRGB||dustColors.get(Math.round(d.net*10))||MIDRGB);")
rep("spriteScrub","    if(monthIdx!==null&&colorMode==='health'){","    if(monthIdx!==null&&colorMode==='women'){")
rep("blitComp","  ctx.globalCompositeOperation='lighter';\n  dustGroups.forEach(g=>{","  ctx.globalCompositeOperation=P.geo>0.5?'source-over':'lighter';\n  dustGroups.forEach(g=>{")
rep("dockDim","  document.getElementById('timeDock').classList.toggle('dim',m!=='health');","  document.getElementById('timeDock').classList.toggle('dim',m!=='women');")
rep("dockGuard","function dockGuard(){if(colorMode!=='health')setMode('health');}","function dockGuard(){if(colorMode!=='women')setMode('women');}")
rep("tipScrubMode","  if(monthIdx===null||colorMode!=='health'){","  if(monthIdx===null||colorMode!=='women'){")
rep("panelScrubMode","  if(monthIdx!==null&&colorMode==='health'){","  if(monthIdx!==null&&colorMode==='women'){")
rep("legendHealth","  if(colorMode==='health'){","  if(colorMode==='women'){")
rep("legendBucket","  }else if(colorMode==='bucket'){","  }else if(colorMode==='work'){")
rep("glowStruct","const glowA=(colorMode==='structure'?0.10:0.30)*dim;","const glowA=(colorMode==='corridors'?0.10:0.30)*dim;")

# ---- edges: corridor gradient, forced dash, member edges in geo only on hover
rep("memberGeo","""  links.forEach(l=>{                                   // membership first (solid)
    if(l.kind!=='member')return;
    let a=0.28;""",
"""  links.forEach(l=>{                                   // membership first (solid)
    if(l.kind!=='member')return;
    if(P.geo>0.5&&!(active&&active.has(l.s.id)&&active.has(l.t.id)))return;
    let a=0.22;""")
rep("simEdges","""  ctx.setLineDash([3,5]);                              // similarity (dashed, alpha=weight)
  links.forEach(l=>{
    if(l.kind!=='sim'||!P.simEdges)return;
    let a=Math.min(0.60, 0.22+(l.sim-0.78)/0.111*0.38);
    if(active&&!(active.has(l.s.id)&&active.has(l.t.id)))a=0.05;
    if(searchQ&&!(match(l.s)||match(l.t)))a=0.04;
    const [x1,y1]=toScreen(l.s),[x2,y2]=toScreen(l.t);
    ctx.strokeStyle=`rgba(168,139,250,${a})`;ctx.lineWidth=1*P.linkWidth;
    ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
  });
  ctx.setLineDash([]);""",
"""  links.forEach(l=>{                                   // corridors: gradient = direction, width = log volume
    if(l.kind!=='sim'||!P.simEdges)return;
    let a=colorMode==='corridors'?0.55:0.22;
    if(active)a=(active.has(l.s.id)&&active.has(l.t.id))?0.8:0.05;
    if(searchQ&&!(match(l.s)||match(l.t)))a=0.04;
    const [x1,y1]=toScreen(l.s),[x2,y2]=toScreen(l.t);
    const two=Math.max(l.n,l.back||1)/Math.max(1,Math.min(l.n,l.back||l.n))<2;
    const gr=ctx.createLinearGradient(x1,y1,x2,y2);
    gr.addColorStop(0,`rgba(168,139,250,${two?a:a*0.25})`);gr.addColorStop(1,`rgba(168,139,250,${a})`);
    ctx.setLineDash(l.forced?[3,5]:[]);
    ctx.strokeStyle=gr;ctx.lineWidth=(0.6+1.6*l.w)*P.linkWidth;
    ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
  });
  ctx.setLineDash([]);
  if(focus&&focus.kind==='bucket'){                    // origin -> district corridors for the focused state
    edgesIn.forEach(e=>{ if(e.s!==focus)return;
      const [x1,y1]=toScreen(e.s),[x2,y2]=toScreen(e.t);
      const gr=ctx.createLinearGradient(x1,y1,x2,y2);gr.addColorStop(0,'rgba(168,139,250,.15)');gr.addColorStop(1,'rgba(168,139,250,.6)');
      ctx.strokeStyle=gr;ctx.lineWidth=(0.6+1.0*e.w)*P.linkWidth;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();});
  }""")
# flat fill under 5px: skip the body gradient too
rep("flatFill","""      const body=ctx.createRadialGradient(x-r*0.3,y-r*0.32,r*0.1,x,y,r);""",
"""      if(r<5){ctx.fillStyle=rgba(n.cur,dim);ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fill();}
      else{
      const body=ctx.createRadialGradient(x-r*0.3,y-r*0.32,r*0.1,x,y,r);""")
rep("flatFillEnd","""      ctx.strokeStyle=rgba(shade(n.cur,0.5),0.9*dim);
      ctx.lineWidth=Math.max(0.8,r*0.07);
      ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.stroke();""",
"""      ctx.strokeStyle=rgba(shade(n.cur,0.5),0.9*dim);
      ctx.lineWidth=Math.max(0.8,r*0.07);
      ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.stroke();
      }""")
# satellite labels: gate small districts until deeper zoom
rep("satLabels","""      labA=Math.max(0,Math.min(1,(scale-P.textFade)/0.35))*0.9*dim;
      if(n===focus||isHit)labA=Math.max(labA,0.9*dim);""",
"""      labA=Math.max(0,Math.min(1,(scale-P.textFade)/0.35))*0.9*dim;
      if(scale<P.textFade+1.0&&n.n<300000)labA=0;
      if(x<-40||x>W+40||y<-40||y>H+40)labA=0;
      if(n===focus||isHit)labA=Math.max(labA,0.9*dim);""")

rep("fitTight","  scale=Math.min(1.6,Math.min((W-leftGutter-70)/(2*ext),(H-160)/(2*ext)));\n  tx=leftGutter/2;ty=-18;","  scale=Math.min(1.6,Math.min((W-leftGutter-70)/(2*ext),(H-70)/(2*ext)));\n  tx=leftGutter/2;ty=-4;")
# ---- tune panel wiring: geo slider
rep("wireGeo","wireSlider('sSize','nodeSize');","wireSlider('sGeo','geo',1);document.getElementById('sGeo').addEventListener('input',()=>{invalidateSprites();});\nwireSlider('sSize','nodeSize');")

# ---- dock: trade groups instead of months
rep("flags","const FLAGS={0:'count inflated: crawl dates',18:'count inflated: crawl dates',24:'partial month: n=163'};",
    "const FLAGS={4:'0.9% of the registry: districts under 1,000 shown grey',6:'residual: Miscellaneous, Others, Not provided',2:'saturates teal by design (national 92.3%)'};")
rep("setIdxAll","""  if(i===null){tdMain.textContent="Aug '24 to Aug '26 \\u00b7 all 18,066";tdFlag.textContent='';}
  else{slider.value=i;
    tdMain.textContent=mLab(DATA.months[i]);
    tdFlag.textContent=FLAGS[i]||`n=${DATA.composite[i][2].toLocaleString()} articles`;}""",
"""  if(i===null){tdMain.textContent="All trades \\u00b7 "+DATA.total.toLocaleString()+" registrations";tdFlag.textContent='';}
  else{slider.value=i;const c=DATA.composite[i];
    tdMain.textContent=`${GROUPS[i]} \\u00b7 ${pct(c[2]/DATA.total)} of registrations \\u00b7 ${pct(c[3])} women`;
    tdFlag.textContent=FLAGS[i]||`n=${c[2].toLocaleString()}`;}""")
rep("playBound","  let i=(monthIdx===null||monthIdx>=23)?0:monthIdx;","  let i=(monthIdx===null||monthIdx>=GROUPS.length-1)?0:monthIdx;")
rep("playEnd","    i++;if(i>23){clearInterval(playT);playT=null;tdPlay.innerHTML='\\u25b6';return;}","    i++;if(i>GROUPS.length-1){clearInterval(playT);playT=null;tdPlay.innerHTML='\\u25b6';setIdx(null);return;}")
# dock spark -> 7 linear bars
i=h.find("function drawDockSpark(){"); j=h.find("requestAnimationFrame(drawDockSpark);")
if i>0 and j>i:
    h=h[:i]+"""function drawDockSpark(){
  const w=tdSpark.clientWidth||400,h=26,n=DATA.composite.length,gap=6,bw=(w-gap*(n-1))/n;
  let s='';
  DATA.composite.forEach((c,i)=>{const share=c[2]/DATA.total, bh=Math.max(1,share*(h-4)); const x=i*(bw+gap);
    s+=`<rect x="${x}" y="${h-bh}" width="${bw}" height="${bh}" fill="${healthColor(c[1])}" opacity="${monthIdx===null||monthIdx===i?.95:.45}" ${monthIdx===i?'stroke="#e9f0f5" stroke-width="1"':''}><title>${GROUPS[i]}: ${pct(share)} of registrations, ${pct(c[3])} women</title></rect>`;});
  tdSpark.innerHTML=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${s}</svg>`;
  tdSpark.querySelector('svg').onclick=e=>{const r=tdSpark.getBoundingClientRect();const i=Math.max(0,Math.min(n-1,Math.floor((e.clientX-r.left)/r.width*n)));dockGuard();setIdx(i);};
}
"""+h[j:]; ok.append("dockSpark")
else: bad.append("dockSpark")
rep("mLabIdentity","const mLab=m=>{","const mLab=m=>m;const _mLabOld=m=>{")

# ---- tooltip
i=h.find("function tipHTML(n){"); j=h.find("/* ---- detail panel v2 ---- */")
if i>0 and j>i:
    h=h[:i]+"""function tipHTML(n){
  const hub=n.kind==='bucket';
  const cls=hub?`state \\u00b7 ${n.n.toLocaleString()} registrations (calibrated) \\u00b7 ${n.nd} districts`
    :`district in ${bMap[n.parent].name} \\u00b7 ${n.n.toLocaleString()} registrations (dump ${n.n_raw.toLocaleString()}) \\u00b7 ${n.motes||0} motes`;
  let val='',cav='';
  if(colorMode==='women'){
    if(monthIdx===null)val=`<span style="color:${fmtRGB(n.health)}">${pct(n.fem)} women</span> of registrations`;
    else{const v=monthVal(n); if(!v||!v[1])val=`${GROUPS[monthIdx]}: no registrations`; else{val=`${GROUPS[monthIdx]}: <span style="color:${fmtRGB(v[0])}">${pct(v[2])} women</span> \\u00b7 n=${v[1].toLocaleString()}`; if(v[1]<1000)cav='n under 1,000: share unstable';}}
  }else if(colorMode==='work'){
    val=hub?'states carry no class':`top ${n.top3[0]?n.top3[0][0]+' '+pct(n.top3[0][1]):''}${n.typ>=0?` \\u00b7 specialises ${TYPN[n.typ]} (LQ ${n.lq})`:''}`;
    if(!hub&&n.typ<0)cav='not classified: below typology floor';
  }else if(colorMode==='literacy'){val=`<span style="color:${rgba(litRGB(n.litT),1)}">not literate ${pct(n.lit)}</span>`;}
  else{val=hub?`in ${n.in.toLocaleString()} \\u00b7 out ${n.out.toLocaleString()} \\u00b7 net ${n.net>0?'+':''}${n.net.toLocaleString()}`:`in-migrant share ${pct(n.mig)}`;}
  if(!cav&&!hub&&n.matched===false)cav='position: state centroid, no boundary match';
  if(!cav&&!hub&&n.n<10000)cav='small district';
  if(!cav&&hub&&n.factor<0.80)cav=`dump ${Math.round((1/n.factor-1)*100)}% above official`;
  return `<div class="t">${n.label}</div><div class="m">${cls}</div><div class="m">${val}</div>`+(cav?`<div class="m" style="color:var(--neg)">${cav}</div>`:'');
}

"""+h[j:]; ok.append("tip")
else: bad.append("tip")

# ---- panel
i=h.find("function openPanel(n){pinN=n;"); j=h.find("/* ---- colour-mode toggle ---- */")
if i>0 and j>i:
    h=h[:i]+"""function barStrip(vals,labels,ticks){const mx=Math.max(...vals,1e-9);
  return `<div style="display:flex;gap:4px;align-items:flex-end;height:44px;margin-top:6px">`+vals.map((v,i)=>`<div title="${labels[i]}: ${typeof ticks==='function'?ticks(v,i):pct(v)}" style="flex:1;background:${typeof ticks==='function'?healthColor((v-0.5)/0.17):'var(--accent)'};opacity:.85;height:${Math.max(2,v/mx*40)}px"></div>`).join('')+`</div><div style="display:flex;gap:4px;font-family:var(--mono);font-size:8.5px;color:var(--faint)">`+labels.map(l=>`<div style="flex:1;overflow:hidden;white-space:nowrap">${l}</div>`).join('')+`</div>`;}
function openPanel(n){pinN=n;
  clearTimeout(immersiveT);wrap.classList.remove('immersive');
  document.getElementById('tunePanel').classList.remove('open');
  document.getElementById('tuneBtn').classList.remove('on');
  const hub=n.kind==='bucket';
  const ser=hub?(DATA.series[n.id]||{}):(DATA.cluster_series[n.id]||{});
  const fem7=GROUPS.map(g=>ser[g]?ser[g][2]:0);
  let extra=`<div class="k2">Women by trade</div>`+barStrip(fem7,GROUPS.map(g=>g.split(' ')[0]),(v,i)=>pct(v)+' women');
  const A7=['<18','18-25','26-35','36-45','46-55','56-59','60+'], E5=['not literate','primary or less','middle','secondary','higher'];
  const a7=n.age7.reduce((s,v)=>s+v,0)||1, e5=n.edu5.reduce((s,v)=>s+v,0)||1;
  extra+=`<div class="k2">Age</div>`+barStrip(n.age7.map(v=>v/a7),A7)+`<div class="k2">Education</div>`+barStrip(n.edu5.map(v=>v/e5),E5);
  if(hub){
    extra+=`<div class="k2">Corridors out</div>`+(n.top_out||[]).map(([id,c])=>`<button class="prow" data-go="${id}">\\u2192 ${bMap[id]?bMap[id].name:id} \\u00b7 ${c.toLocaleString()}${c<2000?' \\u00b7 not drawn':''}</button>`).join('')
         +`<div class="k2">Corridors in</div>`+(n.top_in||[]).map(([id,c])=>`<button class="prow" data-go="${id}">\\u2190 ${bMap[id]?bMap[id].name:id} \\u00b7 ${c.toLocaleString()}${c<2000?' \\u00b7 not drawn':''}</button>`).join('')
         +`<div class="k2" style="margin-top:10px">distance elasticity \\u22120.86 \\u00b7 common language \\u00d71.67 \\u00b7 movers +5.4 pp more educated</div>`;
  }else{
    extra+=`<div class="k2">Top occupations</div><div class="terms" style="margin-top:6px">`+(n.top5||[]).map(([o,s,f])=>`<span>${o} ${pct(s)}${f!=null?' \\u00b7 '+pct(f)+' women':''}</span>`).join(' ')+`</div>`;
    if(n.origins&&n.origins.length)extra+=`<div class="k2">Top origin states</div>`+n.origins.map(([id,c])=>`<button class="prow" data-go="${id}">${bMap[id]?bMap[id].name:id} \\u00b7 ${c.toLocaleString()}</button>`).join('');
    extra+=`<button class="prow" data-go="${n.parent}">\\u2192 ${bMap[n.parent].name}</button>`;
  }
  const head=hub?`<span><b>${n.n.toLocaleString()}</b> registrations</span><span>factor ${n.factor}</span><span>net ${n.net>0?'+':''}${n.net.toLocaleString()}</span>`
    :`<span><b>${n.n.toLocaleString()}</b> registrations</span><span>${chipFor(n.health)} women ${pct(n.fem)}</span><span>${n.typ>=0?TYPN[n.typ]+' LQ '+n.lq:'unclassified'}</span>`;
  npb.innerHTML=`<div class="k">${hub?'State':'District \\u2192 '+bMap[n.parent].name}</div><h3>${n.label}</h3><div class="stats">${head}</div>${extra}`;
  npb.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{const t=nMap[b.dataset.go];if(t){openPanel(t);easeViewTo(t);}});
  panel.style.display='block';draw();
}

"""+h[j:]; ok.append("panel")
else: bad.append("panel")

# ---- legend
i=h.find("function renderLegend(){"); j=h.find("renderLegend();\nwindow.__dump")
if j<0: j=h.find("renderLegend();\n\n/* ---- keyboard ---- */")
if i>0 and j>i:
    h=h[:i]+"""function renderLegend(){
  const L=document.getElementById('legend'); let rows='';
  if(colorMode==='women'){
    rows+=`<div class="row"><span class="lg-scale"></span></div>
      <div class="row" style="width:120px;justify-content:space-between"><span>33%</span><span>50%</span><span>67%</span></div>
      <div class="row lg-cap">women among registrants \\u00b7 parity at 50% \\u00b7 India ${pct(META.national_fem)} \\u00b7 teal dot = 10,000 women, orange dot = 10,000 men \\u00b7 registrations, not the workforce${monthIdx!==null?' \\u00b7 grey = n under 1,000 \\u00b7 hollow = none':''}</div>`;
  }else if(colorMode==='work'){
    rows+=DATA.group_names.map((g,i)=>`<div class="row"><span class="lg-sw" style="background:${DATA.work_hue[i]}"></span> ${g} ${pct(DATA.composite[i][2]/DATA.total)}</div>`).join('')
      +`<div class="row lg-cap">disc = what the district does more than India does (LQ class) \\u00b7 dots = what its people actually do \\u00b7 hollow = not classified</div>`;
  }else if(colorMode==='literacy'){
    rows+=`<div class="row"><span class="lg-scale" style="background:linear-gradient(90deg,#787885,#f0b429)"></span></div>
      <div class="row" style="width:120px;justify-content:space-between"><span>3%</span><span></span><span>42%</span></div>
      <div class="row lg-cap">share not literate \\u00b7 India ${pct(META.national_lit)} \\u00b7 brighter = more not-literate \\u00b7 Moran I 0.73: expect blocks</div>`;
  }else{
    rows+=`<div class="row lg-cap">\\u25ac corridor \\u2265 2,000 movers \\u00b7 fades from sender, bright at receiver \\u00b7 width = log volume \\u00b7 ${pct(META.corridors_drawn_share)} of ${META.interstate_movers.toLocaleString()} inter-state registrations drawn \\u00b7 dashed = a state's top corridor under 2,000 \\u00b7 hover a state: its origin \\u2192 district corridors</div>`;
  }
  rows+=`<div class="row"><span style="font-size:8px;letter-spacing:2px">\\u2022\\u2022\\u2022</span> \\u00b7 = 10,000 registrations (state-calibrated) \\u00b7 ${(META.motes_f+META.motes_m).toLocaleString()} motes</div>
    <div class="row lg-cap">belt = ${DATA.belt.toLocaleString()} dots = ${((DATA.total-META.calibrated_total)/1e6).toFixed(1)}M dump rows above the dashboard's ${(META.calibrated_total/1e6).toFixed(1)}M distinct UANs: estimated duplicate mass, an upper bound</div>
    <div class="row"><span class="lg-dot" style="width:6px;height:6px"></span><span class="lg-dot" style="width:14px;height:14px"></span> disc area \\u221d registrations (districts only)</div>
    <div class="row"><span class="lg-ring"></span> ring = state anchor, unsized</div>`;
  if(P.geo>0)rows+=`<div class="row lg-cap">positions: 2024 LGD boundary centroids (${META.matched} of ${META.n_districts} matched), blended toward physics by the slider; not a map \\u00b7 zoom in for small-state labels</div>`;
  L.innerHTML=rows;
}
"""+h[j:]; ok.append("legend")
else: bad.append("legend")

# ---- observatory: replace <main> content and the CHARTS script block
i=h.find("<main>"); j=h.find("</main>")
if i>0 and j>i:
    h=h[:i]+"""<main>
  <section class="sec">
    <div class="eyebrow">Three reads</div>
    <h2>Trade sets the level, place sets the spread</h2>
    <p class="lede">The all-trades map spans roughly 44% to 67% women across districts. Scrub to Domestic &amp; care and the whole country turns teal (92% women); Construction &amp; mining turns it orange (27%). The within-trade spread lives in each district's panel.</p>
    <div id="chartGroups" class="chart"></div>
  </section>
  <section class="sec">
    <div class="eyebrow">States</div>
    <h2>Women among registrants, by state and trade</h2>
    <p class="lede">Each row is a state; columns are the seven trade groups; colour is the female share on the same parity scale as the graph. Grey means fewer than 1,000 registrations in that cell.</p>
    <div id="chartStates" class="chart"></div>
  </section>
  <section class="sec">
    <div class="eyebrow">Read this before citing</div>
    <h2>Caveats</h2>
    <ul class="caveats" id="caveats"></ul>
  </section>
  <footer class="foot" id="foot"></footer>
</main>"""+h[j+7:]; ok.append("main")
else: bad.append("main")
i=h.find("/* =================== CHARTS =================== */"); j=h.rfind("</script>")
if i>0 and j>i:
    h=h[:i]+"""/* =================== CHARTS (eShram) =================== */
(function(){
  const g=document.getElementById('chartGroups');
  let html='<table><thead><tr><th>trade group</th><th>registrations</th><th>share</th><th>women</th><th></th></tr></thead><tbody>';
  DATA.composite.forEach((c,i)=>{html+=`<tr><td><span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:${DATA.work_hue[i]};margin-right:6px"></span>${c[0]}</td><td>${c[2].toLocaleString()}</td><td>${pct(c[2]/DATA.total)}</td><td style="color:${healthColor(c[1])}">${pct(c[3])}</td><td><div style="height:8px;width:${Math.round(c[2]/DATA.total*300)}px;background:${healthColor(c[1])};border-radius:4px"></div></td></tr>`;});
  g.innerHTML=html+'</tbody></table>';
  const s=document.getElementById('chartStates');
  const hubs=[...DATA.buckets].sort((a,b)=>b.n-a.n);
  let t='<table><thead><tr><th>state</th><th>registrations</th>'+GROUPS.map(x=>`<th>${x}</th>`).join('')+'</tr></thead><tbody>';
  hubs.forEach(b=>{const ser=DATA.series[b.id]||{}; t+=`<tr><td>${b.name}</td><td>${b.n.toLocaleString()}</td>`+GROUPS.map(gn=>{const v=ser[gn]; if(!v||v[1]<1000)return '<td style="color:var(--faint)">\\u00b7</td>'; return `<td style="color:${healthColor(v[0])}">${pct(v[2])}</td>`;}).join('')+'</tr>';});
  s.innerHTML=t+'</tbody></table>';
  document.getElementById('caveats').innerHTML=[
    `<b>Registrations, not the workforce.</b> eShram is self-enrolment with scheme incentives; shares describe who registered, not who works.`,
    `<b>Two series.</b> The data.gov.in dump holds ${DATA.total.toLocaleString()} rows; the eShram dashboard reports ${META.calibrated_total.toLocaleString()} distinct UANs. Sizes and motes are scaled to the dashboard by state factor; the belt is the difference, an upper bound on duplicates.`,
    `<b>${META.dropped_legacy_rows} legacy rows dropped</b> (under 100 registrations, mostly pre-2014 Telangana twins under the Andhra code) and spelling twins merged; ${META.n_districts} districts remain.`,
    `<b>Positions are boundary centroids</b> from the 2024 LGD district boundaries: ${META.matched} matched, ${META.fallback} placed at their state centroid (marked in the tooltip). This is not a map.`,
    `<b>One zero for discs and motes.</b> Colour pivots at parity (50%), not at India's ${pct(META.national_fem)}, so a teal disc and teal dots mean the same thing: more women than men.`,
    `<b>Corridors are lifetime linkages</b> (permanent vs current state), not migration rates; ${pct(META.corridors_drawn_share)} of ${META.interstate_movers.toLocaleString()} inter-state registrations are drawn.`
  ].map(x=>`<li>${x}</li>`).join('');
  document.getElementById('foot').innerHTML=`Source: data.gov.in eShram district dump (resource 1d4d1c5a), aggregated by PIF; calibration to the eShram dashboard as of ${META.dashboard_date}. Boundaries: ${META.boundary}. Generated ${DATA.generated}.`;
})();
"""+h[j:]; ok.append("charts")
else: bad.append("charts")
# remove the 3D link hint (no eshram 3d yet in that hint) -> point to eshram-3d
rep("hint3d",'<a href="/3d" style="color:var(--accent);text-decoration:none;','<a href="/eshram-3d" style="color:var(--accent);text-decoration:none;')

rep("borders2d","""function draw(){
  ctx.clearRect(0,0,W,H);
  const labelRects=[];""",
"""function draw(){
  ctx.clearRect(0,0,W,H);
  const labelRects=[];
  if(P.geo>0&&DATA.borders){                          // state outlines, only as far as the layout is a map
    const fa=P.geo, fo=hoverN||pinN, fs=fo?(fo.kind==='bucket'?fo.id:fo.parent):null;
    ctx.setLineDash([]);ctx.lineJoin='round';
    DATA.borders.forEach(b=>{const hi=b.id===fs; ctx.beginPath();
      b.r.forEach(ring=>{ring.forEach((q,i)=>{const sx=W/2+tx+q[0]*scale,sy=H/2+ty+q[1]*scale;i?ctx.lineTo(sx,sy):ctx.moveTo(sx,sy);});ctx.closePath();});
      ctx.fillStyle=`rgba(233,240,245,${(hi?.06:.022)*fa})`;ctx.fill();
      ctx.strokeStyle=`rgba(233,240,245,${(hi?.6:.16)*fa})`;ctx.lineWidth=hi?1.3:.8;ctx.stroke();});
  }""")
open("eshram.html","w").write(h)
print("ok:",len(ok),"| FAILED:",bad)
