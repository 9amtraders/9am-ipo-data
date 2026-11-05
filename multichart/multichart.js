/* 9AM Multi-Chart — host at 9amtraders/9am-ipo-data/multichart/multichart.js (served by jsDelivr). Edit here, not in WordPress. */
(function(){
"use strict";
var REPO="https://raw.githubusercontent.com/9amtraders/9am-ipo-data/main/";
var PHASES_URL=REPO+"bubble/phases.json", CAL_URL=REPO+"multichart/calendar.json";
var BUBBLE_PAGE="/stock-market-bubble-phases-nifty-500/";
var root=document.getElementById("mc"),$=function(id){return document.getElementById(id)};
var LS="mc9am_";
function load(k,d){try{var v=localStorage.getItem(LS+k);return v?JSON.parse(v):d}catch(e){return d}}
function save(k,v){try{localStorage.setItem(LS+k,JSON.stringify(v))}catch(e){}}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function toast(t){var el=$("mc-toast");el.textContent=t;el.style.display="block";clearTimeout(toast.t);toast.t=setTimeout(function(){el.style.display="none"},3500)}

/* ---------------- symbols ---------------- */
// NSE data is not licensed for TradingView's free embedded charts ("only available on TradingView"),
// so stocks load from BSE and NSE indices map to the closest BSE index. All of these were tested live.
var ALIAS={NIFTY:"BSE:SNSX50",NIFTY50:"BSE:SNSX50",BANKNIFTY:"BSE:BANK",FINNIFTY:"BSE:FINSER",
 NIFTYIT:"BSE:IT",NIFTYPHARMA:"BSE:HC",NIFTYAUTO:"BSE:AUTO",NIFTYMETAL:"BSE:METAL",NIFTYFMCG:"BSE:FMCG",NIFTYREALTY:"BSE:REALTY",
 SENSEX:"BSE:SENSEX",SENSEX50:"BSE:SNSX50",BANKEX:"BSE:BANK",BSE500:"BSE:BSE500",BSE100:"BSE:BSE100",
 GOLD:"TVC:GOLD",SILVER:"TVC:SILVER",CRUDE:"TVC:USOIL",USDINR:"FX_IDC:USDINR",BTC:"BITSTAMP:BTCUSD",BITCOIN:"BITSTAMP:BTCUSD",DXY:"CAPITALCOM:DXY",SPX:"FOREXCOM:SPXUSD",SP500:"FOREXCOM:SPXUSD",DOW:"FOREXCOM:DJI",DJI:"FOREXCOM:DJI",EURUSD:"FX:EURUSD"};
// common nicknames -> NSE/BSE code
var NICK={JIO:"JIOFIN",JIOFINANCE:"JIOFIN",SBI:"SBIN",HUL:"HINDUNILVR",AIRTEL:"BHARTIARTL",IOCL:"IOC",INDIANOIL:"IOC",LNT:"LT","L&T":"LT",
 HDFC:"HDFCBANK",ICICI:"ICICIBANK",KOTAK:"KOTAKBANK",AXIS:"AXISBANK",MAHINDRA:"M&M",MM:"M&M",INFOSYS:"INFY",WIPRO:"WIPRO",ZOMATO:"ETERNAL",PAYTM:"PAYTM",NYKAA:"NYKAA",
 COALINDIA:"COALINDIA",BAJAJAUTO:"BAJAJ-AUTO",HAL:"HAL",BEL:"BEL",IRCTC:"IRCTC",RVNL:"RVNL",IRFC:"IRFC",TATASTEEL:"TATASTEEL",TATAMOTORS:"TATAMOTORS",ASIANPAINT:"ASIANPAINT"};
var SWAPNOTE={NIFTY:"Nifty isn't allowed in free charts — showing Sensex 50, the closest index.",NIFTY50:"Nifty isn't allowed in free charts — showing Sensex 50, the closest index.",BANKNIFTY:"Bank Nifty isn't allowed in free charts — showing BSE Bankex instead."};
var NSEIDX={"NSE:NIFTY":"BSE:SNSX50","NSE:BANKNIFTY":"BSE:BANK","NSE:CNXIT":"BSE:IT","NSE:CNXPHARMA":"BSE:HC","NSE:CNXAUTO":"BSE:AUTO","NSE:CNXMETAL":"BSE:METAL","NSE:CNXFMCG":"BSE:FMCG","NSE:CNXREALTY":"BSE:REALTY","NSE:CNXFINANCE":"BSE:FINSER","NSE:INDIAVIX":"BSE:SENSEX"};
function fixNSE(sym){if(NSEIDX[sym])return NSEIDX[sym];return String(sym).indexOf("NSE:")==0?"BSE:"+sym.slice(4):sym}
var TFN={"1":"1m","5":"5m","15":"15m","60":"1h","240":"4h","D":"Day","W":"Week","M":"Month"};
function cleanName(n){return String(n||"").toLowerCase().replace(/&/g," and ").replace(/\b(ltd|limited|corp|corporation|co|company|the|india|of)\b\.?/g," ").replace(/[^a-z0-9 ]/g," ").replace(/\s+/g," ").trim()}
function matches(q){
 if(!PDATA)return[];var Q=String(q||"").trim();if(Q.length<2)return[];var U=Q.toUpperCase().replace(/\s+/g,""),L=cleanName(Q),out=[];
 var nick=NICK[U];PDATA.stocks.forEach(function(st){var sc=0,nm=cleanName(st.n),sym=st.s;
  if(nick&&sym==nick)sc=100;else if(sym==U)sc=95;else if(sym.indexOf(U)==0)sc=80;else if(nm.indexOf(L)==0)sc=75;
  else if(L&&(" "+nm).indexOf(" "+L)>=0)sc=60;else if(L.length>=3&&nm.replace(/ /g,"").indexOf(L.replace(/ /g,""))>=0)sc=50;
  if(sc)out.push({s:sym,n:st.n,sc:sc-nm.length/100})});
 return out.sort(function(a,b){return b.sc-a.sc}).slice(0,8)}
function norm(s){var raw=String(s||"").trim(),best=matches(raw)[0];s=raw.toUpperCase().replace(/\s+/g,"");if(!s)return"";
 if(NICK[s])return"BSE:"+NICK[s];
 if(best&&s.indexOf(":")<0&&!ALIAS[s])return"BSE:"+best.s;
 if(s=="VIX"||s=="INDIAVIX"){toast("India VIX isn't available in free charts.");return""}
 if(SWAPNOTE[s])toast(SWAPNOTE[s]);
 if(s.indexOf(":")>0){if(s.indexOf("NSE:")==0)toast("NSE isn't allowed in free charts — showing the BSE chart (same company).");return fixNSE(s)}
 return ALIAS[s]||("BSE:"+s)}
function base(sym){var p=String(sym).split(":");return p[p.length-1]}
// TradingView writes "&" and "-" in Indian stock codes as "_" (M&M -> M_M, BAJAJ-AUTO -> BAJAJ_AUTO)
// Free widgets give BSE (Indian) symbols end-of-day data only: Daily, Weekly, Monthly
var EOD_TF=["D","W","M"];function isEOD(sym){return /^BSE:/.test(String(sym))}
function okTF(sym,tf){return isEOD(sym)&&EOD_TF.indexOf(tf)<0?"D":tf}
function tvSym(sym){var p=String(sym).split(":");if(p.length<2)return sym;return p[0]+":"+p[1].replace(/[&-]/g,"_")}

/* ---------------- state ---------------- */
var small=window.matchMedia("(max-width:760px)").matches;
var DEF={lay:small?2:4,theme:"light",link:false,sel:0,charts:[{s:"BSE:SENSEX",tf:"D"},{s:"BSE:BANK",tf:"D"},{s:"FX_IDC:USDINR",tf:"15"},{s:"TVC:GOLD",tf:"15"}],strat:""};
var cfg=Object.assign({},DEF,load("screen",{}));
cfg.charts=(cfg.charts&&cfg.charts.length==4)?cfg.charts:DEF.charts.slice();
cfg.charts.forEach(function(c){c.s=fixNSE(c.s)});  // older saved screens used NSE symbols
(function fromURL(){var u=new URLSearchParams(location.search);if(!u.get("c"))return;
 var c=u.get("c").split(",").slice(0,4).map(function(x){var p=x.split("~");return{s:norm(p[0]),tf:TFN[p[1]]?p[1]:"D"}});
 while(c.length<4)c.push(DEF.charts[c.length]);cfg.charts=c;var l=+u.get("l");if(l==1||l==2||l==4)cfg.lay=l})();
function persist(){save("screen",cfg)}

/* ---------------- TradingView loader ---------------- */
var tvReady=false,tvFail=false,tvQ=[],mountSeq=0;
(function(){var s=document.createElement("script");s.src="https://s3.tradingview.com/tv.js";s.async=true;
 s.onload=function(){tvReady=!!window.TradingView;tvQ.splice(0).forEach(function(f){f()})};
 s.onerror=function(){tvFail=true;tvQ.splice(0).forEach(function(f){f()})};document.head.appendChild(s)})();
function whenTV(f){if(tvReady||tvFail)f();else tvQ.push(f)}

/* ---------------- strategies & presets ---------------- */
var EMA200={id:"MAExp@tv-basicstudies",inputs:{length:200}},VOL="Volume@tv-basicstudies",RSI="RSI@tv-basicstudies",BB="BB@tv-basicstudies",VWAP="VWAP@tv-basicstudies",MACD="MACD@tv-basicstudies";
var STRATS={
 hi52:{n:"52-Week High Breakout",tf:["D","W","M","D"],extra:[null,null,null,"BSE:SENSEX"],st:[[VOL],[VOL],[],[]],
  ck:["Price is within 3% of its 52-week high","Daily candle CLOSES above the 52-week high","Volume on the breakout day is at least 1.5x normal","The weekly and monthly charts are also in an uptrend","Sensex (bottom right) is not in a sharp fall","Decide your stop loss before you enter"],
  tip:"52-week high todna matlab saal bhar ke sab sellers ab nuksaan mein nahi hain — upar supply kam hoti hai. Par close aur volume dono confirm karo."},
 ema:{n:"200 EMA Pullback",tf:["D","W","M","D"],extra:[null,null,null,"BSE:SENSEX"],st:[[EMA200],[EMA200],[],[EMA200]],
  ck:["Daily price is above a RISING 200 EMA","Price pulls back close to the 200 EMA or a support level","Sensex is not in a sharp fall (bottom-right chart)","A bullish daily candle forms near the 200 EMA or support","Stop loss below the pullback low"],
  tip:"Trend tumhara dost hai: 200 EMA upar ki taraf ho tabhi pullback dhoondo. Girte EMA pe 'sasta' samajh ke mat kharido."},
 brk:{n:"Breakout + Volume",tf:["D","W","M","D"],extra:[null,null,null,"BSE:SENSEX"],st:[[VOL],[VOL],[VOL],[]],
  ck:["Clear resistance touched at least 2 times before","Daily candle CLOSES above resistance","Volume on breakout day is at least 1.5x normal","Weekly and monthly charts also look strong — not right under a big resistance","Plan what you will do if price falls back below the breakout level"],
  tip:"Volume ke bina breakout aksar fake hota hai. Close above resistance + zyada volume = asli breakout ka pehla sign."},
 rsi:{n:"RSI Divergence",tf:["D","W","M","D"],extra:[null,null,null,"BSE:SENSEX"],st:[[RSI],[RSI],[RSI],[]],
  ck:["Price makes a new high (or low)","RSI makes a LOWER high (or HIGHER low) at the same time","Divergence appears on at least 2 timeframes","Wait for a confirming candle — divergence alone is not an entry","Stop loss beyond the latest swing high/low"],
  tip:"Price naya high bana raha hai par RSI nahi — matlab andar se taakat kam ho rahi hai. Par confirmation candle ka wait zaroori hai."},
 bb:{n:"Bollinger Squeeze",tf:["D","W","M","D"],extra:[null,null,null,"BSE:SENSEX"],st:[[BB],[BB],[BB],[]],
  ck:["Bollinger Bands are the narrowest in about 3 months","Volume is drying up during the squeeze","Wait for a close outside the bands","Trade in the direction of the break, not before it","Stop loss back inside the bands"],
  tip:"Jab bands bahut patle ho jaate hain, bada move aane wala hota hai — par direction pehle se koi nahi jaanta. Break ka wait karo."}
};
var PRESETS={
 mtf:{n:"Multi-timeframe: selected symbol (Month / Week / Day)"},
 morning:{n:"Morning check: Sensex, Bankex, USD/INR, Gold",c:[["BSE:SENSEX","D"],["BSE:BANK","D"],["FX_IDC:USDINR","15"],["TVC:GOLD","15"]]},
 commod:{n:"Commodities intraday: Gold, Silver, Crude, USD/INR (15m)",c:[["TVC:GOLD","15"],["TVC:SILVER","15"],["TVC:USOIL","15"],["FX_IDC:USDINR","15"]]},
 sector:{n:"Sector rotation: IT, Healthcare, Auto, Metal",c:[["BSE:IT","D"],["BSE:HC","D"],["BSE:AUTO","D"],["BSE:METAL","D"]]},
 sector2:{n:"Sector rotation 2: Bankex, FMCG, Capital Goods, Power",c:[["BSE:BANK","D"],["BSE:FMCG","D"],["BSE:CG","D"],["BSE:POWER","D"]]},
 global:{n:"Global cues: Sensex, S&P 500, Dollar index, Crude",c:[["BSE:SENSEX","D"],["FOREXCOM:SPXUSD","D"],["CAPITALCOM:DXY","D"],["TVC:USOIL","D"]]},
 metals:{n:"Gold vs Silver vs USD/INR vs Sensex",c:[["TVC:GOLD","D"],["TVC:SILVER","D"],["FX_IDC:USDINR","D"],["BSE:SENSEX","D"]]},
 stocksector:{n:"Selected stock vs Sensex vs its sector"}
};

/* ---------------- charts ---------------- */
function studiesFor(i){var s=cfg.strat&&STRATS[cfg.strat];return s?s.st[i]||[]:[]}
var LAZY=window.IntersectionObserver?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){LAZY.unobserve(e.target);var i=+e.target.getAttribute("data-i");if(e.target.getAttribute("data-pending")){e.target.removeAttribute("data-pending");mountNow(i)}}})},{rootMargin:"250px"}):null;
function mount(i){var box=$("mc-tv-"+i);if(!box)return;
 var lazyFrom=window.matchMedia("(max-width:760px)").matches?1:2;
 if(LAZY&&i>=lazyFrom&&!root.classList.contains("focus")){var r=box.getBoundingClientRect();if(r.top>window.innerHeight+250){box.setAttribute("data-i",i);box.setAttribute("data-pending","1");box.innerHTML='<div class="msg">Chart loads when you scroll here…</div>';LAZY.observe(box);return}}
 mountNow(i)}
function mountNow(i){
 var box=$("mc-tv-"+i);if(!box)return;var c=cfg.charts[i],id="mc-w"+i+"-"+(++mountSeq);c.tf=okTF(c.s,c.tf);
 box.innerHTML='<div id="'+id+'" style="height:100%"></div><div class="msg" style="z-index:-1">Loading chart…</div>';
 whenTV(function(){
  if(!window.TradingView){box.innerHTML='<div class="msg">Chart could not load. Check your connection or ad-blocker, then refresh.</div>';return}
  try{new window.TradingView.widget({autosize:true,symbol:tvSym(c.s),interval:c.tf,timezone:"Asia/Kolkata",theme:cfg.theme,style:"1",locale:"in",
   allow_symbol_change:false,hide_side_toolbar:cfg.lay==4,withdateranges:cfg.lay!=4,save_image:false,studies:studiesFor(i),container_id:id})}
  catch(e){box.innerHTML='<div class="msg">Chart could not load.</div>'}
 });
}
function badge(sym){var b=PH&&PH[base(sym)];if(!b)return"";var P=PHN[b.p];
 return'<a class="badge" style="--c:'+P.c+'" href="'+BUBBLE_PAGE+'" target="_blank" rel="noopener" title="Bubble Phase Meter: '+esc(b.st)+'">'+P.n+(b.days!=null?' · '+b.days+(b.known===false?"+":"")+'d':"")+'</a>'}
function header(i){var c=cfg.charts[i],nn=notesFor(c.s).length;
 return'<span class="sym">'+esc(base(c.s))+'</span><select data-tf="'+i+'" aria-label="Timeframe">'+Object.keys(TFN).filter(function(k){return !isEOD(c.s)||EOD_TF.indexOf(k)>=0}).map(function(k){return'<option value="'+k+'"'+(k==c.tf?" selected":"")+'>'+TFN[k]+'</option>'}).join("")+'</select>'
 +badge(c.s)+(nn?'<span class="nt">📝 '+nn+'</span>':"")+'<span class="sp"></span><span class="fine">'+esc(c.s.split(":")[0])+'</span>'}
function buildGrid(){
 var g=$("mc-grid"),n=cfg.lay;g.className="grid l"+n;var h="";
 for(var i=0;i<n;i++)h+='<div class="card pane'+(cfg.sel==i?" on":"")+'" data-p="'+i+'"><div class="ph" id="mc-ph-'+i+'">'+header(i)+'</div><div class="tv" id="mc-tv-'+i+'"></div></div>';
 g.innerHTML=h;for(var j=0;j<n;j++)mount(j);
 [].forEach.call($("mc-lay").children,function(b){b.classList.toggle("on",+b.getAttribute("data-l")==n)});
}
function refreshHeaders(){for(var i=0;i<cfg.lay;i++){var el=$("mc-ph-"+i);if(el)el.innerHTML=header(i)}}
function selectPane(i){if(i>=cfg.lay)i=0;cfg.sel=i;[].forEach.call($("mc-grid").children,function(p,k){p.classList.toggle("on",k==i)});persist();renderNotes();news()}
function setChart(i,s,tf,noMount){var want=tf||cfg.charts[i].tf,got=okTF(s,want);if(got!=want)toast("Indian stocks show Daily, Weekly and Monthly charts only in free TradingView charts.");cfg.charts[i]={s:s,tf:got};if(!noMount&&i<cfg.lay){mount(i);var el=$("mc-ph-"+i);if(el)el.innerHTML=header(i)}}
function apply(list){list.forEach(function(c,i){cfg.charts[i]={s:c[0],tf:c[1]}});if(cfg.lay<4&&list.length>=4&&!small)cfg.lay=4;persist();buildGrid();renderNotes();news()}

/* ---------------- bubble phases (for badges, Today's 4, note prices) ---------------- */
var PH=null,PDATA=null,PHN={stealth:{n:"Stealth",c:"var(--st)"},awareness:{n:"Awareness",c:"var(--aw)"},mania:{n:"Mania",c:"var(--ma)"},blowoff:{n:"Blow-off",c:"var(--bo)"},out:{n:"Out of cycle",c:"var(--ou)"}};
fetch(PHASES_URL,{cache:"no-store"}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){
 PDATA=d;PH={};d.stocks.forEach(function(s){PH[s.s]=s});
 refreshHeaders();renderNotes();
}).catch(function(){});

function todays4(){
 if(!PDATA){toast("Today's picks are loading — try again in a moment.");return null}
 var S=PDATA.stocks,used={};
 function best(f,key,dir,why){var c=S.filter(function(s){return f(s)&&!used[s.s]}).sort(function(a,b){return dir*(b[key]-a[key])})[0];if(c){used[c.s]=1;return{s:c,why:why(c)}}return null}
 var picks=[
  best(function(s){return s.p=="mania"&&s.was},"d200",1,function(s){return"New in Mania: "+(s.d200>0?"+":"")+s.d200+"% above its 200-day average."})||best(function(s){return s.p=="mania"},"d200",1,function(s){return"Most stretched Mania stock: "+s.d200+"% above its 200-day average."}),
  best(function(s){return s.p=="awareness"&&s.was=="stealth"},"d1",1,function(s){return"Just moved from Stealth to Awareness — a quiet base turning into an uptrend."})||best(function(s){return s.st=="Take off"},"d1",1,function(s){return"In 'Take off': just started rising above its 200-day average."}),
  best(function(s){return s.p=="blowoff"&&s.was},"d1",-1,function(s){return"Fell into Blow-off: now "+s.dd+"% from its 52-week high."})||best(function(s){return s.p=="blowoff"},"d1",-1,function(s){return"Blow-off stock with the biggest fall today ("+s.d1+"%)."}),
  best(function(s){return true},"vr",1,function(s){return"Biggest volume surge: "+s.vr+"x its normal volume."})
 ].filter(Boolean);
 return picks;
}

/* ---------------- notes ---------------- */
var NOTES=load("notes",[]);
function notesFor(sym){return NOTES.filter(function(n){return n.s==sym})}
function nowClose(sym){var b=PH&&PH[base(sym)];return b&&/^(BSE|NSE):/.test(String(sym))?b.c:null}
function sinceHTML(n){var cur=nowClose(n.s);if(!n.p||!cur)return"";var ch=(cur/n.p-1)*100;
 return'<div class="since '+(ch>=0?"up":"dn")+'">📝 Noted at ₹'+n.p.toLocaleString("en-IN")+' → now ₹'+cur.toLocaleString("en-IN")+' ('+(ch>=0?"+":"")+ch.toFixed(1)+'%)</div>'}
function fmtDate(iso){var d=new Date(iso);return d.toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"})}
var showAll=false;
function renderNotes(){
 var c=cfg.charts[cfg.sel],list=(showAll?NOTES:notesFor(c.s)).slice().sort(function(a,b){return b.t-a.t}),auto=nowClose(c.s);
 var h='<h3>'+(showAll?"All notes":"Notes for "+esc(base(c.s)))+'</h3>'
 +'<textarea id="mc-ntext" placeholder="e.g. Waiting for a close above 2,950. Stop below 2,880."></textarea>'
 +'<div class="row"><input id="mc-nprice" inputmode="decimal" placeholder="Price" value="'+(auto||"")+'"><select class="sel" id="mc-ntag" style="max-width:none;flex:1"><option value="">No strategy tag</option>'
 +Object.keys(STRATS).map(function(k){return'<option value="'+k+'"'+(cfg.strat==k?" selected":"")+'>'+STRATS[k].n+'</option>'}).join("")+'</select></div>'
 +'<div class="row"><button class="btn hot" id="mc-nadd">Save note</button><button class="btn" id="mc-nall">'+(showAll?"This chart only":"All notes ("+NOTES.length+")")+'</button></div>'
 +'<p class="fine">'+(auto?"Price auto-filled from the latest closing price"+(PDATA?" ("+esc(PDATA.date)+")":"")+".":"Type the price to track how your idea plays out.")+' Notes stay in this browser only.</p>';
 if(!list.length)h+='<p class="fine" style="margin-top:12px">No notes yet.</p>';
 list.forEach(function(n){h+='<div class="note"><div class="h"><span><b data-go="'+esc(n.s)+'">'+esc(base(n.s))+'</b> · '+fmtDate(n.t)+(n.g&&STRATS[n.g]?' · '+STRATS[n.g].n:"")+'</span><button class="x" data-del="'+n.id+'" aria-label="Delete note">✕</button></div><div class="t">'+esc(n.x)+'</div>'+sinceHTML(n)+'</div>'});
 h+='<div class="row" style="margin-top:12px"><button class="btn" id="mc-exp-n">⬇ Export</button><label class="btn">⬆ Import<input type="file" id="mc-imp" accept=".json,application/json" hidden></label></div>';
 $("mc-tb-notes").innerHTML=h;
}
function addNote(){var x=$("mc-ntext").value.trim();if(!x){$("mc-ntext").focus();return}
 var c=cfg.charts[cfg.sel],p=parseFloat(String($("mc-nprice").value).replace(/,/g,""));
 NOTES.push({id:Date.now().toString(36)+Math.random().toString(36).slice(2,6),s:c.s,x:x,t:Date.now(),p:isFinite(p)&&p>0?p:null,g:$("mc-ntag").value||null});
 save("notes",NOTES);renderNotes();refreshHeaders();toast("Note saved")}
function exportNotes(){var blob=new Blob([JSON.stringify({app:"9am-multichart",v:1,exported:new Date().toISOString(),notes:NOTES},null,1)],{type:"application/json"});
 var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="9am-notes-"+new Date().toISOString().slice(0,10)+".json";document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},500)}
function importNotes(file){var r=new FileReader();r.onload=function(){try{var d=JSON.parse(r.result),inc=(d.notes||d).filter(function(n){return n&&n.s&&n.x&&n.t});
 var have={};NOTES.forEach(function(n){have[n.id]=1});var added=0;inc.forEach(function(n){if(!have[n.id]){NOTES.push({id:String(n.id||Date.now()),s:String(n.s),x:String(n.x),t:+n.t,p:+n.p||null,g:n.g||null});added++}});
 save("notes",NOTES);renderNotes();refreshHeaders();toast(added+" notes imported")}catch(e){toast("That file is not a 9AM notes backup.")}};r.readAsText(file)}

/* ---------------- strategy tab ---------------- */
function renderStrat(){
 var k=cfg.strat,s=STRATS[k],h="";
 if(!s){h='<h3>Strategy setups</h3><p>Pick a setup and the 4 charts switch to the right timeframes and indicators for the selected stock, with a checklist here.</p>'
  +Object.keys(STRATS).map(function(x){return'<div class="pick" style="--c:var(--navy)" data-st="'+x+'"><b>'+STRATS[x].n+'</b></div>'}).join("")
  +'<p class="fine">Learning checklists, not buy or sell calls.</p>'}
 else{var day=new Date().toISOString().slice(0,10),ticks=load("ck_"+k,{});if(ticks.d!=day)ticks={d:day,v:{}};
  h='<h3>'+s.n+'</h3><p class="fine">For '+esc(base(cfg.charts[0].s))+' · ticks reset every day</p>'
  +s.ck.map(function(t,i){return'<label class="ck"><input type="checkbox" data-ck="'+i+'"'+(ticks.v[i]?" checked":"")+'><span>'+esc(t)+'</span></label>'}).join("")
  +'<div class="tip">💡 '+esc(s.tip)+'</div>'
  +'<div class="row"><button class="btn" data-st="">Leave strategy</button><button class="btn" id="mc-stn">📝 Note with this tag</button></div>'
  +'<p class="fine">Indicators are pre-loaded where the free chart allows. Learning checklist only — not advice.</p>'}
 $("mc-tb-strat").innerHTML=h;
}
function useStrat(k){
 cfg.strat=k;$("mc-strat").value=k;
 if(k){var s=STRATS[k],main=cfg.charts[cfg.sel].s;apply(s.tf.map(function(tf,i){return[s.extra[i]||main,tf]}));cfg.sel=0;persist()}
 else{persist();buildGrid()}
 renderStrat();showTab("strat");
}

/* ---------------- news ---------------- */
var newsSym=null;
function news(){var s=cfg.charts[cfg.sel].s;if(s==newsSym||!$("mc-tb-news").classList.contains("on"))return;newsSym=s;
 var box=$("mc-news");box.innerHTML='<h3>News: '+esc(base(s))+'</h3><div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div></div><p class="fine">Headlines by TradingView. Coverage for smaller Indian stocks can be limited.</p>';
 var sc=document.createElement("script");sc.src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js";sc.async=true;
 sc.text=JSON.stringify({feedMode:"symbol",symbol:tvSym(s),isTransparent:true,displayMode:"regular",width:"100%",height:560,colorTheme:cfg.theme,locale:"in"});
 box.querySelector(".tradingview-widget-container").appendChild(sc)}

/* ---------------- tabs ---------------- */
function showTab(t){[].forEach.call($("mc-tabs").children,function(b){b.classList.toggle("on",b.getAttribute("data-t")==t)});
 ["notes","strat","news","alerts"].forEach(function(x){$("mc-tb-"+x).classList.toggle("on",x==t)});if(t=="news"){newsSym=null;news()}}

/* ---------------- calendar, clock, session, expiry ---------------- */
var CAL={holidays:[{d:"2026-01-15",n:"Municipal Corporation Election (Maharashtra)"},{d:"2026-01-26",n:"Republic Day"},{d:"2026-03-03",n:"Holi"},{d:"2026-03-26",n:"Shri Ram Navami"},{d:"2026-03-31",n:"Shri Mahavir Jayanti"},{d:"2026-04-03",n:"Good Friday"},{d:"2026-04-14",n:"Dr. Baba Saheb Ambedkar Jayanti"},{d:"2026-05-01",n:"Maharashtra Day"},{d:"2026-05-28",n:"Bakri Id"},{d:"2026-06-26",n:"Muharram"},{d:"2026-09-14",n:"Ganesh Chaturthi"},{d:"2026-10-02",n:"Mahatma Gandhi Jayanti"},{d:"2026-10-20",n:"Dussehra"},{d:"2026-11-10",n:"Diwali Balipratipada"},{d:"2026-11-24",n:"Prakash Gurpurb Sri Guru Nanak Dev"},{d:"2026-12-25",n:"Christmas"}],
 special:[{d:"2026-11-08",n:"Muhurat trading (Sunday) - timings as per NSE circular"}],
 expiries:[{label:"Nifty 50 weekly",dow:2,monthly:false},{label:"Monthly F&O (Nifty, Bank Nifty, stocks)",dow:2,monthly:true},{label:"Sensex weekly (BSE)",dow:4,monthly:false}]};
var HOL={};function idxHol(){HOL={};CAL.holidays.forEach(function(h){HOL[h.d]=h.n})}idxHol();
fetch(CAL_URL,{cache:"no-store"}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){if(d&&d.holidays){CAL=d;idxHol();lastDay=""}}).catch(function(){});

var offset=0,synced=false,syncNote="";
var IST=5.5*3600e3;
function now(){return Date.now()+offset}
function ist(t){var d=new Date(t+IST);return{y:d.getUTCFullYear(),mo:d.getUTCMonth(),d:d.getUTCDate(),dow:d.getUTCDay(),h:d.getUTCHours(),mi:d.getUTCMinutes(),s:d.getUTCSeconds(),ms:d.getUTCMilliseconds(),
 key:d.toISOString().slice(0,10),sec:d.getUTCHours()*3600+d.getUTCMinutes()*60+d.getUTCSeconds()+d.getUTCMilliseconds()/1000}}
function sample(url,parse){var t0=Date.now();return fetch(url+(url.indexOf("?")>0?"&":"?")+"_="+t0,{cache:"no-store"}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){var t1=Date.now(),srv=parse(j);if(!isFinite(srv))throw 0;return{off:srv+(t1-t0)/2-t1,rtt:t1-t0}})}
var SOURCES=[["https://timeapi.io/api/time/current/zone?timeZone=UTC",function(j){return Date.parse(String(j.dateTime).slice(0,23)+"Z")}],
 ["https://worldtimeapi.org/api/timezone/Etc/UTC",function(j){return Date.parse(j.utc_datetime)}]];
function headerSync(){var t0=Date.now();return fetch(location.href,{method:"HEAD",cache:"no-store"}).then(function(r){var t1=Date.now(),d=Date.parse(r.headers.get("Date"));if(!isFinite(d))throw 0;return{off:d+500+(t1-t0)/2-t1,rtt:t1-t0,rough:true}})}
function syncClock(){
 var src=SOURCES.slice(),out=[];
 function next(){if(!src.length)return finish();var s=src.shift();
  var go=function(n){if(!n)return next();sample(s[0],s[1]).then(function(r){out.push(r);go(n-1)}).catch(next)};go(3)}
 function finish(){
  if(out.length){out.sort(function(a,b){return a.rtt-b.rtt});var b=out[0];offset=b.off;synced=true;
   var err=Math.max(10,Math.round(b.rtt/2));syncNote="Synced ±"+err+" ms";}
  else return headerSync().then(function(r){offset=r.off;synced=true;syncNote="Roughly synced (±1 s)"}).catch(function(){synced=false;syncNote="Using your device clock (could not sync)"}).then(showSync);
  showSync()}
 next();
}
function showSync(){var o=-offset,abs=Math.abs(o)/1000,dev=synced&&abs>=0.2?" · Your clock is "+abs.toFixed(1)+" s "+(o>0?"fast":"slow"):"";$("mc-sync").textContent=syncNote+dev}
syncClock();setInterval(syncClock,10*60e3);

function isTrading(key,dow){return dow>0&&dow<6&&!HOL[key]}
function keyAdd(key,n){var d=new Date(key+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
function dowOf(key){return new Date(key+"T00:00:00Z").getUTCDay()}
function prevTrading(key){var k=key;for(var i=0;i<10;i++){if(isTrading(k,dowOf(k)))return k;k=keyAdd(k,-1)}return key}
function lastDowOfMonth(y,mo,dow){var d=new Date(Date.UTC(y,mo+1,0));while(d.getUTCDay()!=dow)d.setUTCDate(d.getUTCDate()-1);return d.toISOString().slice(0,10)}
function nextExpiry(e,today,afterClose){
 if(e.monthly){var t=new Date(today+"T00:00:00Z");for(var m=0;m<3;m++){var y=t.getUTCFullYear(),mo=t.getUTCMonth()+m;var k=prevTrading(lastDowOfMonth(y+Math.floor(mo/12),mo%12,e.dow));
   if(k>today||(k==today&&!afterClose))return{k:k,sched:lastDowOfMonth(y+Math.floor(mo/12),mo%12,e.dow)}}}
 else{for(var i=0;i<21;i++){var s=keyAdd(today,i);if(dowOf(s)!=e.dow)continue;var k2=prevTrading(s);if(k2>today||(k2==today&&!afterClose))return{k:k2,sched:s}}}
 return null}
function fmtK(k){var d=new Date(k+"T00:00:00Z");return["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][d.getUTCDay()]+" "+d.getUTCDate()+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d.getUTCMonth()]}
function hms(sec,ms){sec=Math.max(0,sec);var d=Math.floor(sec/86400);sec-=d*86400;var h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=Math.floor(sec%60),f=Math.floor((sec%1)*1000);
 return(d?d+"d ":"")+String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0")+(ms?"."+String(f).padStart(3,"0"):"")}
var SESS=[[0,9*3600,"Pre-market","Pre-open starts in"],[9*3600,9*3600+15*60,"Pre-open session","Market opens in"],[9*3600+15*60,15*3600+30*60,"Market open","Market closes in"],[15*3600+30*60,16*3600,"Post-close session","Post-close ends in"],[16*3600,86400,"Market closed","Next pre-open in"]];
function nextOpenSec(t){var k=t.key;for(var i=1;i<15;i++){var n=keyAdd(k,i);if(isTrading(n,dowOf(n)))return i*86400-t.sec+9*3600}return 0}
var lastDay="",lastTx="";
function tick(){
 var T=now(),t=ist(T);
 var tx=String(t.h).padStart(2,"0")+":"+String(t.mi).padStart(2,"0")+":"+String(t.s).padStart(2,"0");if(tx==lastTx)return;lastTx=tx;
 $("mc-time").innerHTML=tx+' <small style="color:var(--mute);font-size:.6em">IST</small>';
 var trading=isTrading(t.key,t.dow),name,count,fill=0;
 if(!trading){name=HOL[t.key]?"Market holiday: "+HOL[t.key]:"Weekend — market closed";count="Next pre-open in "+hms(nextOpenSec(t))}
 else{for(var i=0;i<SESS.length;i++){var s=SESS[i];if(t.sec>=s[0]&&t.sec<s[1]){name=s[2];var left=(i==4?nextOpenSec(t):s[1]-t.sec);if(i==0)left=9*3600-t.sec;count=s[3]+" "+hms(left);break}}
  fill=t.sec<9*3600+15*60?0:Math.min(1,(t.sec-(9*3600+15*60))/(6.25*3600))}
 $("mc-sname").textContent=name;$("mc-scount").textContent=count;$("mc-sfill").style.width=(fill*100)+"%";
 $("mc-spre").style.cssText="left:0;width:"+(trading&&t.sec>=9*3600&&t.sec<9*3600+15*60?"100%":"0")+";";
 var mk=t.key+(t.sec>=15*3600+30*60?"a":"b");if(mk!=lastDay){lastDay=mk;dayStuff(t)}
}
function dayStuff(t){
 var hol=$("mc-hol"),sp=(CAL.special||[]).filter(function(x){return x.d==t.key})[0],nh=null;
 for(var i=0;i<=3;i++){var k=keyAdd(t.key,i);if(HOL[k]){nh={k:k,n:HOL[k]};break}}
 if(sp){hol.style.display="block";hol.textContent="📅 Today: "+sp.n}
 else if(nh){hol.style.display="block";hol.textContent="📅 "+(nh.k==t.key?"Today":fmtK(nh.k))+": NSE closed for "+nh.n+"."}else hol.style.display="none";
 var after=t.sec>=15*3600+30*60;
 $("mc-exp").innerHTML=(CAL.expiries||[]).map(function(e){var x=nextExpiry(e,t.key,after);if(!x)return"";var days=Math.round((Date.parse(x.k)-Date.parse(t.key))/864e5);
  return'<div>'+esc(e.label)+': <b>'+(days==0?"Today":fmtK(x.k))+'</b>'+(x.k!=x.sched?' <span class="fine">(moved from '+fmtK(x.sched)+', holiday)</span>':"")+(days>0?' <span class="fine">· '+days+'d</span>':"")+'</div>'}).join("");
}

/* ---------------- alerts ---------------- */
var ALR=load("alerts",[{t:"09:14:50",on:true,l:"Market opens in 10 seconds"},{t:"15:15:00",on:true,l:"15 minutes to market close"},{t:"15:29:50",on:true,l:"Market closes in 10 seconds"}]);
var sound=load("sound",false),actx=null,fired={};
function beep(){try{actx=actx||new(window.AudioContext||window.webkitAudioContext)();var o=actx.createOscillator(),g=actx.createGain();o.type="sine";o.frequency.value=880;g.gain.setValueAtTime(.0001,actx.currentTime);
 g.gain.exponentialRampToValueAtTime(.3,actx.currentTime+.02);g.gain.exponentialRampToValueAtTime(.0001,actx.currentTime+.6);o.connect(g).connect(actx.destination);o.start();o.stop(actx.currentTime+.65)}catch(e){}}
function alarms(t,trading){
 if(!trading)return;var nowS=t.sec;
 ALR.forEach(function(a,i){if(!a.on)return;var p=a.t.split(":"),at=(+p[0])*3600+(+p[1])*60+(+(p[2]||0)),id=t.key+"|"+i+"|"+a.t;
  if(nowS>=at&&nowS<at+2&&!fired[id]){fired[id]=1;toast("⏰ "+(a.l||a.t));if(sound){beep();setTimeout(beep,700)}}})}
function renderAlerts(){
 var h='<h3>Time alerts (IST, trading days)</h3>'+ALR.map(function(a,i){return'<div class="al"><input type="checkbox" data-aon="'+i+'"'+(a.on?" checked":"")+'><code>'+esc(a.t)+'</code><span>'+esc(a.l||"")+'</span><button class="x" data-adel="'+i+'" aria-label="Delete alert">✕</button></div>'}).join("")
 +'<div class="row" style="margin-top:10px"><input type="time" step="1" id="mc-at" value="15:00:00" style="width:130px"><input id="mc-al" placeholder="Label" style="flex:1;min-width:0;width:auto"><button class="btn" id="mc-aadd">Add</button></div>'
 +'<div class="row"><button class="btn'+(sound?" hot":"")+'" id="mc-snd">'+(sound?"🔔 Sound on":"🔕 Sound off — tap to enable")+'</button></div>'
 +'<p class="fine">Alerts work while this page is open. Browsers need one tap on the sound button before they allow beeps.</p>';
 $("mc-al-body").innerHTML=h}

/* ---------------- share, focus, dark ---------------- */
function shareLink(){var u=location.origin+location.pathname+"?l="+cfg.lay+"&c="+cfg.charts.slice(0,cfg.lay).map(function(c){return c.s+"~"+c.tf}).join(",");
 (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){toast("Link copied — paste it in WhatsApp or Telegram")}).catch(function(){prompt("Copy this link:",u)})}
function focusMode(on){if(on==null)on=!root.classList.contains("focus");root.classList.toggle("focus",on);
 if(on)[].forEach.call(root.querySelectorAll("[data-pending]"),function(b){b.removeAttribute("data-pending");if(LAZY)LAZY.unobserve(b);mountNow(+b.getAttribute("data-i"))});
 if(on&&root.requestFullscreen&&!document.fullscreenElement)root.requestFullscreen().catch(function(){});
 if(!on&&document.fullscreenElement)document.exitFullscreen().catch(function(){});$("mc-focus").textContent=on?"✕ Exit full screen":"⛶ Full screen"}
document.addEventListener("fullscreenchange",function(){if(!document.fullscreenElement&&root.classList.contains("focus"))focusMode(false)});
function setTheme(t){cfg.theme=t;root.setAttribute("data-theme",t);$("mc-dark").textContent=t=="dark"?"☀️":"🌙";persist();buildGrid();newsSym=null;news()}

/* ---------------- events ---------------- */
$("mc-form").addEventListener("submit",function(e){e.preventDefault();var s=norm($("mc-q").value);if(!s)return;
 if(cfg.link){for(var i=0;i<4;i++)cfg.charts[i]={s:s,tf:cfg.charts[i].tf};persist();buildGrid()}else{setChart(cfg.sel,s);persist()}
 $("mc-q").value="";$("mc-q").blur();$("mc-sug").style.display="none";renderNotes();news();if(cfg.strat)renderStrat()});
var sugI=-1;
function showSug(){var q=$("mc-q").value,m=matches(q),box=$("mc-sug");sugI=-1;
 var nk=NICK[q.toUpperCase().replace(/\s+/g,"")];if(nk&&!m.some(function(x){return x.s==nk}))m.unshift({s:nk,n:"Nickname match"});
 var extra=Object.keys(ALIAS).filter(function(k){return q.length>=2&&k.indexOf(q.toUpperCase().replace(/\s+/g,""))==0}).slice(0,3);
 if(!m.length&&!extra.length){box.style.display="none";return}
 box.innerHTML=extra.map(function(k){return'<div class="o" data-pick="'+esc(k)+'"><b>'+esc(k)+'</b><span>'+esc(ALIAS[k])+'</span></div>'}).join("")
  +m.map(function(x){return'<div class="o" data-pick="'+esc(x.s)+'"><b>'+esc(x.s)+'</b><span>'+esc(x.n)+'</span></div>'}).join("");box.style.display="block"}
function pick(v){$("mc-q").value=v;$("mc-sug").style.display="none";$("mc-form").dispatchEvent(new Event("submit",{cancelable:true}))}
$("mc-q").addEventListener("input",showSug);$("mc-q").addEventListener("focus",showSug);
$("mc-q").addEventListener("keydown",function(e){var o=$("mc-sug").querySelectorAll(".o");if(!o.length||$("mc-sug").style.display=="none")return;
 if(e.key=="ArrowDown"||e.key=="ArrowUp"){e.preventDefault();sugI=(sugI+(e.key=="ArrowDown"?1:-1)+o.length)%o.length;[].forEach.call(o,function(x,i){x.classList.toggle("on",i==sugI)})}
 else if(e.key=="Enter"&&sugI>=0){e.preventDefault();pick(o[sugI].getAttribute("data-pick"))}
 else if(e.key=="Escape")$("mc-sug").style.display="none"});
$("mc-sug").addEventListener("mousedown",function(e){var o=e.target.closest("[data-pick]");if(o){e.preventDefault();pick(o.getAttribute("data-pick"))}});
$("mc-q").addEventListener("blur",function(){setTimeout(function(){$("mc-sug").style.display="none"},150)});
$("mc-link").checked=!!cfg.link;$("mc-link").addEventListener("change",function(){cfg.link=this.checked;persist()});
$("mc-lay").addEventListener("click",function(e){var b=e.target.closest("[data-l]");if(!b)return;cfg.lay=+b.getAttribute("data-l");if(cfg.sel>=cfg.lay)cfg.sel=0;persist();buildGrid();renderNotes()});
Object.keys(PRESETS).forEach(function(k){var o=document.createElement("option");o.value=k;o.textContent=PRESETS[k].n;$("mc-preset").appendChild(o)});
Object.keys(STRATS).forEach(function(k){var o=document.createElement("option");o.value=k;o.textContent=STRATS[k].n;$("mc-strat").appendChild(o)});
$("mc-preset").addEventListener("change",function(){var k=this.value,s=cfg.charts[cfg.sel].s;this.value="";if(!k)return;cfg.strat="";$("mc-strat").value="";renderStrat();
 if(k=="mtf")apply(isEOD(s)?[[s,"M"],[s,"W"],[s,"D"],["BSE:SENSEX","D"]]:[[s,"D"],[s,"60"],[s,"15"],[s,"5"]]);
 else if(k=="stocksector")apply([[s,"D"],["BSE:SENSEX","D"],[sectorIdx(s),"D"],[s,"W"]]);
 else apply(PRESETS[k].c);cfg.sel=0;persist()});
function sectorIdx(s){var b=PH&&PH[base(s)],sec=b&&b.sec||"";var m={"Information Technology":"BSE:IT","Healthcare":"BSE:HC","Automobile and Auto Components":"BSE:AUTO","Metals & Mining":"BSE:METAL","Fast Moving Consumer Goods":"BSE:FMCG","Realty":"BSE:REALTY","Financial Services":"BSE:FINSER","Oil Gas & Consumable Fuels":"BSE:OILGAS","Power":"BSE:POWER","Capital Goods":"BSE:CG"};return m[sec]||"BSE:BSE500"}
$("mc-strat").addEventListener("change",function(){useStrat(this.value)});
$("mc-today").addEventListener("click",function(){var p=todays4();if(!p)return;if(!p.length){toast("No picks today");return}
 cfg.strat="";$("mc-strat").value="";apply(p.map(function(x){return["BSE:"+x.s.s,"D"]}));cfg.sel=0;persist();
 var h='<h3>⭐ Today\'s 4 — '+esc(PDATA.date)+'</h3><p class="fine">Picked by price rules from the Bubble Phase Meter. For study, not buy or sell calls.</p>'
 +p.map(function(x,i){var P=PHN[x.s.p];return'<div class="pick" style="--c:'+P.c+'" data-pane="'+i+'"><b>'+esc(x.s.s)+'</b> <span class="badge" style="--c:'+P.c+'">'+P.n+'</span><div class="fine">'+esc(x.s.n)+'</div><div>'+esc(x.why)+'</div></div>'}).join("");
 $("mc-tb-strat").innerHTML=h;showTab("strat")});
$("mc-share").addEventListener("click",shareLink);
$("mc-focus").addEventListener("click",function(){focusMode()});
$("mc-dark").addEventListener("click",function(){setTheme(cfg.theme=="dark"?"light":"dark")});
$("mc-tabs").addEventListener("click",function(e){var b=e.target.closest("[data-t]");if(b)showTab(b.getAttribute("data-t"))});
root.addEventListener("change",function(e){var t=e.target;
 if(t.hasAttribute("data-tf")){var i=+t.getAttribute("data-tf");cfg.charts[i].tf=t.value;persist();mount(i)}
 else if(t.hasAttribute("data-ck")){var day=new Date().toISOString().slice(0,10),ticks=load("ck_"+cfg.strat,{});if(ticks.d!=day)ticks={d:day,v:{}};ticks.v[t.getAttribute("data-ck")]=t.checked;save("ck_"+cfg.strat,ticks)}
 else if(t.hasAttribute("data-aon")){ALR[+t.getAttribute("data-aon")].on=t.checked;save("alerts",ALR)}
 else if(t.id=="mc-imp"&&t.files[0])importNotes(t.files[0])});
root.addEventListener("click",function(e){var t=e.target,b;
 if(t.closest("select,a,input,textarea"))return;
 if((b=t.closest(".ph"))){selectPane(+b.parentNode.getAttribute("data-p"));return}
 if(t.id=="mc-nadd"){addNote();return}
 if(t.id=="mc-nall"){showAll=!showAll;renderNotes();return}
 if(t.id=="mc-exp-n"){exportNotes();return}
 if((b=t.closest("[data-del]"))){if(confirm("Delete this note?")){var id=b.getAttribute("data-del");NOTES=NOTES.filter(function(n){return n.id!=id});save("notes",NOTES);renderNotes();refreshHeaders()}return}
 if((b=t.closest("[data-go]"))){var s=b.getAttribute("data-go");setChart(cfg.sel,s);persist();showAll=false;renderNotes();return}
 if((b=t.closest("[data-st]"))){useStrat(b.getAttribute("data-st"));return}
 if(t.id=="mc-stn"){showTab("notes");$("mc-ntag").value=cfg.strat;$("mc-ntext").focus();return}
 if((b=t.closest("[data-pane]"))){selectPane(+b.getAttribute("data-pane"));return}
 if(t.id=="mc-aadd"){var v=$("mc-at").value;if(!/^\d\d:\d\d(:\d\d)?$/.test(v))return;if(v.length==5)v+=":00";ALR.push({t:v,on:true,l:$("mc-al").value.trim()});ALR.sort(function(a,b){return a.t<b.t?-1:1});save("alerts",ALR);renderAlerts();return}
 if((b=t.closest("[data-adel]"))){ALR.splice(+b.getAttribute("data-adel"),1);save("alerts",ALR);renderAlerts();return}
 if(t.id=="mc-snd"){sound=!sound;save("sound",sound);if(sound)beep();renderAlerts();return}
});
document.addEventListener("keydown",function(e){
 if(e.target.closest&&e.target.closest("input,textarea,select")||e.ctrlKey||e.metaKey||e.altKey)return;
 var k=e.key.toLowerCase();
 if(k=="/"){e.preventDefault();$("mc-q").focus()}
 else if(k=="1"||k=="2"||k=="4"){cfg.lay=+k;if(cfg.sel>=cfg.lay)cfg.sel=0;persist();buildGrid();renderNotes()}
 else if(k=="f")focusMode();
 else if(k=="d")setTheme(cfg.theme=="dark"?"light":"dark");
 else if(k=="n"){e.preventDefault();showTab("notes");$("mc-ntext").focus()}
 else if(k=="escape"&&root.classList.contains("focus"))focusMode(false);
});

/* ---------------- start ---------------- */
root.setAttribute("data-theme",cfg.theme);$("mc-dark").textContent=cfg.theme=="dark"?"☀️":"🌙";
if(cfg.sel>=cfg.lay)cfg.sel=0;
$("mc-strat").value=cfg.strat||"";
buildGrid();renderNotes();renderStrat();renderAlerts();
tick();setInterval(tick,250);
setInterval(function(){var t=ist(now());alarms(t,isTrading(t.key,t.dow))},250);  // keeps working when the tab is in the background
})();
