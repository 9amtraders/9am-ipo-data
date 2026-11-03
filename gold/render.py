#!/usr/bin/env python3
"""Builds the English and Hindi Gold Thermometer pages from gold/data/latest.json.

Writes build/gold-thermometer-en.html and build/gold-thermometer-hi.html. Everything, including
the gauge and the chart, is plain HTML and SVG, so search engines read the full page.
"""
import html
import json
import math
from urllib.parse import quote
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "build"
URL_EN = "/gold-thermometer/"
URL_HI = "/sona-sasta-ya-mahanga/"
SITE = "https://9amtraders.com"
DEMO = "https://wa.me/919315906004?text=Hi%2C%20I%20want%20to%20book%20a%20free%20demo%20class"
COLORS = {"cheap": "#1f8a52", "fair": "#c9a227", "expensive": "#e07b28", "very_expensive": "#c1272d"}
ZONES = [("cheap", 0, 25), ("fair", 25, 60), ("expensive", 60, 85), ("very_expensive", 85, 100)]
SRC = {
    "gp": '<a href="https://goldprice.dev/" target="_blank" rel="noopener">goldprice.dev</a>',
    "fx": '<a href="https://frankfurter.dev/" target="_blank" rel="noopener">Frankfurter</a>',
    "wb": '<a href="https://www.worldbank.org/en/research/commodity-markets" target="_blank" rel="noopener">World Bank Commodity Price Data (The Pink Sheet)</a>',
}

T = {
 "en": {
  "lang": "en", "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  "band": {"cheap": "Cheap", "fair": "Fair", "expensive": "Expensive", "very_expensive": "Very expensive"},
  "band_text": {
   "cheap": "Gold is close to or below its recent average, a level seen in the cheapest quarter of months since §Y§.",
   "fair": "Gold is trading near its normal level compared with the past year.",
   "expensive": "Gold has run up more than usual compared with the past year.",
   "very_expensive": "Gold is stretched far above its recent average, a level reached in only about 15% of months since §Y§."},
  "zone_rule": {"cheap": "Bottom 25% of months", "fair": "25% to 60%", "expensive": "60% to 85%", "very_expensive": "Top 15% of months"},
  "updated": "Updated {d} · {t} IST",
  "switch": '<a class="lang" href="' + URL_HI + '">हिंदी में पढ़ें →</a>',
  "h1": 'Gold Thermometer: Is Gold <span>Cheap or Expensive</span> Today?',
  "intro": "Not just today's gold price: a daily reading of whether gold is cheap or expensive compared with its own history since §Y§, based on international gold prices and the rupee exchange rate.",
  "today_is": "Today gold is",
  "main": "Gold is <b>{x}</b> {dir} its 12-month average. Compared with every month since §Y§, today's reading is higher than <b>{pct}%</b> of them.",
  "above": "above", "below": "below",
  "gauge_aria": "Gold Thermometer gauge showing {band}, reading {pct} out of 100",
  "r_price": "Gold today (24K, per 10 g)",
  "r_price_sub": "₹{g} per gram · 22K ₹{k22} · 18K ₹{k18} per 10 g. International price, before import duty and GST.",
  "r_avg": "Against 12-month average", "r_avg_sub": "Average {a}: ₹{v} per 10 g",
  "r_yoy": "Against a year ago", "r_yoy_sub": "vs the {m} average",
  "r_read": "Thermometer reading", "r_read_sub": "0 = cheapest, 100 = most stretched month since §Y§",
  "attr": "Today's gold price: {gp}. USD/INR {fx} on {fxd}.",
  "past_h": "What happened next in the past?",
  "past": "Since §Y§, gold was in the <b>{band}</b> zone in <b>{n}</b> months. A year later, gold was higher in <b>{up}%</b> of those cases, with a typical (median) change of <b>{med}</b>. Across all months, gold was higher a year later {base}% of the time.",
  "past_few": "Gold has been in the <b>{band}</b> zone in only {n} months since §Y§, too few to show a reliable pattern.",
  "past_note": "This is what happened in the past, not a forecast. Gold can fall even when history looks favourable.",
  "chart_h": "Gold in rupees: last 5 years",
  "chart_sub": "Monthly average price of 24K gold per 10 g, with its 12-month average. Today's price is the last point.",
  "legend": ["Monthly price", "12-month average", "Today"],
  "ribbon_h": "How the reading changed: last 5 years",
  "ribbon_sub": "Each block is one month, coloured by that month's Thermometer reading. Hover over or tap a block to see the month.",
  "yday": "{chg} since {d}",
  "share_b": "Share on WhatsApp",
  "share_t": "Is gold cheap or expensive today? The 9AM Gold Thermometer reads {band} ({pct}/100). See why: {url}",
  "jeweller_h": "Why is your jeweller's rate higher?",
  "jeweller": "Indian gold prices add import duty and 3% GST, and jewellery also carries making charges. So your jeweller's rate will be higher than the international price shown here. The Thermometer uses the international price so that 25 years of history compare like with like, because India's import duty has changed several times in that period.",
  "how_h": "How the Gold Thermometer works",
  "how": ["We take today's international gold price and convert it to rupees per 10 grams using the latest USD/INR rate.",
          "We compare it with gold's average price over the previous 12 months. Gold rises over the long run, so the raw price is almost always near a record. The gap from its own recent average shows whether gold has run ahead of itself.",
          "We compare today's gap with the same gap for every month since §Y§, and place it on the gauge."],
  "zones_h": ["Zone", "Today's gap compared with months since §Y§"],
  "use_h": "How to use this reading",
  "use": ["<b>Buying jewellery for a wedding or festival?</b> Buy what you need when you need it. The reading tells you whether you are paying a stretched price, which can help you decide between buying all at once or in parts.",
          "<b>Investing in gold?</b> Many long-term investors buy a little every month through gold ETFs or gold mutual funds, which smooths out expensive and cheap phases.",
          "<b>Trading gold?</b> An expensive reading is not a sell signal. Gold can stay expensive for months. Traders still need a plan, a stop-loss and the right position size."],
  "faq_h": "FAQs",
  "faq": [
   ("Is gold expensive right now?", "Today's reading is {band}: gold is {x} {dir} its 12-month average, higher than {pct}% of months since §Y§. The reading is updated every day."),
   ("Is the Gold Thermometer a prediction of gold prices?", "No. It shows where today's price stands against gold's own history. The section on what happened next shows past patterns after similar readings, not a forecast."),
   ("Why is this price lower than my jeweller's rate?", "This page shows the international gold price converted to rupees. Jewellers' rates also include import duty, 3% GST and, for jewellery, making charges."),
   ("How often is the Gold Thermometer updated?", "Every day, using the latest international gold price and USD/INR exchange rate."),
   ("Where does the data come from?", "Today's gold price comes from goldprice.dev, exchange rates from European Central Bank reference rates via Frankfurter, and monthly history from the World Bank Commodity Price Data (The Pink Sheet).")],
  "cta_h": "Want to understand what moves gold?",
  "cta": "Learn how commodity and currency markets work, read charts and trade with a plan. Live classes in New Moti Nagar, Delhi or online. Your first demo class is free.",
  "cta_b": "Book a free demo class",
  "sources": "<b>Sources:</b> today's gold price from {gp}; USD/INR from European Central Bank reference rates via {fx}; monthly gold prices from the {wb}, licensed CC BY 4.0. Rupee history is built from monthly average gold prices and monthly average exchange rates.",
  "disc": "<b>Disclaimer:</b> The Gold Thermometer is for education only. It is not investment advice or a recommendation to buy or sell gold. Prices are international indicative prices converted to rupees and will differ from Indian market and jeweller rates. Past patterns do not predict future prices.",
  "stale": "This reading was last updated on {d}. Prices have moved since then.",
 },
 "hi": {
  "lang": "hi", "months": ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
  "band": {"cheap": "सस्ता", "fair": "सामान्य", "expensive": "महंगा", "very_expensive": "बहुत महंगा"},
  "band_text": {
   "cheap": "सोना अपने हाल के औसत के आसपास या उससे नीचे है। §Y§ के बाद ऐसा स्तर सबसे सस्ते 25% महीनों में ही देखा गया।",
   "fair": "पिछले एक साल की तुलना में सोना अपने सामान्य स्तर के आसपास है।",
   "expensive": "पिछले एक साल की तुलना में सोना सामान्य से ज़्यादा चढ़ चुका है।",
   "very_expensive": "सोना अपने हाल के औसत से काफ़ी ऊपर है। §Y§ के बाद सिर्फ़ लगभग 15% महीनों में ही ऐसा स्तर दिखा।"},
  "zone_rule": {"cheap": "सबसे नीचे के 25% महीने", "fair": "25% से 60%", "expensive": "60% से 85%", "very_expensive": "सबसे ऊपर के 15% महीने"},
  "updated": "अपडेट: {d} · {t} IST",
  "switch": '<a class="lang" href="' + URL_EN + '">Read in English →</a>',
  "h1": 'सोना <span>सस्ता है या महंगा?</span> आज का गोल्ड थर्मामीटर',
  "intro": "सिर्फ़ आज का सोने का भाव नहीं, बल्कि रोज़ की एक रीडिंग जो बताती है कि §Y§ के बाद के इतिहास के मुकाबले सोना अभी सस्ता है या महंगा। यह अंतरराष्ट्रीय सोने के भाव और डॉलर-रुपया रेट पर आधारित है।",
  "today_is": "आज सोना है",
  "main": "सोना अपने 12 महीने के औसत से <b>{x}</b> {dir} है। §Y§ के बाद के हर महीने से तुलना करें तो आज की रीडिंग <b>{pct}%</b> महीनों से ऊपर है।",
  "above": "ऊपर", "below": "नीचे",
  "gauge_aria": "गोल्ड थर्मामीटर: {band}, रीडिंग 100 में से {pct}",
  "r_price": "आज सोने का भाव (24 कैरेट, 10 ग्राम)",
  "r_price_sub": "₹{g} प्रति ग्राम · 22 कैरेट ₹{k22} · 18 कैरेट ₹{k18} प्रति 10 ग्राम। अंतरराष्ट्रीय भाव, आयात शुल्क और GST से पहले।",
  "r_avg": "12 महीने के औसत से", "r_avg_sub": "औसत ({a}): ₹{v} प्रति 10 ग्राम",
  "r_yoy": "एक साल पहले से", "r_yoy_sub": "{m} के औसत से तुलना",
  "r_read": "थर्मामीटर रीडिंग", "r_read_sub": "0 = सबसे सस्ता, 100 = §Y§ के बाद का सबसे ज़्यादा खिंचा हुआ महीना",
  "attr": "आज का सोने का भाव: {gp}। डॉलर-रुपया रेट {fx}, {fxd}।",
  "past_h": "पहले ऐसा होने पर आगे क्या हुआ?",
  "past": "§Y§ के बाद <b>{n}</b> महीनों में सोना <b>{band}</b> ज़ोन में था। उनमें से <b>{up}%</b> मामलों में एक साल बाद सोना ऊपर था, और आम तौर पर (मीडियन) बदलाव <b>{med}</b> रहा। सभी महीनों को मिलाकर देखें तो एक साल बाद सोना {base}% बार ऊपर था।",
  "past_few": "§Y§ के बाद सोना सिर्फ़ {n} महीनों में <b>{band}</b> ज़ोन में रहा, जो भरोसेमंद पैटर्न दिखाने के लिए काफ़ी नहीं है।",
  "past_note": "यह पुराने आंकड़ों का पैटर्न है, भविष्यवाणी नहीं। पैटर्न अच्छा होने पर भी सोना गिर सकता है।",
  "chart_h": "रुपये में सोना: पिछले 5 साल",
  "chart_sub": "24 कैरेट सोने का 10 ग्राम का मासिक औसत भाव और उसका 12 महीने का औसत। आख़िरी बिंदु आज का भाव है।",
  "legend": ["मासिक भाव", "12 महीने का औसत", "आज"],
  "ribbon_h": "पिछले 5 साल में रीडिंग कैसे बदली",
  "ribbon_sub": "हर खाना एक महीना है, जिसका रंग उस महीने की थर्मामीटर रीडिंग बताता है। महीना देखने के लिए खाने पर माउस ले जाएं या टैप करें।",
  "yday": "{d} से {chg}",
  "share_b": "WhatsApp पर शेयर करें",
  "share_t": "आज सोना सस्ता है या महंगा? 9AM गोल्ड थर्मामीटर की रीडिंग: {band} ({pct}/100)। पूरी जानकारी: {url}",
  "jeweller_h": "आपके ज्वैलर का भाव ज़्यादा क्यों होता है?",
  "jeweller": "भारत में सोने के भाव में आयात शुल्क और 3% GST जुड़ता है, और गहनों पर मेकिंग चार्ज भी लगता है। इसलिए ज्वैलर का भाव यहां दिखाए गए अंतरराष्ट्रीय भाव से ज़्यादा होगा। थर्मामीटर अंतरराष्ट्रीय भाव इसलिए इस्तेमाल करता है ताकि 25 साल की तुलना एक जैसी रहे, क्योंकि इस दौरान भारत में आयात शुल्क कई बार बदला है।",
  "how_h": "गोल्ड थर्मामीटर कैसे काम करता है?",
  "how": ["हम आज का अंतरराष्ट्रीय सोने का भाव लेते हैं और ताज़ा डॉलर-रुपया रेट से उसे 10 ग्राम के रुपये के भाव में बदलते हैं।",
          "फिर उसकी तुलना पिछले 12 महीनों के औसत भाव से करते हैं। लंबे समय में सोना बढ़ता ही है, इसलिए सिर्फ़ भाव देखने पर वह लगभग हमेशा रिकॉर्ड के पास दिखता है। अपने हाल के औसत से दूरी बताती है कि सोना ज़रूरत से ज़्यादा तो नहीं चढ़ गया।",
          "आज की इस दूरी की तुलना §Y§ के बाद के हर महीने की दूरी से करके उसे गेज पर दिखाया जाता है।"],
  "zones_h": ["ज़ोन", "§Y§ के बाद के महीनों के मुकाबले आज की दूरी"],
  "use_h": "इस रीडिंग का इस्तेमाल कैसे करें",
  "use": ["<b>शादी या त्योहार के लिए गहने खरीद रहे हैं?</b> जितनी ज़रूरत हो, ज़रूरत के समय ही खरीदें। रीडिंग से पता चलता है कि आप खिंचा हुआ भाव तो नहीं दे रहे, जिससे एक साथ खरीदने या थोड़ा-थोड़ा करके खरीदने का फ़ैसला आसान हो सकता है।",
          "<b>सोने में निवेश कर रहे हैं?</b> कई लंबी अवधि के निवेशक गोल्ड ETF या गोल्ड म्यूचुअल फ़ंड के ज़रिए हर महीने थोड़ा-थोड़ा खरीदते हैं, जिससे महंगे और सस्ते दोनों दौर का असर बराबर हो जाता है।",
          "<b>सोने में ट्रेडिंग करते हैं?</b> महंगी रीडिंग बेचने का संकेत नहीं है। सोना महीनों तक महंगा बना रह सकता है। ट्रेडिंग के लिए प्लान, स्टॉप-लॉस और सही पोज़िशन साइज़ ज़रूरी है।"],
  "faq_h": "अक्सर पूछे जाने वाले सवाल",
  "faq": [
   ("क्या अभी सोना महंगा है?", "आज की रीडिंग '{band}' है: सोना अपने 12 महीने के औसत से {x} {dir} है, जो §Y§ के बाद के {pct}% महीनों से ज़्यादा है। यह रीडिंग रोज़ अपडेट होती है।"),
   ("क्या गोल्ड थर्मामीटर सोने के भाव की भविष्यवाणी करता है?", "नहीं। थर्मामीटर बताता है कि आज का भाव सोने के अपने इतिहास के मुकाबले कहां है। 'आगे क्या हुआ' वाला हिस्सा मिलती-जुलती पुरानी रीडिंग के बाद के आंकड़े दिखाता है, भविष्यवाणी नहीं करता।"),
   ("यह भाव मेरे ज्वैलर के भाव से कम क्यों है?", "यहां अंतरराष्ट्रीय सोने का भाव रुपये में दिखाया गया है। ज्वैलर के भाव में आयात शुल्क, 3% GST और गहनों पर मेकिंग चार्ज भी जुड़ते हैं।"),
   ("गोल्ड थर्मामीटर कितनी बार अपडेट होता है?", "हर दिन, ताज़ा अंतरराष्ट्रीय सोने के भाव और डॉलर-रुपया रेट से।"),
   ("आंकड़े कहां से आते हैं?", "आज का भाव goldprice.dev से, विनिमय दर यूरोपीय सेंट्रल बैंक की रेफ़रेंस रेट (Frankfurter के ज़रिए) से, और पुराने मासिक भाव वर्ल्ड बैंक के कमोडिटी प्राइस डेटा (The Pink Sheet) से आते हैं।")],
  "cta_h": "जानना चाहते हैं कि सोने का भाव क्यों बदलता है?",
  "cta": "कमोडिटी और करेंसी मार्केट कैसे काम करते हैं, चार्ट कैसे पढ़ें और प्लान के साथ ट्रेड कैसे करें, यह सब सीखें। न्यू मोती नगर, दिल्ली में या ऑनलाइन लाइव क्लास। पहली डेमो क्लास मुफ़्त है।",
  "cta_b": "फ़्री डेमो क्लास बुक करें",
  "sources": "<b>स्रोत:</b> आज का सोने का भाव {gp} से; डॉलर-रुपया रेट यूरोपीय सेंट्रल बैंक की रेफ़रेंस रेट से, {fx} के ज़रिए; मासिक सोने के भाव {wb} से, CC BY 4.0 लाइसेंस के तहत। रुपये का इतिहास मासिक औसत सोने के भाव और मासिक औसत विनिमय दर से बनाया गया है।",
  "disc": "<b>डिस्क्लेमर:</b> गोल्ड थर्मामीटर सिर्फ़ जानकारी और शिक्षा के लिए है। यह निवेश सलाह या सोना खरीदने-बेचने की सिफ़ारिश नहीं है। यहां दिखाए गए भाव अंतरराष्ट्रीय अनुमानित भाव हैं जिन्हें रुपये में बदला गया है, और ये भारतीय बाज़ार और ज्वैलर के भाव से अलग होंगे। पुराना पैटर्न भविष्य के भाव नहीं बताता।",
  "stale": "यह रीडिंग आख़िरी बार {d} को अपडेट हुई थी। तब से भाव बदल चुके हैं।",
 },
}

CSS = """<style>
#n9gt{--navy:#14275a;--navy2:#0c1a3f;--red:#c1272d;--ink:#0e1a36;--grey:#5d6577;--line:#e3e7ef;--bg:#f5f7fb;
font-family:inherit;color:var(--ink);line-height:1.65;max-width:1080px;margin:0 auto;padding:0 16px;box-sizing:border-box}
#n9gt *{box-sizing:border-box}#n9gt a{color:var(--navy)}
#n9gt .hero{background:linear-gradient(160deg,#14275a,#0a1534);color:#fff;border-radius:18px;padding:34px 30px;margin:22px 0}
#n9gt .top{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
#n9gt .kicker{display:inline-block;background:var(--red);color:#fff;font-size:13px;font-weight:700;letter-spacing:1px;padding:5px 12px;border-radius:5px}
#n9gt .lang{color:#fff!important;font-weight:700;font-size:14px;text-decoration:none;border:1.5px solid rgba(255,255,255,.4);padding:5px 12px;border-radius:20px}
#n9gt h1{font-size:clamp(28px,4.6vw,42px);line-height:1.15;margin:14px 0 8px;color:#fff;font-weight:800}
#n9gt h1 span{color:#f2c94c}#n9gt .hero p{color:#d5ddf0;margin:0;max-width:760px}
#n9gt .reading{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;margin-bottom:16px}
#n9gt .gauge svg{width:100%;height:auto;display:block}
#n9gt .legend{display:flex;flex-wrap:wrap;gap:6px 12px;justify-content:center;font-size:13px;color:var(--grey);margin-top:4px}
#n9gt .legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}
#n9gt .lab{font-size:15px;color:var(--grey);margin:0}
#n9gt .big{font-size:clamp(34px,5vw,48px);font-weight:800;line-height:1.1;margin:2px 0 8px}
#n9gt .reading p{margin:0 0 8px}
#n9gt .cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:6px}
#n9gt .card{background:#fff;border:1px solid var(--line);border-top:4px solid var(--navy);border-radius:12px;padding:14px}
#n9gt .card h3{font-size:14px;color:var(--grey);margin:0 0 4px;font-weight:600}
#n9gt .card .v{font-size:24px;font-weight:800;color:var(--ink);line-height:1.2}
#n9gt .card p{font-size:13px;color:var(--grey);margin:6px 0 0;line-height:1.45}
#n9gt .attr{font-size:13px;color:var(--grey);margin:4px 0 18px}
#n9gt h2{font-size:clamp(22px,3.2vw,28px);margin:34px 0 8px;color:var(--navy);font-weight:800}
#n9gt h3{color:var(--navy)}
#n9gt .box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px}
#n9gt .note{font-size:14px;color:var(--grey);margin:8px 0 0}
#n9gt .chart svg{width:100%;height:auto;display:block}
#n9gt .sub{color:var(--grey);margin:0 0 12px}
#n9gt table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:15px}
#n9gt th,#n9gt td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left}
#n9gt th{background:var(--navy);color:#fff;font-size:14px}
#n9gt .dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:8px;vertical-align:middle}
#n9gt details{background:#fff;border:1px solid var(--line);border-radius:10px;padding:13px 17px;margin-bottom:10px}
#n9gt summary{font-weight:700;cursor:pointer;color:var(--navy)}#n9gt details p{margin:10px 0 0;color:var(--grey)}
#n9gt .cta{background:linear-gradient(160deg,#14275a,#0a1534);color:#fff;border-radius:18px;padding:28px;margin:34px 0 16px;text-align:center}
#n9gt .cta h2{color:#fff;margin:0 0 8px}#n9gt .cta p{color:#d5ddf0;margin:0 0 18px}
#n9gt .btn{display:inline-block;background:var(--red);color:#fff!important;text-decoration:none;font-weight:700;padding:14px 26px;border-radius:10px;box-shadow:0 5px 0 #7d1418}
#n9gt .disc{font-size:13px;color:var(--grey);border-top:1px solid var(--line);padding-top:12px;margin:14px 0}
#n9gt .stale{display:none;background:#fff5f5;border:1px solid #f3c7c9;border-left:5px solid var(--red);border-radius:10px;padding:12px 16px;margin:0 0 14px;font-size:15px}
#n9gt .needle{transform-origin:160px 160px;transform:rotate(var(--a))}
#n9gt .chg{font-size:13px;font-weight:700;margin:4px 0 0!important}#n9gt .chg.up{color:#1f8a52!important}#n9gt .chg.dn{color:#c1272d!important}
#n9gt .share{display:inline-flex;align-items:center;gap:8px;margin-top:6px;background:#25d366;color:#fff!important;text-decoration:none;font-weight:700;font-size:15px;padding:10px 16px;border-radius:9px}
#n9gt .share svg{width:20px;height:20px}
#n9gt .reading.pre .needle{transform:rotate(0deg)}
#n9gt .reading.pre .seg{stroke-dasharray:1;stroke-dashoffset:1}
#n9gt .reading.pre .bigname{opacity:0}
#n9gt .reading.go .seg{stroke-dasharray:1;animation:n9draw .55s ease-out var(--d) both}
#n9gt .reading.go .seg.on{animation:n9draw .55s ease-out var(--d) both,n9glow 1.2s ease-in-out 3.2s 3}
#n9gt .reading.go .needle{animation:n9sweep 2.6s ease-in-out .5s both}
#n9gt .reading.go .bigname{animation:n9up .5s ease-out 2.9s both}
@keyframes n9draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes n9sweep{0%{transform:rotate(0deg)}38%{transform:rotate(180deg)}74%{transform:rotate(calc(var(--a) + 6deg))}88%{transform:rotate(calc(var(--a) - 2deg))}100%{transform:rotate(var(--a))}}
@keyframes n9glow{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes n9up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){#n9gt .reading .seg,#n9gt .reading .needle,#n9gt .reading .bigname{animation:none!important}}
@media (max-width:760px){#n9gt .reading{grid-template-columns:1fr}#n9gt .cards{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:420px){#n9gt .cards{grid-template-columns:1fr}#n9gt .hero{padding:26px 20px}}
</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def inr(n):
    """Indian digit grouping: 114170 -> 1,14,170."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + parts + [tail])


def pct(x, sign=True):
    return f"{x * 100:+.1f}%" if sign else f"{abs(x) * 100:.1f}%"


def month_name(t, m):
    y, mo = m.split("-")
    return f"{t['months'][int(mo) - 1]} {y}"


def day_name(t, d):
    y, mo, dd = d.split("-")
    return f"{int(dd)} {t['months'][int(mo) - 1]} {y}"


def gauge(L, t):
    """Semicircle gauge. The needle is drawn at 0 and rotated to the reading, so CSS can animate the swing.
    Without CSS or JavaScript the SVG transform still shows the final position."""
    cx, cy, r, w = 160, 160, 118, 26

    def pt(p, rad):
        a = math.pi * (1 - p / 100)
        return cx + rad * math.cos(a), cy - rad * math.sin(a)

    segs = ""
    for k, (name, a, b) in enumerate(ZONES):
        x1, y1 = pt(a, r)
        x2, y2 = pt(b, r)
        on = " on" if name == L["band"] else ""
        segs += (f'<path class="seg{on}" style="--d:{k * 0.12:.2f}s" pathLength="1" d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {x2:.1f},{y2:.1f}" '
                 f'fill="none" stroke="{COLORS[name]}" stroke-width="{w}"/>')
    for p_ in (25, 60, 85):
        xa, ya = pt(p_, r - w / 2 - 1)
        xb, yb = pt(p_, r + w / 2 + 1)
        segs += f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="#fff" stroke-width="3"/>'
    ticks = ""
    for p_ in range(0, 101, 10):
        xa, ya = pt(p_, r - w / 2 - 6)
        xb, yb = pt(p_, r - w / 2 - (12 if p_ % 50 == 0 else 9))
        ticks += f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="#b8c0d2" stroke-width="1.5"/>'
    deg = L["percentile"] * 1.8
    label = t["gauge_aria"].format(band=t["band"][L["band"]], pct=round(L["percentile"]))
    return (f'<svg viewBox="0 0 320 185" role="img" aria-label="{esc(label)}">{segs}{ticks}'
            f'<g class="needle" style="--a:{deg:.1f}deg" transform="rotate({deg:.1f} {cx} {cy})">'
            f'<path d="M{cx},{cy - 5} L{cx - (r - 34)},{cy} L{cx},{cy + 5} Z" fill="#0e1a36"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="12" fill="#0e1a36"/><circle cx="{cx}" cy="{cy}" r="4.5" fill="{COLORS[L["band"]]}"/>'
            f'<text x="28" y="180" font-size="13" fill="#5d6577">0</text><text x="282" y="180" font-size="13" fill="#5d6577">100</text></svg>')


def ribbon(L, t):
    """One coloured block per month for the last five years, coloured by that month's reading."""
    rb = L.get("ribbon") or []
    if not rb:
        return ""
    W, H, l, rgt, top, bh = 680, 70, 8, 8, 6, 34
    bw = (W - l - rgt) / len(rb)
    cells, years = "", ""
    for i, c in enumerate(rb):
        x = l + i * bw
        tip = f"{month_name(t, c['m'])}: {t['band'][c['band']]} ({round(c['pct'])}/100)"
        cells += (f'<rect x="{x:.1f}" y="{top}" width="{bw + 0.4:.1f}" height="{bh}" fill="{COLORS[c["band"]]}">'
                  f'<title>{esc(tip)}</title></rect>')
        if c["m"].endswith("-01"):
            years += (f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + bh + 6}" stroke="#fff" stroke-width="2"/>'
                      f'<text x="{x + 3:.1f}" y="{top + bh + 22}" font-size="12" fill="#5d6577">{c["m"][:4]}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(t["ribbon_h"])}">{cells}{years}</svg>'


def chart(L, t):
    pts = L["chart"]
    W, H, l, rgt, top, bot = 680, 300, 70, 16, 14, 34
    vals = [p["p"] for p in pts] + [p["a"] for p in pts] + [L["inr_10g_24k"]]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or 1000
    lo, hi = lo - pad, hi + pad
    n = len(pts)

    def X(i):
        return l + (W - l - rgt) * i / n

    def Y(v):
        return top + (H - top - bot) * (1 - (v - lo) / (hi - lo))

    grid = ""
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        y = Y(v)
        lab = f"₹{v / 100000:.2f}L" if hi >= 100000 else f"₹{v / 1000:.0f}k"
        grid += f'<line x1="{l}" x2="{W - rgt}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e7ef"/><text x="{l - 8}" y="{y + 4:.1f}" font-size="12" fill="#5d6577" text-anchor="end">{lab}</text>'
    for i, p in enumerate(pts):
        if p["m"].endswith("-01"):
            x = X(i)
            grid += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{H - bot}" stroke="#eef1f6"/><text x="{x:.1f}" y="{H - 12}" font-size="12" fill="#5d6577" text-anchor="middle">{p["m"][:4]}</text>'
    line = " ".join(f"{X(i):.1f},{Y(p['p']):.1f}" for i, p in enumerate(pts)) + f" {X(n):.1f},{Y(L['inr_10g_24k']):.1f}"
    avg = " ".join(f"{X(i):.1f},{Y(p['a']):.1f}" for i, p in enumerate(pts))
    tx, ty = X(n), Y(L["inr_10g_24k"])
    lg = t["legend"]
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(t["chart_h"])}">{grid}'
            f'<polyline points="{avg}" fill="none" stroke="#c1272d" stroke-width="2" stroke-dasharray="6 5"/>'
            f'<polyline points="{line}" fill="none" stroke="#14275a" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="6" fill="#c9a227" stroke="#fff" stroke-width="2"/></svg>'
            f'<div class="legend"><span><i style="background:#14275a"></i>{lg[0]}</span>'
            f'<span><i style="background:#c1272d"></i>{lg[1]}</span><span><i style="background:#c9a227"></i>{lg[2]}</span></div>')


def page(L, lang):
    t = T[lang]
    band = L["band"]
    bname = t["band"][band]
    s = L["stretch"]
    x, d = pct(s, sign=False), t["above"] if s >= 0 else t["below"]
    p_ = round(L["percentile"])
    upd_d, upd_t = L["updated_ist"].split(" ")
    pt_ = L["pattern"]
    if pt_["n"] >= 12:
        past = t["past"].format(band=bname, n=pt_["n"], up=round(pt_["up_share"] * 100),
                                med=pct(pt_["median"]), base=round(pt_["base_up_share"] * 100))
    else:
        past = t["past_few"].format(band=bname, n=pt_["n"])
    yoy = pct(L["yoy"]) if L.get("yoy") is not None else "–"
    yday = ""
    if L.get("prev"):
        diff = L["inr_10g_24k"] - L["prev"]["inr_10g"]
        chg = f'{"+" if diff >= 0 else "−"}₹{inr(abs(diff))} ({pct(diff / L["prev"]["inr_10g"])})'
        yday = f'<p class="chg {"up" if diff >= 0 else "dn"}">{t["yday"].format(chg=chg, d=day_name(t, L["prev"]["date"]))}</p>'
    share = "https://wa.me/?text=" + quote(t["share_t"].format(band=bname, pct=p_, url=SITE + (URL_EN if lang == "en" else URL_HI)))
    zones = "".join(f'<tr><td><span class="dot" style="background:{COLORS[z]}"></span><b>{t["band"][z]}</b></td><td>{t["zone_rule"][z]}</td></tr>' for z, _, _ in ZONES)
    faqs = [(q, a.format(band=bname, x=x, dir=d, pct=p_)) for q, a in t["faq"]]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
    ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
                     "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
                    ensure_ascii=False)
    legend = "".join(f'<span><i style="background:{COLORS[z]}"></i>{t["band"][z]}</span>' for z, _, _ in ZONES)
    return f"""<!-- 9AM Traders Academy | Gold Thermometer ({lang}). Built by gold/render.py in github.com/9amtraders/9am-ipo-data.
     Updated automatically every day. Edit the script, not this page. -->
<div id="n9gt" lang="{lang}" data-updated="{L['date']}">
{CSS}
<section class="hero">
  <div class="top"><span class="kicker">{t['updated'].format(d=day_name(t, upd_d), t=upd_t)}</span>{t['switch']}</div>
  <h1>{t['h1']}</h1>
  <p>{t['intro']}</p>
</section>
<div class="stale" id="n9gt-stale">{t['stale'].format(d=day_name(t, L['date']))}</div>

<div class="reading">
  <div class="gauge">{gauge(L, t)}<div class="legend">{legend}</div></div>
  <div>
    <p class="lab">{t['today_is']}</p>
    <div class="big bigname" style="color:{COLORS[band]}">{bname}</div>
    <p>{t['main'].format(x=x, dir=d, pct=p_)}</p>
    <p class="note">{t['band_text'][band]}</p>
    <a class="share" href="{share}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-3.9-4.7-4.1-.1-.2-1.1-1.5-1.1-2.8s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.3 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.5.1.3.6 1 1.3 1.7.9.8 1.7 1.1 2 1.2.2.1.4.1.5-.1l.7-.9c.2-.2.4-.2.6-.1l1.9.9c.3.1.4.2.5.3.1.2.1.7-.1 1.3z"/></svg>{t['share_b']}</a>
  </div>
</div>

<div class="cards">
  <div class="card"><h3>{t['r_price']}</h3><div class="v">₹{inr(L['inr_10g_24k'])}</div>{yday}<p>{t['r_price_sub'].format(g=inr(L['inr_g_24k']), k22=inr(L['inr_10g_22k']), k18=inr(L['inr_10g_18k']))}</p></div>
  <div class="card"><h3>{t['r_avg']}</h3><div class="v">{pct(s)}</div><p>{t['r_avg_sub'].format(a=month_name(t, L['avg12_from']) + ' – ' + month_name(t, L['avg12_to']), v=inr(L['avg12']))}</p></div>
  <div class="card"><h3>{t['r_yoy']}</h3><div class="v">{yoy}</div><p>{t['r_yoy_sub'].format(m=month_name(t, L['yoy_month']))}</p></div>
  <div class="card"><h3>{t['r_read']}</h3><div class="v"><span class="count" data-to="{p_}">{p_}</span> / 100</div><p>{t['r_read_sub']}</p></div>
</div>
<p class="attr">{t['attr'].format(gp=SRC['gp'], fx=L['usdinr'], fxd=day_name(t, L['fx_date']) if L.get('fx_date') else '')}</p>

<h2>{t['past_h']}</h2>
<div class="box"><p style="margin:0">{past}</p><p class="note">{t['past_note']}</p></div>

<h2>{t['chart_h']}</h2>
<p class="sub">{t['chart_sub']}</p>
<div class="box chart">{chart(L, t)}</div>

<h2>{t['ribbon_h']}</h2>
<p class="sub">{t['ribbon_sub']}</p>
<div class="box chart">{ribbon(L, t)}<div class="legend">{legend}</div></div>

<h2>{t['jeweller_h']}</h2>
<p>{t['jeweller']}</p>

<h2>{t['how_h']}</h2>
<ol>{''.join(f'<li>{x_}</li>' for x_ in t['how'])}</ol>
<table><thead><tr><th>{t['zones_h'][0]}</th><th>{t['zones_h'][1]}</th></tr></thead><tbody>{zones}</tbody></table>

<h2>{t['use_h']}</h2>
<ul>{''.join(f'<li>{x_}</li>' for x_ in t['use'])}</ul>

<h2>{t['faq_h']}</h2>
{faq_html}

<section class="cta">
  <h2>{t['cta_h']}</h2>
  <p>{t['cta']}</p>
  <a class="btn" href="{DEMO}" target="_blank" rel="noopener">{t['cta_b']}</a>
</section>

<p class="disc">{t['sources'].format(**SRC)}</p>
<p class="disc">{t['disc']}</p>
<script type="application/ld+json">
{ld}
</script>
<script>
(function(){{var box=document.querySelector("#n9gt .reading");if(!box)return;
if(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches)return;
var nums=document.querySelectorAll("#n9gt .count");box.classList.add("pre");nums.forEach(function(n){{n.textContent="0";}});
function go(){{box.classList.remove("pre");box.classList.add("go");
var nd=box.querySelector(".needle"),t0=null;requestAnimationFrame(function step(ts){{if(!t0)t0=ts;
var m=getComputedStyle(nd).transform,a=0;if(m&&m!=="none"){{var v=m.match(/-?[0-9.e]+/g);a=Math.atan2(+v[1],+v[0])*180/Math.PI;if(a<-90)a+=360;}}
var r=Math.max(0,Math.min(100,Math.round(a/1.8)));nums.forEach(function(n){{n.textContent=ts-t0>3300?n.getAttribute("data-to"):r;}});
if(ts-t0<=3300)requestAnimationFrame(step);}});}}
if("IntersectionObserver" in window){{var io=new IntersectionObserver(function(e){{if(e[0].isIntersecting){{io.disconnect();go();}}}},{{threshold:.35}});io.observe(box);}}else go();}})();
(function(){{var r=document.getElementById("n9gt"),s=document.getElementById("n9gt-stale");if(!r||!s)return;
var d=new Date(r.getAttribute("data-updated")+"T00:00:00+05:30");if((Date.now()-d)/864e5>3)s.style.display="block";}})();
</script>
</div>
""".replace("§Y§", L["hist_from"][:4])


def main():
    L = json.loads((ROOT / "data" / "latest.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for lang in ("en", "hi"):
        (OUT / f"gold-thermometer-{lang}.html").write_text(page(L, lang), encoding="utf-8")
    print(f"OK: Gold Thermometer pages built for {L['date']} ({L['band']}, reading {round(L['percentile'])}).")


if __name__ == "__main__":
    main()
