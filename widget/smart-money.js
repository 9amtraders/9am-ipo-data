(function(){
"use strict";
var DATA_URL="https://raw.githubusercontent.com/9amtraders/9am-ipo-data/main/smartmoney/deals.json";
var root=document.getElementById("sm9");root.classList.add("anim"),$=function(id){return document.getElementById(id)};
var DPR=Math.min(window.devicePixelRatio||1,2);
var ST={bns:false,per:1,type:"ALL",inv:"ALL",q:"",churn:true,river:"stock",sort:"v",dir:-1,page:0};
var DB=null,VIEW=null;

/* ---------- investor classification (best guess from the name) ---------- */
var RX={
 star:/JHUNJHUNWALA|RARE ENTERPRISES|ASHISH KACHOLIA|BENGAL FINANCE|VIJAY KISHANLAL KEDIA|VIJAY KEDIA|KEDIA SECURITIES|DOLLY KHANNA|RAJIV KHANNA|MUKUL MAHAVIR AGRAWAL|MUKUL AGRAWAL|PARAM CAPITAL|ABAKKUS|SUNIL SINGHANIA|PORINJU|EQUITY INTELLIGENCE|RADHAKISHAN DAMANI|DERIVE TRADING|BRIGHT STAR INVESTMENTS|NEMISH S\.? ?SHAH|MADHUSUDAN KELA|MADHU KELA|SINGULARITY|ANIL KUMAR GOEL|SATPAL KHATTAR|AKASH BHANSHALI|VALLABH BHANSHALI|SHANKAR SHARMA|ASHISH DHAWAN|AASHISH KACHOLIA|SANJIV DHIRESHBHAI SHAH|BHARAT JAYANTILAL SHAH/,
 hft:/GRAVITON|HRTI|QE SECURITIES|JUNOMONETA|SILVERLEAF|MATHISYS|NK SECURITIES|IRAGE|TOWER RESEARCH|ALPHAGREP|XTX|JUMP TRADING|CITADEL SECURITIES|MICROCURVES|DOVETAIL|PACE STOCK|ELIXIR WEALTH|SHARE INDIA SECURITIES|SUNRISE GILTS|ANKIT RAJ|F3 ADVISORS|HIGH FREQUENCY|QUANT ?TRADING|ESHAANSH|PRASAN|SB STOCKS/,
 mf:/MUTUAL FUND|\bMF\b|ASSET MANAGEMENT|\bAMC\b|ETF\b/,
 ins:/INSURANCE|\bLIC\b|LIFE INSURANCE/,
 fii:/\bPTE\b|\bLLC\b|\bPLC\b|\bL\.?P\.?$|\bLP\b|SICAV|GMBH|\bINC\b|\bAG\b|\bS\.?A\.?$|MAURITIUS|SINGAPORE|CAYMAN|MASTER FUND|OFFSHORE|EMERGING MARKET|SOCIETE GENERALE|GOLDMAN SACHS|MORGAN STANLEY|BNP PARIBAS|CITIGROUP|NOMURA|VANGUARD|BLACKROCK|NORGES|GOVERNMENT PENSION|ABU DHABI|\bGIC\b|JPMORGAN|BOFA|MERRILL|UBS\b|HSBC|BARCLAYS|CLSA|FIDELITY|INVESCO|NATIXIS|AMUNDI|COPTHALL|ELARA INDIA OPPORTUNITIES|VIKASA|NOVA GLOBAL|AG DYNAMIC|MINERVA VENTURES|ZINNIA|LTS INVESTMENT|NEXUS|FOREIGN PORTFOLIO|\bFPI\b|GLOBAL FUND/,
 corp:/\bLTD\b|LIMITED|\bLLP\b|\bPVT\b|PRIVATE|TRUST|FINVEST|SECURITIES|CAPITAL|VENTURES|INVESTMENTS?|HOLDINGS?|ENTERPRISES|\bFUND\b|ADVISORS|FINANCE|BROKING|STOCK|TRADING|BANK/
};
var TYPE={star:["Superstar","b-star","#ffc24b"],fii:["Foreign fund","b-fii","#a678ff"],mf:["Mutual fund","b-mf","#5ee7ff"],ins:["Insurance","b-ins","#1fd18b"],corp:["Company / firm","b-corp","#5a82ff"],ind:["Individual / HNI","b-ind","#ff78aa"],hft:["Prop / HFT","b-hft","#8f9bc0"]};
var cache={};
function classify(c){
  if(cache[c])return cache[c];
  var t="ind";
  if(RX.star.test(c))t="star";else if(RX.hft.test(c))t="hft";else if(RX.mf.test(c))t="mf";else if(RX.ins.test(c))t="ins";else if(RX.fii.test(c))t="fii";else if(/\bHUF\b/.test(c))t="ind";else if(RX.corp.test(c))t="corp";
  return cache[c]=t;
}

/* ---------- formatting ---------- */
function cr(v,sign){var a=Math.abs(v),s=sign?(v>0?"+":v<0?"−":""):(v<0?"−":"");
  if(a>=1000)return s+"₹"+(a/1000).toFixed(a>=10000?1:2)+"K Cr";
  if(a>=100)return s+"₹"+a.toFixed(0)+" Cr";
  if(a>=1)return s+"₹"+a.toFixed(1)+" Cr";
  return s+"₹"+(a*100).toFixed(0)+" L";}
function inr(n){return Math.round(n).toLocaleString("en-IN")}
function esc(s){return String(s).replace(/[&<>"']/g,function(m){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]})}
function dfmt(d){var p=d.split("-");return p[2]+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+p[1]-1]}
function title(s){return s.toLowerCase().replace(/\b[a-z]/g,function(m){return m.toUpperCase()}).replace(/\b(Ltd|Llp|Pvt|Huf|Pte|Llc|Plc|Mf)\b/g,function(m){return m.toUpperCase()})}
function badge(t){return '<span class="badge '+TYPE[t][1]+'">'+(t==="star"?"⭐ ":"")+TYPE[t][0]+"</span>"}

/* ---------- demo data (shown only until the live file exists) ---------- */
function demo(){
  var seed=7;function R(){seed=(seed*16807)%2147483647;return(seed-1)/2147483646}
  var S=[["RELIANCE","Reliance Industries","Oil Gas & Consumable Fuels",1420],["HDFCBANK","HDFC Bank","Financial Services",1710],["ZOMATO","Eternal","Consumer Services",265],["IRFC","Indian Railway Finance","Financial Services",132],["SUZLON","Suzlon Energy","Capital Goods",61],["TATAPOWER","Tata Power","Power",398],["DIXON","Dixon Technologies","Consumer Durables",15200],["KAYNES","Kaynes Technology","Capital Goods",5600],["PAYTM","One97 Communications","Financial Services",980],["NYKAA","FSN E-Commerce","Consumer Services",205],["IDEA","Vodafone Idea","Telecommunication",8.4],["YESBANK","Yes Bank","Financial Services",21],["BSE","BSE Ltd","Financial Services",2350],["HAL","Hindustan Aeronautics","Capital Goods",4400],["CDSL","Central Depository","Financial Services",1580],["POLYCAB","Polycab India","Capital Goods",7100],["TRENT","Trent","Consumer Services",5200],["APOLLOHOSP","Apollo Hospitals","Healthcare",7300],["SYRMA","Syrma SGS Tech","Capital Goods",640],["NAZARA","Nazara Technologies","Media Entertainment & Publication",1180]];
  var B=["ALPHA GROWTH MASTER FUND PTE LTD","SUNRISE MUTUAL FUND A/C SMALL CAP","EASTBRIDGE INSURANCE CO LTD","KESTREL CAPITAL LLP","R K MEHTA","NORTHSTAR EMERGING MARKETS LLC","MEHRA FAMILY TRUST","BLUEWATER ASSET MANAGEMENT","S P AGARWAL HUF","HORIZON INDIA OPPORTUNITIES FUND","MERIDIAN FINVEST PVT LTD","ANITA DESAI"];
  var C=["FASTLANE QUANT SECURITIES LLP","PICOSECOND TRADING LLP"];
  var dates=[],d=new Date(),out=[],secs={};
  while(dates.length<65){d.setDate(d.getDate()-1);if(d.getDay()%6)dates.push(d.toISOString().slice(0,10))}
  S.forEach(function(s){secs[s[0]]=s[2]});
  dates.forEach(function(dt,i){
    var n=5+Math.floor(R()*5);
    for(var k=0;k<n;k++){var s=S[Math.floor(R()*S.length)],bias=(s[0].charCodeAt(0)%3)-1,buy=R()<.5+bias*.25;
      var val=(R()<.15?60+R()*400:2+R()*45)*1e7,q=Math.round(val/s[3]);
      out.push({d:dt,s:s[0],n:s[1],c:B[Math.floor(R()*B.length)],b:buy?1:0,q:q,p:+(s[3]*(.97+R()*.06)).toFixed(2),t:val>20e7&&R()<.5?"BLOCK":"BULK"});}
    for(var j=0;j<2;j++){var s2=S[Math.floor(R()*S.length)],q2=Math.round((5+R()*30)*1e7/s2[3]),cl=C[j];
      out.push({d:dt,s:s2[0],n:s2[1],c:cl,b:1,q:q2,p:s2[3]},{d:dt,s:s2[0],n:s2[1],c:cl,b:0,q:Math.round(q2*(.96+R()*.04)),p:+(s2[3]*1.001).toFixed(2),t:"BULK"});
      out[out.length-2].t="BULK";}
  });
  var close={};S.forEach(function(s){close[s[0]]=+(s[3]*(.82+R()*.42)).toFixed(2)});
  var news={SYRMA:[{t:"Demo headline: this is where real news for the stock will appear",u:"https://news.google.com/",s:"Demo",d:dates[0]}]};
  return {updated:"demo",dates:dates,sectors:secs,deals:out,demo:true,close:close,closeDate:dates[0],news:news};
}

/* ---------- one-time prep: churn, price since deal, streaks ---------- */
function ord(n){return n+(n%100>10&&n%100<14?"th":["th","st","nd","rd"][n%10]||"th")}
function pct(x){return(x>=0?"+":"−")+Math.abs(x).toFixed(Math.abs(x)<10?1:0)+"%"}
function prep(){
  var g={},C=DB.close||{};
  DB.deals.forEach(function(r){var k=r.d+"|"+r.s+"|"+r.c;(g[k]=g[k]||[0,0])[r.b]+=r.q});
  DB.deals.forEach(function(r){var x=g[r.d+"|"+r.s+"|"+r.c];r._ch=x[0]>0&&x[1]>0&&Math.min(x[0],x[1])/Math.max(x[0],x[1])>=.8;r._ty=classify(r.c);r.v=r.q*r.p/1e7;
    r.x=C[r.s]?(C[r.s]/r.p-1)*100:null;r.ok=r.x===null?null:(r.b?r.x>=0:r.x<=0)});
  var S={},sold={};
  DB.deals.forEach(function(r){if(r._ch)return;var k=r.c+"|"+r.s;if(!r.b){sold[k]=1;return}
    var o=S[k]=S[k]||{c:r.c,s:r.s,n:r.n,t:r._ty,days:{},v:0,q:0,pq:0};o.days[r.d]=1;o.v+=r.v;o.q+=r.q;o.pq+=r.q*r.p});
  DB.streaks=[];
  Object.keys(S).forEach(function(k){var o=S[k];o.dates=Object.keys(o.days).sort();o.nd=o.dates.length;if(o.nd<2)return;
    o.avg=o.pq/o.q;o.x=C[o.s]?(C[o.s]/o.avg-1)*100:null;o.sold=!!sold[k];DB.streaks.push(o)});
  DB.streaks.sort(function(a,b){return b.nd-a.nd||b.v-a.v});
  DB.deals.forEach(function(r){if(!r.b||r._ch)return;var o=S[r.c+"|"+r.s];if(o&&o.nd>=2)r._st=o.dates.indexOf(r.d)+1});
}

/* ---------- compute everything for current filters ---------- */
function compute(){
  var days=DB.dates.slice(0,ST.per),dset={};days.forEach(function(d){dset[d]=1});
  var q=ST.q.trim().toUpperCase();
  var base=DB.deals.filter(function(r){return dset[r.d]&&(ST.type==="ALL"||r.t===ST.type)});
  if(ST.bns){var sp={};DB.deals.forEach(function(r){if(dset[r.d]&&!r.b&&!r._ch)sp[r.c+"|"+r.s]=1});
    base=base.filter(function(r){return r.b&&!r._ch&&!sp[r.c+"|"+r.s]})}
  var rows=base.filter(function(r){
    if(ST.inv!=="ALL"&&r._ty!==ST.inv)return false;
    if(q&&r.s.indexOf(q)<0&&r.c.indexOf(q)<0&&String(r.n).toUpperCase().indexOf(q)<0)return false;return true});
  var live=rows.filter(function(r){return!(ST.churn&&r._ch)});
  var stocks={},sectors={},clients={},types={},buy=0,sell=0,stars=0,churned=rows.length-live.length;
  live.forEach(function(r){
    var sg=r.b?1:-1;if(r.b)buy+=r.v;else sell+=r.v;if(r._ty==="star")stars++;
    var s=stocks[r.s]=stocks[r.s]||{s:r.s,n:r.n,sec:DB.sectors[r.s]||"Other / SME",buy:0,sell:0,cnt:0,star:false,deals:[]};
    s[r.b?"buy":"sell"]+=r.v;s.cnt++;if(r._ty==="star")s.star=true;s.deals.push(r);
    var se=sectors[s.sec]=sectors[s.sec]||{n:s.sec,net:0,gross:0};se.net+=sg*r.v;se.gross+=r.v;
    var c=clients[r.c]=clients[r.c]||{c:r.c,t:r._ty,net:0,syms:{}};c.net+=sg*r.v;c.syms[r.s]=(c.syms[r.s]||0)+sg*r.v;
    var t=types[r._ty]=types[r._ty]||{t:r._ty,buy:0,sell:0};t[r.b?"buy":"sell"]+=r.v;
  });
  var sl=Object.keys(stocks).map(function(k){var s=stocks[k];s.net=s.buy-s.sell;s.gross=s.buy+s.sell;return s});
  VIEW={days:days,rows:rows,live:live,stocks:sl,sectors:Object.keys(sectors).map(function(k){return sectors[k]}),clients:Object.keys(clients).map(function(k){return clients[k]}),types:types,buy:buy,sell:sell,stars:stars,churned:churned};
}

/* ---------- counters ---------- */
function count(el,to,fmt){var from=+(el.dataset.v||0),t0=performance.now(),D=900;el.dataset.v=to;
  (function f(t){var k=Math.min(1,(t-t0)/D),e=1-Math.pow(1-k,3);el.textContent=fmt(from+(to-from)*e);if(k<1)requestAnimationFrame(f)})(t0)}

function renderTop(){
  var V=VIEW,net=V.buy-V.sell,lbl=ST.per===1?dfmt(V.days[0]||"2000-01-01"):"last "+V.days.length+" trading days";
  count($("k-buy"),V.buy,function(v){return cr(v)});count($("k-sell"),V.sell,function(v){return cr(v)});
  count($("k-stk"),V.stocks.length,function(v){return Math.round(v)});count($("k-star"),V.stars,function(v){return Math.round(v)});
  $("k-buy-s").innerHTML="Net "+'<b class="'+(net>=0?"g":"r")+'">'+cr(net,true)+"</b> · "+lbl;
  $("k-sell-s").textContent=V.live.length+" deals"+(V.churned?" · "+V.churned+" churn hidden":"");
  var up=V.stocks.filter(function(s){return s.net>0}).length;$("k-stk-s").textContent=up+" net bought · "+(V.stocks.length-up)+" net sold";
  // ticker
  var t=V.live.slice().sort(function(a,b){return b.v-a.v}).slice(0,40).map(function(r){
    return '<span class="ti"><b>'+esc(r.s)+'</b><span class="act '+(r.b?"B":"S")+'">'+(r.b?"BUY":"SELL")+'</span><span class="mut">'+esc(title(r.c).slice(0,34))+'</span><b class="mono '+(r.b?"g":"r")+'">'+cr(r.v)+"</b></span>"}).join("");
  $("sm9-tick").innerHTML=t?t+t:'<span class="ti mut">No deals for these filters</span>';
  // insights
  var s=V.stocks.slice().sort(function(a,b){return b.net-a.net}),top=s[0],bot=s[s.length-1];
  var sec=V.sectors.slice().sort(function(a,b){return b.net-a.net});
  var star=V.live.filter(function(r){return r._ty==="star"}).sort(function(a,b){return b.v-a.v})[0];
  var blk=V.live.filter(function(r){return r.t==="BLOCK"}).sort(function(a,b){return b.v-a.v})[0];
  var I=[];
  if(top&&top.net>0)I.push(["🧲","Biggest money magnet",top.s,cr(top.net,true)+" net bought",top.s]);
  if(bot&&bot.net<0)I.push(["🚪","Biggest exit",bot.s,cr(bot.net,true)+" net sold",bot.s]);
  if(sec[0]&&sec[0].net>0)I.push(["🏭","Hottest sector",sec[0].n,cr(sec[0].net,true)+" flowing in",null]);
  var stk=DB.streaks.filter(function(o){return ST.inv==="ALL"||o.t===ST.inv})[0];
  if(stk)I.push(["🔥","Accumulation streak",stk.s,title(stk.c).slice(0,24)+" bought on "+stk.nd+" days · "+cr(stk.v),stk.s]);
  if(star)I.push(["⭐","Superstar move",star.s,title(star.c).slice(0,26)+" "+(star.b?"bought ":"sold ")+cr(star.v),star.s]);
  else if(blk)I.push(["🧱","Biggest block deal",blk.s,(blk.b?"Bought by ":"Sold by ")+title(blk.c).slice(0,24)+" · "+cr(blk.v),blk.s]);
  else if(sec.length>1&&sec[sec.length-1].net<0)I.push(["🧊","Coldest sector",sec[sec.length-1].n,cr(sec[sec.length-1].net,true)+" flowing out",null]);
  renderSummary();
  $("sm9-ins").innerHTML=I.map(function(x){return'<div class="ins" '+(x[4]?'data-sym="'+esc(x[4])+'"':"")+'><div class="e">'+x[0]+'</div><div class="t">'+x[1]+'</div><div class="h">'+esc(x[2])+'</div><div class="d">'+esc(x[3])+"</div></div>"}).join("");
}

/* ---------- canvas helpers ---------- */
function fit(cv){if(!cv._bh)cv._bh=+cv.getAttribute("height");var w=cv.clientWidth,h=cv._bh;if(window.innerWidth<600)h=Math.round(h*.85);
  if(cv._w!==w||cv._h!==h){cv.width=w*DPR;cv.height=h*DPR;cv.style.height=h+"px";cv._w=w;cv._h=h}
  var x=cv.getContext("2d");x.setTransform(DPR,0,0,DPR,0,0);return{x:x,w:w,h:h}}
var tip=$("sm9-tip");
function showTip(e,html){tip.innerHTML=html;tip.style.opacity=1;var x=e.clientX+14,y=e.clientY+14;if(x+270>innerWidth)x=e.clientX-274;tip.style.left=x+"px";tip.style.top=y+"px"}
function hideTip(){tip.style.opacity=0}
function visible(el){var r=el.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight}

/* ---------- Money River ---------- */
var river={cv:$("sm9-river"),parts:[],L:[],Rt:[],t:0};
function buildRiver(){
  var src=ST.river==="stock"?VIEW.stocks.map(function(s){return{n:s.s,sub:s.sec,net:s.net,sym:s.s}}):VIEW.sectors.map(function(s){return{n:s.n,sub:"",net:s.net}});
  var mob=window.innerWidth<600,N=mob?5:7;
  river.L=src.filter(function(s){return s.net<0}).sort(function(a,b){return a.net-b.net}).slice(0,N);
  river.Rt=src.filter(function(s){return s.net>0}).sort(function(a,b){return b.net-a.net}).slice(0,N);
  river.parts=[];
}
function riverGeom(w,h){
  var mob=w<600,pad=mob?78:150,hub={x:w/2,y:h/2},all=river.L.concat(river.Rt),mx=Math.max.apply(null,all.map(function(s){return Math.abs(s.net)}).concat([1e-9]));
  function place(arr,x){var n=arr.length,gap=(h-60)/Math.max(n,1);return arr.map(function(s,i){return{s:s,x:x,y:30+gap*(i+.5),w:3+Math.sqrt(Math.abs(s.net)/mx)*(mob?16:26)}})}
  return{hub:hub,L:place(river.L,pad),R:place(river.Rt,w-pad),mob:mob}
}
function bez(a,b,t){var cx=(a.x+b.x)/2,u=1-t;return{x:u*u*u*a.x+3*u*u*t*cx+3*u*t*t*cx+t*t*t*b.x,y:u*u*u*a.y+3*u*u*t*a.y+3*u*t*t*b.y+t*t*t*b.y}}
function drawRiver(){
  var cv=river.cv;if(!visible(cv))return;var F=fit(cv),x=F.x,w=F.w,h=F.h,G=riverGeom(w,h);river.t++;
  x.clearRect(0,0,w,h);
  if(!G.L.length&&!G.R.length){x.fillStyle="#8f9bc0";x.font="14px Inter,sans-serif";x.textAlign="center";x.fillText("No money flow for these filters",w/2,h/2);return}
  // streams
  function stream(a,b,col,wd){x.beginPath();x.moveTo(a.x,a.y);var cx=(a.x+b.x)/2;x.bezierCurveTo(cx,a.y,cx,b.y,b.x,b.y);x.strokeStyle=col;x.lineWidth=wd;x.lineCap="round";x.stroke()}
  G.L.forEach(function(n){var gr=x.createLinearGradient(n.x,0,G.hub.x,0);gr.addColorStop(0,"rgba(255,77,94,.45)");gr.addColorStop(1,"rgba(120,140,255,.25)");stream(n,G.hub,gr,n.w)});
  G.R.forEach(function(n){var gr=x.createLinearGradient(G.hub.x,0,n.x,0);gr.addColorStop(0,"rgba(120,140,255,.25)");gr.addColorStop(1,"rgba(31,209,139,.5)");stream(G.hub,n,gr,n.w)});
  // spawn particles proportional to stream width
  G.L.forEach(function(n,i){if(Math.random()<n.w/40)river.parts.push({side:0,i:i,t:0,sp:.006+Math.random()*.006,o:(Math.random()-.5)*n.w*.7})});
  G.R.forEach(function(n,i){if(Math.random()<n.w/40)river.parts.push({side:1,i:i,t:0,sp:.006+Math.random()*.006,o:(Math.random()-.5)*n.w*.7})});
  river.parts=river.parts.filter(function(p){p.t+=p.sp;var arr=p.side?G.R:G.L,n=arr[p.i];if(!n||p.t>1)return false;
    var pt=p.side?bez(G.hub,n,p.t):bez(n,G.hub,p.t),col=p.side?"31,209,139":"255,77,94";
    x.beginPath();x.arc(pt.x,pt.y+p.o*(p.side?p.t:1-p.t),1.8,0,7);x.fillStyle="rgba("+col+","+(.9-Math.abs(.5-p.t)*.6)+")";x.shadowColor="rgba("+col+",1)";x.shadowBlur=8;x.fill();x.shadowBlur=0;return true});
  if(river.parts.length>900)river.parts.splice(0,river.parts.length-900);
  // hub
  var pr=18+Math.sin(river.t/20)*3,hg=x.createRadialGradient(G.hub.x,G.hub.y,2,G.hub.x,G.hub.y,pr*2.4);hg.addColorStop(0,"rgba(94,231,255,.9)");hg.addColorStop(.4,"rgba(90,100,255,.35)");hg.addColorStop(1,"rgba(90,100,255,0)");
  x.fillStyle=hg;x.beginPath();x.arc(G.hub.x,G.hub.y,pr*2.4,0,7);x.fill();x.fillStyle="#0a1128";x.beginPath();x.arc(G.hub.x,G.hub.y,pr,0,7);x.fill();x.strokeStyle="#5ee7ff";x.lineWidth=2;x.stroke();
  x.fillStyle="#fff";x.font="700 15px Inter,sans-serif";x.textAlign="center";x.textBaseline="middle";x.fillText("₹",G.hub.x,G.hub.y+1);
  // labels
  x.font=(G.mob?"700 9px":"700 11px")+" Inter";x.fillStyle="#8f9bc0";x.textBaseline="alphabetic";x.textAlign="left";x.fillText("MONEY LEAVING ↓",8,16);x.textAlign="right";x.fillText("MONEY ARRIVING ↓",w-8,16);
  function lab(n,right){var fs=G.mob?10:13;x.textAlign=right?"left":"right";var lx=right?n.x+10:n.x-10;
    x.font="700 "+fs+"px Inter,sans-serif";x.fillStyle="#e8ecf7";var name=n.s.n;if(G.mob&&name.length>9)name=name.slice(0,9)+"…";else if(name.length>18)name=name.slice(0,17)+"…";x.fillText(name,lx,n.y-1);
    x.font="700 "+(fs-1)+"px \"JetBrains Mono\",monospace";x.fillStyle=right?"#1fd18b":"#ff4d5e";x.fillText(cr(n.s.net,true),lx,n.y+fs);
    x.beginPath();x.arc(n.x,n.y,4+n.w/5,0,7);x.fillStyle=right?"#1fd18b":"#ff4d5e";x.fill()}
  G.L.forEach(function(n){lab(n,false)});G.R.forEach(function(n){lab(n,true)});
  river.G=G;
}
river.cv.addEventListener("mousemove",function(e){var G=river.G;if(!G)return;var r=river.cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,hit=null;
  G.L.concat(G.R).forEach(function(n){if(Math.abs(mx-n.x)<60&&Math.abs(my-n.y)<18)hit=n});
  river.cv.style.cursor=hit&&hit.s.sym?"pointer":"default";
  if(hit)showTip(e,"<b>"+esc(hit.s.n)+"</b><br>"+(hit.s.net>0?'<span class="g">Net bought ':'<span class="r">Net sold ')+cr(Math.abs(hit.s.net))+"</span>"+(hit.s.sub?'<br><span class="mut">'+esc(hit.s.sub)+"</span>":"")+(hit.s.sym?'<br><span class="mut">Click for details</span>':""));else hideTip()});
river.cv.addEventListener("mouseleave",hideTip);
river.cv.addEventListener("click",function(e){var G=river.G;if(!G)return;var r=river.cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
  G.L.concat(G.R).forEach(function(n){if(n.s.sym&&Math.abs(mx-n.x)<70&&Math.abs(my-n.y)<20)openStock(n.s.sym)})});

/* ---------- Sankey Money Map: investor type -> sector -> stock ---------- */
var sk={cv:$("sm9-sk"),mode:"all",prog:0,hover:null,parts:[],nodes:[],links:[],lay:null};
function buildSankey(){
  var mob=window.innerWidth<600,NS=mob?12:18,NSEC=mob?7:10;
  var rows=VIEW.live.filter(function(r){return sk.mode==="all"||(sk.mode==="buy"?r.b:!r.b)});
  var secT={},stT={};
  rows.forEach(function(r){var se=DB.sectors[r.s]||"Other / SME";secT[se]=(secT[se]||0)+r.v;stT[r.s]=(stT[r.s]||0)+r.v});
  var secs=Object.keys(secT).sort(function(a,b){return secT[b]-secT[a]}),secKeep={};secs.slice(0,NSEC).forEach(function(x){secKeep[x]=1});
  var sts=Object.keys(stT).sort(function(a,b){return stT[b]-stT[a]}),stKeep={};sts.slice(0,NS).forEach(function(x){stKeep[x]=1});
  var N={},L={};
  function node(id,col,label,extra){var n=N[id];if(!n){n=N[id]={id:id,col:col,label:label,v:0,net:0,ins:[],outs:[]};for(var k in extra)n[k]=extra[k]}return n}
  function link(a,b,v,sg){var k=a.id+">"+b.id,l=L[k];if(!l){l=L[k]={s:a,t:b,v:0,net:0};a.outs.push(l);b.ins.push(l)}l.v+=v;l.net+=sg*v}
  rows.forEach(function(r){
    var se=DB.sectors[r.s]||"Other / SME";if(!secKeep[se])se="Other sectors";
    var sym=stKeep[r.s]?r.s:"Other stocks",sg=r.b?1:-1;
    var a=node("T:"+r._ty,0,TYPE[r._ty][0],{ty:r._ty}),b=node("S:"+se,1,se,{}),c=node("K:"+sym,2,sym,{sym:sym==="Other stocks"?null:sym,sec:se});
    [a,b,c].forEach(function(n){n.v+=r.v;n.net+=sg*r.v});
    link(a,b,r.v,sg);link(b,c,r.v,sg);
  });
  sk.nodes=Object.keys(N).map(function(k){return N[k]});sk.links=Object.keys(L).map(function(k){return L[k]});
  sk.lay=null;sk.parts=[];sk.prog=0;sk.hover=null;
}
function layoutSankey(w,h){
  var mob=w<600,nw=mob?8:12,labW=mob?78:158,gap=mob?5:8,top=8,bot=8;
  var cols=[[],[],[]];sk.nodes.forEach(function(n){cols[n.col].push(n)});
  cols[0].sort(function(a,b){return b.v-a.v});
  cols[1].sort(function(a,b){return(a.label==="Other sectors")-(b.label==="Other sectors")||b.v-a.v});
  var secRank={};cols[1].forEach(function(n,i){secRank[n.label]=i});
  cols[2].sort(function(a,b){return(a.label==="Other stocks")-(b.label==="Other stocks")||secRank[a.sec]-secRank[b.sec]||b.v-a.v});
  var T=cols[0].reduce(function(s,n){return s+n.v},0)||1,k=Infinity;
  cols.forEach(function(c){if(c.length)k=Math.min(k,(h-top-bot-gap*(c.length-1))/T)});
  var xs=[mob?4:10,Math.round(w*(mob?.40:.42)),w-labW-nw];
  cols.forEach(function(c,ci){var tot=c.reduce(function(s,n){return s+Math.max(1.5,n.v*k)},0)+gap*(c.length-1),y=top+(h-top-bot-tot)/2;
    c.forEach(function(n){n.x=xs[ci];n.w=nw;n.y=y;n.h=Math.max(1.5,n.v*k);y+=n.h+gap})});
  sk.nodes.forEach(function(n){
    n.outs.sort(function(a,b){return a.t.y-b.t.y});n.ins.sort(function(a,b){return a.s.y-b.s.y});
    var o=n.y;n.outs.forEach(function(l){l.wd=l.v*k;l.sy=o;o+=l.wd});
    var i=n.y;n.ins.forEach(function(l){l.ty=i;i+=l.wd});
  });
  sk.links.forEach(function(l){l.x0=l.s.x+l.s.w;l.x1=l.t.x;l.col=sk.mode==="buy"?"31,209,139":sk.mode==="sell"?"255,77,94":l.net>=0?"31,209,139":"255,77,94"});
  return{w:w,h:h,mob:mob,k:k};
}
function skBand(x,l){var xm=(l.x0+l.x1)/2;x.beginPath();x.moveTo(l.x0,l.sy);x.bezierCurveTo(xm,l.sy,xm,l.ty,l.x1,l.ty);x.lineTo(l.x1,l.ty+l.wd);x.bezierCurveTo(xm,l.ty+l.wd,xm,l.sy+l.wd,l.x0,l.sy+l.wd);x.closePath()}
function skLit(l){var h=sk.hover;if(!h)return null;if(h.link)return h.link===l;var n=h.node;
  if(l.s===n||l.t===n)return true;
  if(n.col===2&&l.t.col===1)return l.t.outs.some(function(m){return m.t===n});
  if(n.col===0&&l.s.col===1)return l.s.ins.some(function(m){return m.s===n});
  return false}
function drawSankey(){
  var cv=sk.cv;if(!visible(cv))return;var F=fit(cv),x=F.x,w=F.w,h=F.h;
  if(!sk.lay||sk.lay.w!==w||sk.lay.h!==h)sk.lay=layoutSankey(w,h);var G=sk.lay;
  x.clearRect(0,0,w,h);
  if(!sk.links.length){x.fillStyle="#8f9bc0";x.font="14px Inter,sans-serif";x.textAlign="center";x.fillText("No money flow for these filters",w/2,h/2);return}
  sk.prog=Math.min(1,sk.prog+.018);var e=1-Math.pow(1-sk.prog,3);
  x.save();x.beginPath();x.rect(0,0,w*e+2,h);x.clip();
  // rivers
  sk.links.forEach(function(l){var lit=skLit(l),a=lit===null?.30:lit?.62:.06;
    var g=x.createLinearGradient(l.x0,0,l.x1,0);g.addColorStop(0,"rgba("+l.col+","+a*.75+")");g.addColorStop(1,"rgba("+l.col+","+a+")");
    skBand(x,l);x.fillStyle=g;x.fill()});
  // particles
  if(sk.parts.length<(G.mob?600:1100))sk.links.forEach(function(l){if(Math.random()<Math.min(.9,l.wd/26+.04))sk.parts.push({l:l,t:0,sp:.004+Math.random()*.005,o:Math.random()})});
  sk.parts=sk.parts.filter(function(p){p.t+=p.sp;if(p.t>1)return false;var l=p.l,lit=skLit(l);if(lit===false)return true;
    var a={x:l.x0,y:l.sy+l.wd*(.1+p.o*.8)},b={x:l.x1,y:l.ty+l.wd*(.1+p.o*.8)},pt=bez(a,b,p.t);
    x.beginPath();x.arc(pt.x,pt.y,lit?1.9:1.4,0,7);x.fillStyle="rgba("+l.col+","+(lit?1:.75)+")";x.fill();return true});
  // nodes + labels
  var fs=G.mob?10:12;
  sk.nodes.forEach(function(n){
    var c=n.col===0?TYPE[n.ty][2]:n.col===1?"#7c8cff":(n.net>=0?"#1fd18b":"#ff4d5e");
    var dim=sk.hover&&!(sk.hover.node===n||(sk.hover.link&&(sk.hover.link.s===n||sk.hover.link.t===n))||sk.links.some(function(l){return(l.s===n||l.t===n)&&skLit(l)}));
    x.globalAlpha=dim?.35:1;x.fillStyle=c;x.beginPath();if(x.roundRect)x.roundRect(n.x,n.y,n.w,n.h,3);else x.rect(n.x,n.y,n.w,n.h);x.fill();
    if(n.h+(G.mob?5:8)>=(G.mob?11:13)||(sk.hover&&sk.hover.node===n)){
      var lx=n.x+n.w+6,ly=n.y+n.h/2,name=n.label;var max=n.col===1?(G.mob?11:20):n.col===0?(G.mob?13:18):(G.mob?9:14);if(name.length>max)name=name.slice(0,max-1)+"…";
      x.textAlign="left";x.textBaseline="middle";x.font="700 "+fs+"px Inter,sans-serif";
      x.shadowColor="rgba(5,10,30,.95)";x.shadowBlur=6;x.fillStyle="#e8ecf7";x.fillText(name,lx,ly-(n.h>26?fs*.55:0));
      if(n.h>26||n.col===2){var vt=n.col===2&&sk.mode==="all"?cr(n.net,true):cr(n.v);x.font="700 "+(fs-1)+"px \"JetBrains Mono\",monospace";x.fillStyle=n.col===2?c:"#aab3d3";
        if(n.h>26)x.fillText(vt,lx,ly+fs*.6);else{var tw=x.measureText(name).width;x.font="700 "+fs+"px Inter,sans-serif";tw=x.measureText(name).width;x.font="700 "+(fs-1)+"px \"JetBrains Mono\",monospace";if(!G.mob)x.fillText(vt,lx+tw+6,ly)}}
      x.shadowBlur=0}
    x.globalAlpha=1});
  x.restore();
}
function skHit(e){var r=sk.cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
  for(var i=0;i<sk.nodes.length;i++){var n=sk.nodes[i];if(mx>=n.x-4&&mx<=n.x+n.w+(n.col===2?120:70)&&my>=n.y-2&&my<=n.y+Math.max(n.h,10)+2&&(mx<=n.x+n.w+4||n.h>=6||n.col===2))return{node:n}}
  for(var j=sk.links.length-1;j>=0;j--){var l=sk.links[j];if(mx<l.x0||mx>l.x1)continue;
    var lo=0,hi=1,xm=(l.x0+l.x1)/2;for(var it=0;it<18;it++){var t=(lo+hi)/2,u=1-t,xx=u*u*u*l.x0+3*u*u*t*xm+3*u*t*t*xm+t*t*t*l.x1;if(xx<mx)lo=t;else hi=t}
    var t2=(lo+hi)/2,y=bez({x:l.x0,y:l.sy},{x:l.x1,y:l.ty},t2).y;if(my>=y-1&&my<=y+Math.max(l.wd,3)+1)return{link:l}}
  return null}
sk.cv.addEventListener("mousemove",function(e){var hh=skHit(e);sk.hover=hh;sk.cv.style.cursor=hh&&hh.node&&hh.node.sym?"pointer":"default";
  if(!hh)return hideTip();
  if(hh.node){var n=hh.node,nb=n.v,nn=n.net;showTip(e,"<b>"+esc(n.label)+"</b><br>"+(sk.mode==="all"?"Traded "+cr(nb)+"<br>Net <b class='"+(nn>=0?"g":"r")+"'>"+cr(nn,true)+"</b>":(sk.mode==="buy"?"Bought ":"Sold ")+"<b>"+cr(nb)+"</b>")+(n.sym?"<br><span class='mut'>Click for every deal</span>":""))}
  else{var l=hh.link;showTip(e,esc(l.s.label)+" &rarr; <b>"+esc(l.t.label)+"</b><br>"+(sk.mode==="all"?"Traded "+cr(l.v)+" · net <b class='"+(l.net>=0?"g":"r")+"'>"+cr(l.net,true)+"</b>":(sk.mode==="buy"?"Bought ":"Sold ")+"<b>"+cr(l.v)+"</b>"))}});
sk.cv.addEventListener("mouseleave",function(){sk.hover=null;hideTip()});
sk.cv.addEventListener("click",function(e){var hh=skHit(e);if(hh&&hh.node&&hh.node.sym)openStock(hh.node.sym);else if(hh){sk.hover=hh}});
$("f-sk").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;sk.mode=b.dataset.v;setSeg("f-sk",sk.mode);buildSankey()});

/* ---------- Bubble map ---------- */
var bub={cv:$("sm9-bub"),b:[],hover:null};
function buildBubbles(){
  var old={};bub.b.forEach(function(b){old[b.s.s]=b});
  var list=VIEW.stocks.slice().sort(function(a,b){return b.gross-a.gross}).slice(0,window.innerWidth<600?28:45);
  var mx=Math.max.apply(null,list.map(function(s){return s.gross}).concat([1e-9])),w=bub.cv.clientWidth||800,h=bub.cv._h||+bub.cv.getAttribute("height");
  var rmax=Math.min(w,h)/(window.innerWidth<600?7:8.5);
  bub.b=list.map(function(s){var o=old[s.s];var r=Math.max(9,Math.sqrt(s.gross/mx)*rmax);
    return{s:s,r:r,dr:o?o.dr:0,x:o?o.x:w/2+(Math.random()-.5)*60,y:o?o.y:h/2+(Math.random()-.5)*60,vx:0,vy:0,ph:Math.random()*6.28}});
}
function drawBubbles(){
  var cv=bub.cv;if(!visible(cv))return;var F=fit(cv),x=F.x,w=F.w,h=F.h,B=bub.b,t=performance.now()/1000;
  x.clearRect(0,0,w,h);
  // zones
  var gl=x.createLinearGradient(0,0,w,0);gl.addColorStop(0,"rgba(255,77,94,.08)");gl.addColorStop(.5,"rgba(255,255,255,0)");gl.addColorStop(1,"rgba(31,209,139,.08)");x.fillStyle=gl;x.fillRect(0,0,w,h);
  x.setLineDash([4,6]);x.strokeStyle="#22305e";x.beginPath();x.moveTo(w/2,10);x.lineTo(w/2,h-10);x.stroke();x.setLineDash([]);
  x.font="800 12px Inter,sans-serif";x.fillStyle="rgba(255,77,94,.7)";x.textAlign="left";x.fillText("◀ SELLING",12,22);x.fillStyle="rgba(31,209,139,.8)";x.textAlign="right";x.fillText("BUYING ▶",w-12,22);
  if(!B.length){x.fillStyle="#8f9bc0";x.font="14px Inter,sans-serif";x.textAlign="center";x.fillText("No deals for these filters",w/2,h/2);return}
  var mxn=Math.max.apply(null,B.map(function(b){return Math.abs(b.s.net)}).concat([1e-9]));
  B.forEach(function(b){
    b.dr+=(b.r-b.dr)*.08;
    var sg=b.s.net>0?1:b.s.net<0?-1:0,lean=sg*(.1+.3*Math.sqrt(Math.abs(b.s.net)/mxn)),tx=w/2+lean*w,ty=h/2+Math.sin(t*.6+b.ph)*12;
    b.vx+=(tx-b.x)*.0025;b.vy+=(ty-b.y)*.003;
  });
  for(var i=0;i<B.length;i++)for(var j=i+1;j<B.length;j++){var a=B[i],c=B[j],dx=c.x-a.x,dy=c.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||.01,m=a.dr+c.dr+3;
    if(d<m){var k=(m-d)/d*.5;dx*=k;dy*=k;a.x-=dx*.5;a.y-=dy*.5;c.x+=dx*.5;c.y+=dy*.5}}
  B.forEach(function(b){b.vx*=.86;b.vy*=.86;b.x+=b.vx;b.y+=b.vy;b.x=Math.max(b.dr,Math.min(w-b.dr,b.x));b.y=Math.max(b.dr+26,Math.min(h-b.dr,b.y));
    var pos=b.s.net>=0,c1=pos?"31,209,139":"255,77,94",g=x.createRadialGradient(b.x-b.dr*.35,b.y-b.dr*.4,b.dr*.1,b.x,b.y,b.dr);
    g.addColorStop(0,"rgba("+c1+",.95)");g.addColorStop(1,"rgba("+c1+",.35)");
    x.beginPath();x.arc(b.x,b.y,b.dr*(bub.hover===b?1.08:1),0,7);x.fillStyle=g;x.shadowColor="rgba("+c1+",.6)";x.shadowBlur=bub.hover===b?28:12;x.fill();x.shadowBlur=0;
    if(b.s.star){x.lineWidth=2.5;x.strokeStyle="#ffc24b";x.stroke()}
    if(b.dr>17){x.fillStyle="#fff";x.textAlign="center";x.textBaseline="middle";var fs=Math.min(14,b.dr/3.2);x.font="800 "+fs+"px Inter,sans-serif";
      var nm=b.s.s.length>10?b.s.s.slice(0,9)+"…":b.s.s;x.fillText(nm,b.x,b.y-(b.dr>28?fs*.45:0));
      if(b.dr>28){x.font="700 "+(fs*.8)+"px \"JetBrains Mono\",monospace";x.fillStyle="rgba(255,255,255,.85)";x.fillText(cr(b.s.net,true),b.x,b.y+fs*.75)}}
  });
}
function bubHit(e){var r=bub.cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,hit=null;bub.b.forEach(function(b){if((b.x-mx)*(b.x-mx)+(b.y-my)*(b.y-my)<b.dr*b.dr)hit=b});return hit}
bub.cv.addEventListener("mousemove",function(e){var b=bubHit(e);bub.hover=b;bub.cv.style.cursor=b?"pointer":"default";
  if(b)showTip(e,"<b>"+esc(b.s.s)+"</b> "+(b.s.star?"⭐":"")+'<br><span class="mut">'+esc(b.s.n)+"</span><br>Bought <b class='g'>"+cr(b.s.buy)+"</b> · Sold <b class='r'>"+cr(b.s.sell)+"</b><br>Net <b>"+cr(b.s.net,true)+"</b> · "+b.s.cnt+" deals");else hideTip()});
bub.cv.addEventListener("mouseleave",function(){bub.hover=null;hideTip()});
bub.cv.addEventListener("click",function(e){var b=bubHit(e);if(b)openStock(b.s.s)});

/* ---------- donut: flow by investor type ---------- */
var donut={cv:$("sm9-donut"),k:0};
function drawDonut(){
  var cv=donut.cv;if(!visible(cv))return;var F=fit(cv),x=F.x,w=F.w,h=F.h;x.clearRect(0,0,w,h);
  donut.k=Math.min(1,donut.k+.025);var e=1-Math.pow(1-donut.k,3);
  var T=Object.keys(VIEW.types).map(function(k){var o=VIEW.types[k];return{t:k,g:o.buy+o.sell,net:o.buy-o.sell}}).filter(function(o){return o.g>0}).sort(function(a,b){return b.g-a.g});
  var tot=T.reduce(function(s,o){return s+o.g},0);if(!tot){x.fillStyle="#8f9bc0";x.font="14px Inter,sans-serif";x.textAlign="center";x.fillText("No data",w/2,h/2);return}
  var narrow=w<460,cx=narrow?w/2:w*.3,cy=narrow?95:h/2,R=narrow?80:Math.min(h/2-14,w*.22),a0=-Math.PI/2;
  T.forEach(function(o){var a1=a0+o.g/tot*Math.PI*2*e;x.beginPath();x.arc(cx,cy,R,a0,a1);x.arc(cx,cy,R*.62,a1,a0,true);x.closePath();x.fillStyle=TYPE[o.t][2];x.globalAlpha=.9;x.fill();x.globalAlpha=1;a0=a1+0.0001});
  x.fillStyle="#e8ecf7";x.textAlign="center";x.textBaseline="middle";x.font="800 16px \"JetBrains Mono\",monospace";x.fillText(cr(tot),cx,cy-6);x.font="600 10px Inter,sans-serif";x.fillStyle="#8f9bc0";x.fillText("TOTAL TRADED",cx,cy+12);
  var lx=narrow?14:w*.58,ly=narrow?196:Math.max(20,h/2-T.length*15);
  T.forEach(function(o,i){var y=ly+i*(narrow?14:30);if(narrow&&i>5)return;x.fillStyle=TYPE[o.t][2];x.beginPath();x.arc(lx+5,y,5,0,7);x.fill();
    x.textAlign="left";x.fillStyle="#c9d1ec";x.font="600 "+(narrow?11:13)+"px Inter,sans-serif";x.fillText(TYPE[o.t][0],lx+16,y);
    x.textAlign="right";x.font="700 "+(narrow?11:13)+"px \"JetBrains Mono\",monospace";x.fillStyle=o.net>=0?"#1fd18b":"#ff4d5e";x.fillText(cr(o.net,true),w-10,y)});
}

/* ---------- sectors, leaders ---------- */
function renderSectors(){
  var S=VIEW.sectors.slice().sort(function(a,b){return b.net-a.net}),mx=Math.max.apply(null,S.map(function(s){return Math.abs(s.net)}).concat([1e-9]));
  if(S.length>14)S=S.slice(0,7).concat(S.slice(-7));
  $("sm9-sec").innerHTML=S.length?S.map(function(s){var p=Math.abs(s.net)/mx*100;return'<div class="sec" data-sec="'+esc(s.n)+'"><span class="n" title="'+esc(s.n)+'">'+esc(s.n)+'</span><span class="L"><span data-w="'+(s.net<0?p:0)+'"></span></span><span class="R"><span data-w="'+(s.net>0?p:0)+'"></span></span><span class="v '+(s.net>=0?"g":"r")+'">'+cr(s.net,true)+"</span></div>"}).join(""):'<div class="empty">No sector data</div>';
  requestAnimationFrame(function(){requestAnimationFrame(function(){root.querySelectorAll("#sm9-sec [data-w]").forEach(function(el){el.style.width=el.dataset.w+"%"})})});
}
function renderLeaders(){
  var C=VIEW.clients.filter(function(c){return c.t!=="hft"||!ST.churn});
  var W={};VIEW.live.forEach(function(r){if(r.b&&r.x!==null){var w=W[r.c]=W[r.c]||[0,0];w[0]+=r.x*r.v;w[1]+=r.v}});
  C.forEach(function(c){var w=W[c.c];c.wx=w&&w[1]?w[0]/w[1]:null});
  function rows(list,pos){if(!list.length)return'<div class="empty">Nothing here for these filters</div>';
    return list.map(function(c,i){var syms=Object.keys(c.syms).sort(function(a,b){return pos?c.syms[b]-c.syms[a]:c.syms[a]-c.syms[b]}).slice(0,3);
      return'<div class="lead-row"><span class="rank">'+(i+1)+'</span><div style="min-width:0"><div class="who" data-inv="'+esc(c.c)+'" title="See 3-month history">'+esc(title(c.c))+badge(c.t)+'</div><div class="sub">'+syms.map(function(s){return'<a href="#" data-sym="'+esc(s)+'" style="color:inherit">'+esc(s)+"</a>"}).join(" · ")+(c.wx!==null?' · <span class="'+(c.wx>=0?"g":"r")+'">buys '+pct(c.wx)+' since</span>':"")+'</div></div><b class="mono '+(pos?"g":"r")+'">'+cr(c.net,true)+"</b></div>"}).join("")}
  $("sm9-tb").innerHTML=rows(C.filter(function(c){return c.net>0}).sort(function(a,b){return b.net-a.net}).slice(0,8),true);
  $("sm9-ts").innerHTML=rows(C.filter(function(c){return c.net<0}).sort(function(a,b){return a.net-b.net}).slice(0,8),false);
}

/* ---------- summary paragraph (latest day, always) ---------- */
function renderSummary(){
  var d=DB.dates[0];if(!d){$("sm9-sum").style.display="none";return}
  var R=DB.deals.filter(function(r){return r.d===d&&!r._ch}),tot=0,st={},nb=0,nk=0;
  R.forEach(function(r){tot+=r.v;var o=st[r.s]=st[r.s]||0;st[r.s]=o+(r.b?r.v:-r.v);if(r.t==="BLOCK")nk++;else nb++});
  var ks=Object.keys(st).sort(function(a,b){return st[b]-st[a]}),sec={};
  ks.forEach(function(k){var se=DB.sectors[k]||"Other / SME";sec[se]=(sec[se]||0)+st[k]});
  var hs=Object.keys(sec).sort(function(a,b){return sec[b]-sec[a]})[0];
  var y=d.slice(0,4),txt="On <b>"+dfmt(d)+" "+y+"</b>, big investors traded <b>"+cr(tot)+"</b> in "+nb+" bulk deal"+(nb===1?"":"s")+" and "+nk+" block deal"+(nk===1?"":"s")+" across "+ks.length+" stocks on NSE.";
  if(ks.length&&st[ks[0]]>0)txt+=" Most money went into <b class='g'>"+esc(ks[0])+"</b> ("+cr(st[ks[0]],true)+")";
  if(ks.length>1&&st[ks[ks.length-1]]<0)txt+=", while <b class='r'>"+esc(ks[ks.length-1])+"</b> saw the biggest exit ("+cr(st[ks[ks.length-1]],true)+").";else txt+=".";
  if(hs&&sec[hs]>0)txt+=" Hottest sector: <b>"+esc(hs)+"</b>.";
  $("sm9-sum").innerHTML=txt;
}

/* ---------- did it work? ---------- */
function renderWork(){
  var el=$("sm9-wk");if(!DB.close||!DB.closeDate){el.innerHTML='<div class="empty">The price check appears after the next daily update.</div>';return}
  $("sm9-wk-s").textContent="Price move from each deal's price to the close on "+dfmt(DB.closeDate)+" · selected period and filters";
  var B=VIEW.live.filter(function(r){return r.b&&r.x!==null}),S=VIEW.live.filter(function(r){return!r.b&&r.x!==null});
  if(!B.length&&!S.length){el.innerHTML='<div class="empty">No priced deals for these filters</div>';return}
  function avg(a){return a.length?a.reduce(function(t,r){return t+r.x},0)/a.length:0}
  function win(a){return a.length?a.filter(function(r){return r.ok}).length/a.length*100:0}
  var best=B.slice().sort(function(a,b){return b.x-a.x})[0];
  var h='<div class="wk"><div><span>Big buys in profit</span><b class="'+(win(B)>=50?"g":"r")+'">'+(B.length?Math.round(win(B))+"%":"—")+'</b><div class="sub">of '+B.length+' buy deals · avg '+(B.length?pct(avg(B)):"—")+'</div></div>'+
    '<div><span>Price fell after big sells</span><b class="'+(win(S)>=50?"g":"r")+'">'+(S.length?Math.round(win(S))+"%":"—")+'</b><div class="sub">of '+S.length+' sell deals · avg '+(S.length?pct(avg(S)):"—")+'</div></div>'+
    '<div><span>Best buy since deal</span><b class="g">'+(best?pct(best.x):"—")+'</b><div class="sub">'+(best?'<a href="#" data-sym="'+esc(best.s)+'" style="color:inherit">'+esc(best.s)+"</a> · "+esc(title(best.c).slice(0,22)):"")+'</div></div></div>';
  var T={};B.forEach(function(r){(T[r._ty]=T[r._ty]||[]).push(r)});
  var rows=Object.keys(T).map(function(k){return{t:k,a:avg(T[k]),w:win(T[k]),n:T[k].length}}).sort(function(a,b){return b.w-a.w});
  h+='<div class="wrow h"><span>Buyer type</span><span>Buys in profit</span><span style="text-align:right">Win %</span><span style="text-align:right">Avg move</span></div>'+
    rows.map(function(o){return'<div class="wrow"><span>'+TYPE[o.t][0]+' <span class="mut">('+o.n+')</span></span><span class="bar2"><i data-w="'+o.w.toFixed(0)+'" style="background:'+TYPE[o.t][2]+'"></i></span><b class="mono" style="text-align:right">'+Math.round(o.w)+'%</b><b class="mono '+(o.a>=0?"g":"r")+'" style="text-align:right">'+pct(o.a)+"</b></div>"}).join("");
  h+='<p class="disc" style="text-align:left">Measured from the deal price to the latest close only. Past results don\'t predict future moves.</p>';
  el.innerHTML=h;
  requestAnimationFrame(function(){requestAnimationFrame(function(){el.querySelectorAll("[data-w]").forEach(function(i){i.style.width=i.dataset.w+"%"})})});
}

/* ---------- accumulation streaks ---------- */
function renderStreaks(){
  var q=ST.q.trim().toUpperCase();
  var L=DB.streaks.filter(function(o){return(ST.inv==="ALL"||o.t===ST.inv)&&(!q||o.s.indexOf(q)>=0||o.c.indexOf(q)>=0)&&(!ST.bns||!o.sold)}).slice(0,10);
  $("sm9-st").innerHTML=L.length?L.map(function(o){
    return'<div class="strk"><div class="fire"><b>'+o.nd+'</b><span>buy days</span></div><div style="min-width:0"><div><a href="#" class="sym" data-sym="'+esc(o.s)+'" style="color:#fff;font-weight:800">'+esc(o.s)+'</a> <span class="mut">·</span> <span class="who" style="display:inline" data-inv="'+esc(o.c)+'">'+esc(title(o.c))+"</span>"+badge(o.t)+(o.sold?"":'<span class="badge b-hold">no sell reported</span>')+'</div><div class="sub">'+o.dates.map(dfmt).join(" → ")+" · avg ₹"+o.avg.toFixed(2)+'</div></div><div style="text-align:right"><b class="mono g">'+cr(o.v)+'</b>'+(o.x!==null?'<div class="sub '+(o.x>=0?"g":"r")+'">'+pct(o.x)+" since</div>":"")+"</div></div>"}).join(""):'<div class="empty">No repeat buying by the same investor yet. Streaks appear once the tracker has a few days of data.</div>';
}

/* ---------- table ---------- */
var PG=25;
function sorted(){var k=ST.sort,d=ST.dir;return VIEW.rows.slice().sort(function(a,b){var x=a[k],y=b[k];if(k==="x"){x=x===null?-1e9*d:x;y=y===null?-1e9*d:y}if(k==="v"||k==="q"||k==="p"||k==="b"||k==="x")return(x-y)*d;return String(x).localeCompare(String(y))*d||(b.v-a.v)})}
function renderTable(){
  var all=sorted(),n=all.length,pages=Math.max(1,Math.ceil(n/PG));ST.page=Math.min(ST.page,pages-1);
  var rows=all.slice(ST.page*PG,ST.page*PG+PG);
  $("sm9-rows").innerHTML=rows.length?rows.map(function(r){var hid=ST.churn&&r._ch;
    return'<tr class="'+(r._ch?"churn":"")+'"><td class="mut">'+dfmt(r.d)+'</td><td><span class="sym" data-sym="'+esc(r.s)+'">'+esc(r.s)+'</span>'+((DB.news||{})[r.s]?'<span class="nb" data-sym="'+esc(r.s)+'" title="News available">📰</span>':"")+'<div class="sub">'+esc(String(r.n).slice(0,26))+'</div></td><td><div class="who" style="max-width:260px" data-inv="'+esc(r.c)+'" title="See '+esc(title(r.c))+'\'s 3-month history">'+esc(title(r.c))+'</div>'+badge(r._ty)+(r._ch?'<span class="badge b-churn">same-day churn</span>':"")+(r._st>1?'<span class="badge b-streak">🔥 '+ord(r._st)+' buy</span>':"")+'</td><td><span class="act '+(r.b?"B":"S")+'">'+(r.b?"BUY":"SELL")+'</span></td><td class="num mono hide-m">'+inr(r.q)+'</td><td class="num mono hide-m">'+r.p.toLocaleString("en-IN",{maximumFractionDigits:2})+'</td><td class="num mono '+(hid?"":r.b?"g":"r")+'"><b>'+cr(r.v)+'</b></td><td class="num mono" title="'+(DB.close&&DB.close[r.s]?"Close ₹"+DB.close[r.s]+" on "+dfmt(DB.closeDate):"")+'">'+(r.x===null?'<span class="mut">—</span>':'<span class="'+(r.ok?"g":"r")+'">'+pct(r.x)+'</span><span class="ok '+(r.ok?"g":"r")+'">'+(r.ok?"✓":"✗")+"</span>")+'</td><td class="hide-m"><span class="badge b-'+r.t.toLowerCase()+'">'+r.t+"</span></td></tr>"}).join(""):'<tr><td colspan="9" class="empty">No deals match. Try a longer period or clear the search.</td></tr>';
  $("pg-info").textContent="Page "+(ST.page+1)+" of "+pages;$("pg-prev").disabled=ST.page===0;$("pg-next").disabled=ST.page>=pages-1;
  $("sm9-cnt").textContent=n+" deals"+(VIEW.churned?" · "+VIEW.churned+" same-day churn deals greyed out and left out of totals":"");
  root.querySelectorAll(".tbl th").forEach(function(th){th.textContent=th.textContent.replace(/ [▲▼]$/,"");if(th.dataset.k===ST.sort)th.textContent+=ST.dir<0?" ▼":" ▲"});
}

/* ---------- outbound verification links ---------- */
function vlinks(sym,name){var e=encodeURIComponent,tv=sym.replace(/[&-]/g,"_"),q=e(String(name||sym).replace(/\b(Limited|Ltd\.?)\b/gi,"").trim()+" share");
  return'<div class="vlinks">'+
   '<a class="nse" href="https://www.nseindia.com/get-quotes/equity?symbol='+e(sym)+'" target="_blank" rel="noopener">NSE quote ↗</a>'+
   '<a class="nse" href="https://www.nseindia.com/report-detail/display-bulk-and-block-deals" target="_blank" rel="noopener">NSE deals report ↗</a>'+
   '<a href="https://www.tradingview.com/chart/?symbol=NSE%3A'+e(tv)+'" target="_blank" rel="noopener nofollow">Chart ↗</a>'+
   '<a href="https://www.screener.in/company/'+e(sym)+'/" target="_blank" rel="noopener nofollow">Fundamentals ↗</a>'+
   '<a href="https://news.google.com/search?q='+q+'&hl=en-IN&gl=IN&ceid=IN%3Aen" target="_blank" rel="noopener nofollow">All news ↗</a></div>'}
function newsList(sym){var N=(DB.news||{})[sym];if(!N||!N.length)return"";
  return'<h3 style="margin:14px 0 2px">Latest news</h3><div class="news">'+N.map(function(n){return'<a href="'+esc(n.u)+'" target="_blank" rel="noopener nofollow">'+esc(n.t)+'<small>'+esc(n.s||"News")+" · "+dfmt(n.d)+" ↗</small></a>"}).join("")+"</div>"}

/* ---------- stock drawer ---------- */
function openStock(sym){
  var s=VIEW.stocks.filter(function(x){return x.s===sym})[0],rows=VIEW.rows.filter(function(r){return r.s===sym});
  if(!rows.length)rows=DB.deals.filter(function(r){return r.s===sym});
  if(!rows.length)return;
  var B=rows.filter(function(r){return r.b&&!(ST.churn&&r._ch)}),S=rows.filter(function(r){return!r.b&&!(ST.churn&&r._ch)});
  function avg(a){var q=0,v=0;a.forEach(function(r){q+=r.q;v+=r.q*r.p});return q?v/q:0}
  var nb=B.reduce(function(t,r){return t+r.v},0),ns=S.reduce(function(t,r){return t+r.v},0),net=nb-ns;
  var verdict=net>0?'<span class="g">Big money was <b>accumulating</b> '+esc(sym)+"</span>":net<0?'<span class="r">Big money was <b>exiting</b> '+esc(sym)+"</span>":'<span class="mut">Buying and selling were balanced</span>';
  $("sm9-drawer").innerHTML='<button class="x" aria-label="Close">×</button><div class="mut" style="font-size:12px;text-transform:uppercase;letter-spacing:.06em">'+esc((s&&s.sec)||DB.sectors[sym]||"Other / SME")+'</div><h2 style="margin-top:4px">'+esc(sym)+'</h2><p class="mut">'+esc(rows[0].n)+'</p><p style="margin-top:12px">'+verdict+'</p>'+vlinks(sym,rows[0].n)+newsList(sym)+
   '<div class="mini"><div><span>Bought</span><b class="g">'+(nb?cr(nb):"—")+'</b></div><div><span>Sold</span><b class="r">'+(ns?cr(ns):"—")+'</b></div><div><span>Avg buy price</span><b>'+(B.length?"₹"+avg(B).toFixed(2):"—")+'</b></div><div><span>Avg sell price</span><b>'+(S.length?"₹"+avg(S).toFixed(2):"—")+'</b></div>'+(DB.close&&DB.close[sym]?'<div><span>Last close ('+dfmt(DB.closeDate)+')</span><b>₹'+DB.close[sym]+'</b></div><div><span>Buyers since avg buy</span><b class="'+(DB.close[sym]>=avg(B)?"g":"r")+'">'+(B.length?pct((DB.close[sym]/avg(B)-1)*100):"—")+'</b></div>':"")+'</div>'+
   '<h3 style="margin:8px 0">Every deal</h3>'+rows.sort(function(a,b){return b.d.localeCompare(a.d)||b.v-a.v}).map(function(r){return'<div class="lead-row" style="grid-template-columns:auto 1fr auto;'+(r._ch?"opacity:.5":"")+'"><span class="act '+(r.b?"B":"S")+'">'+(r.b?"BUY":"SELL")+'</span><div style="min-width:0"><div class="who" data-inv="'+esc(r.c)+'">'+esc(title(r.c))+badge(r._ty)+'</div><div class="sub">'+dfmt(r.d)+" · "+inr(r.q)+" sh @ ₹"+r.p+" · "+r.t+(r._ch?" · same-day churn":"")+(r._st>1?" · 🔥 "+ord(r._st)+" buy":"")+(r.x!==null?' · <span class="'+(r.ok?"g":"r")+'">'+pct(r.x)+" since</span>":"")+'</div></div><b class="mono">'+cr(r.v)+"</b></div>"}).join("")+
   '<p class="disc">Bulk and block deals show past trades, not future direction. Educational only.</p>';
  $("sm9-drawer").scrollTop=0;$("sm9-drawer").classList.add("on");$("sm9-shade").classList.add("on");hideTip();
  try{if(location.hash!=="#stock-"+sym)history.replaceState(null,"","#stock-"+sym)}catch(e){}
}
/* ---------- investor history (up to ~3 months) ---------- */
function openInvestor(c){
  var all=DB.deals.filter(function(r){return r.c===c});if(!all.length)return;
  var real=all.filter(function(r){return!r._ch}),C=DB.close||{},P={},tb=0,ts=0;
  real.forEach(function(r){var o=P[r.s]=P[r.s]||{s:r.s,n:r.n,bq:0,sq:0,bv:0,sv:0,bpq:0,spq:0,first:r.d,last:r.d,nb:0};
    if(r.b){o.bq+=r.q;o.bv+=r.v;o.bpq+=r.q*r.p;o.nb++;tb+=r.v}else{o.sq+=r.q;o.sv+=r.v;o.spq+=r.q*r.p;ts+=r.v}
    if(r.d<o.first)o.first=r.d;if(r.d>o.last)o.last=r.d});
  var pos=Object.keys(P).map(function(k){var o=P[k];o.ab=o.bq?o.bpq/o.bq:0;o.as=o.sq?o.spq/o.sq:0;
    o.x=o.bq&&C[o.s]?(C[o.s]/o.ab-1)*100:null;
    o.st=!o.bq?["Sold","st-x"]:!o.sq?["Holding · no sell reported","st-h"]:o.sq>=o.bq*.95?["Exited","st-x"]:["Partly sold","st-p"];
    return o}).sort(function(a,b){return(b.bv+b.sv)-(a.bv+a.sv)});
  var held=pos.filter(function(o){return o.x!==null}),wins=held.filter(function(o){return o.x>=0}).length;
  var ty=classify(c),span=all.map(function(r){return r.d}).sort();
  var e=encodeURIComponent,q=e('"'+title(c).replace(/\b(LTD|LLP|PVT|HUF)\b\.?/g,"").trim()+'" stake');
  $("sm9-drawer").innerHTML='<button class="x" aria-label="Close">×</button><div class="mut" style="font-size:12px;text-transform:uppercase;letter-spacing:.06em">Investor history · '+dfmt(span[0])+" – "+dfmt(span[span.length-1])+'</div><h2 style="margin-top:4px">'+esc(title(c))+'</h2><p>'+badge(ty)+'</p>'+
   '<div class="mini"><div><span>Total bought</span><b class="g">'+(tb?cr(tb):"—")+'</b></div><div><span>Total sold</span><b class="r">'+(ts?cr(ts):"—")+'</b></div><div><span>Stocks traded</span><b>'+pos.length+'</b></div><div><span>Buys in profit</span><b class="'+(wins*2>=held.length?"g":"r")+'">'+(held.length?wins+" of "+held.length:"—")+'</b></div></div>'+
   '<div class="vlinks"><a href="https://news.google.com/search?q='+q+'&hl=en-IN&gl=IN&ceid=IN%3Aen" target="_blank" rel="noopener nofollow">News about this investor ↗</a><a class="nse" href="https://www.nseindia.com/report-detail/display-bulk-and-block-deals" target="_blank" rel="noopener">Verify on NSE ↗</a></div>'+
   '<h3 style="margin:14px 0 2px">Positions from bulk &amp; block deals</h3>'+pos.map(function(o){
     return'<div class="pos"><div style="min-width:0"><a href="#" data-sym="'+esc(o.s)+'" style="color:#fff;font-weight:800;text-decoration:none">'+esc(o.s)+'</a> <span class="mut" style="font-size:12px">'+esc(String(o.n).slice(0,28))+'</span>'+
       '<div class="sub">'+(o.bq?"Bought "+inr(o.bq)+" sh @ avg ₹"+o.ab.toFixed(2)+(o.nb>1?" · "+o.nb+" buys":""):"")+(o.bq&&o.sq?" · ":"")+(o.sq?"Sold "+inr(o.sq)+" sh @ avg ₹"+o.as.toFixed(2):"")+'</div>'+
       '<div class="sub">'+dfmt(o.first)+(o.first!==o.last?" → "+dfmt(o.last):"")+' · <span class="'+o.st[1]+'">'+o.st[0]+'</span></div></div>'+
       '<div style="text-align:right"><b class="mono">'+cr(o.bv-o.sv,true)+'</b>'+(o.x!==null?'<div class="sub '+(o.x>=0?"g":"r")+'">'+pct(o.x)+" vs avg buy</div>":"")+'</div></div>'}).join("")+
   '<h3 style="margin:16px 0 2px">Every deal</h3>'+all.slice().sort(function(a,b){return b.d.localeCompare(a.d)||b.v-a.v}).map(function(r){return'<div class="lead-row" style="grid-template-columns:auto 1fr auto;'+(r._ch?"opacity:.5":"")+'"><span class="act '+(r.b?"B":"S")+'">'+(r.b?"BUY":"SELL")+'</span><div style="min-width:0"><div class="who"><a href="#" data-sym="'+esc(r.s)+'" style="color:inherit;text-decoration:none">'+esc(r.s)+'</a></div><div class="sub">'+dfmt(r.d)+" · "+inr(r.q)+" sh @ ₹"+r.p+" · "+r.t+(r._ch?" · same-day churn":"")+(r.x!==null?' · <span class="'+(r.ok?"g":"r")+'">'+pct(r.x)+" since</span>":"")+'</div></div><b class="mono">'+cr(r.v)+"</b></div>"}).join("")+
   '<p class="disc">Only trades big enough to be reported as bulk or block deals are shown. "Holding" means no sell deal was reported, not a confirmed holding.</p>';
  $("sm9-drawer").scrollTop=0;$("sm9-drawer").classList.add("on");$("sm9-shade").classList.add("on");hideTip();
  try{history.replaceState(null,"","#investor-"+encodeURIComponent(c.toLowerCase().replace(/\s+/g,"-")))}catch(x){}
}
function closeDrawer(){$("sm9-drawer").classList.remove("on");$("sm9-shade").classList.remove("on");try{if(/^#(stock|investor)-/.test(location.hash))history.replaceState(null,"",location.pathname+location.search)}catch(e){}}
function fromHash(){var mi=/^#investor-(.+)$/.exec(location.hash);if(mi){var nm=decodeURIComponent(mi[1]).replace(/-/g," ").toUpperCase(),hit=DB.deals.filter(function(r){return r.c===nm||r.c.replace(/\s+/g," ")===nm})[0];if(hit)openInvestor(hit.c);return}var m=/^#stock-([A-Z0-9&%._-]+)$/i.exec(location.hash);if(m){var sym=decodeURIComponent(m[1]).toUpperCase();if(!VIEW.rows.some(function(r){return r.s===sym})){ST.per=30;setSeg("f-per","30");refresh()}openStock(sym)}}
window.addEventListener("hashchange",function(){if(DB)fromHash()});
$("sm9-shade").addEventListener("click",closeDrawer);
document.addEventListener("keydown",function(e){if(e.key==="Escape")closeDrawer()});
root.addEventListener("click",function(e){
  if(e.target.closest(".x"))return closeDrawer();
  var iv=e.target.closest("[data-inv]");if(iv){e.preventDefault();openInvestor(iv.dataset.inv);return}
  var s=e.target.closest("[data-sym]");if(s){e.preventDefault();openStock(s.dataset.sym);return}
  var sec=e.target.closest("[data-sec]");if(sec){ST.q="";$("f-q").value="";ST.river="sector";setSeg("f-river","sector");buildRiver();river.cv.scrollIntoView({behavior:"smooth",block:"center"})}
});

/* ---------- controls ---------- */
function setSeg(id,v){root.querySelectorAll("#"+id+" button").forEach(function(b){b.classList.toggle("on",b.dataset.v===String(v))})}
function seg(id,key,num){$(id).addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;ST[key]=num?+b.dataset.v:b.dataset.v;setSeg(id,b.dataset.v);if(key==="river"){buildRiver();return}refresh()})}
seg("f-per","per",true);seg("f-type","type");seg("f-river","river");
$("f-inv").addEventListener("change",function(){ST.inv=this.value;refresh()});
var qt;$("f-q").addEventListener("input",function(){var v=this.value;clearTimeout(qt);qt=setTimeout(function(){ST.q=v;refresh()},220)});
$("f-churn").addEventListener("change",function(){ST.churn=this.checked;refresh()});
$("f-bns").addEventListener("change",function(){ST.bns=this.checked;refresh()});
root.querySelectorAll(".tbl th").forEach(function(th){th.addEventListener("click",function(){var k=th.dataset.k;if(ST.sort===k)ST.dir*=-1;else{ST.sort=k;ST.dir=k==="v"||k==="d"||k==="q"?-1:1}ST.page=0;renderTable()})});
$("pg-prev").addEventListener("click",function(){ST.page--;renderTable()});$("pg-next").addEventListener("click",function(){ST.page++;renderTable()});
$("sm9-csv").addEventListener("click",function(){
  var lines=[["Date","Symbol","Security","Client","Investor type","Action","Qty","Price","Value (Rs Cr)","Deal type","Same-day churn","% since deal"].join(",")];
  sorted().forEach(function(r){lines.push([r.d,r.s,'"'+String(r.n).replace(/"/g,"'")+'"','"'+r.c.replace(/"/g,"'")+'"',TYPE[r._ty][0],r.b?"BUY":"SELL",r.q,r.p,r.v.toFixed(2),r.t,r._ch?"yes":"no",r.x===null?"":r.x.toFixed(1)].join(","))});
  var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([lines.join("\n")],{type:"text/csv"}));a.download="bulk-block-deals-9amtraders.csv";a.click()});

function refresh(){ST.page=0;compute();renderTop();buildRiver();buildSankey();buildBubbles();renderSectors();renderLeaders();renderWork();renderStreaks();renderTable();donut.k=0}

/* ---------- animation loop + reveal ---------- */
function loop(){drawRiver();drawSankey();drawBubbles();drawDonut();requestAnimationFrame(loop)}
var io="IntersectionObserver" in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");if(e.target.contains(donut.cv))donut.k=0;io.unobserve(e.target)}})},{threshold:.12}):null;
root.querySelectorAll(".card").forEach(function(c){io?io.observe(c):c.classList.add("in")});
var rt;window.addEventListener("resize",function(){clearTimeout(rt);rt=setTimeout(function(){buildRiver();sk.lay=null;buildBubbles()},200)});

/* ---------- load ---------- */
function start(d){
  DB=d;$("sm9-load").style.display="none";
  $("sm9-upd").textContent=d.demo?"demo preview":"updated "+d.updated;
  if(d.demo){$("sm9-banner").style.display="block";$("sm9-banner").innerHTML="<b>Demo preview — these are not real deals.</b> Live NSE bulk &amp; block deals will appear here automatically after the first daily update."}
  if(!d.dates||!d.dates.length){d.dates=[];}
  prep();refresh();setTimeout(fromHash,50);requestAnimationFrame(loop);
}
fetch(DATA_URL+"?t="+Math.floor(Date.now()/3e5),{cache:"no-store"}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){if(!d.deals||!d.deals.length)throw 0;start(d)}).catch(function(){start(demo())});
})();
