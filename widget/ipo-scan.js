/* 9AM IPO Scan widget script. Loaded by the HTML widget on 9amtraders.com/ipo-analyzer-india/.
   Kept as an external file so WordPress, Elementor and speed plugins can't strip or alter it. */
(function () {
function boot() {
  if (!document.getElementById('ipo-scan') || window.__ipoScanBooted) return;
  window.__ipoScanBooted = true;
  /* =================== SETTINGS =================== */
  var DATA = 'https://raw.githubusercontent.com/9amtraders/9am-ipo-data/main'; // updated every morning by the IPO Scan task
  var REQUEST_EMAIL = 'info@9amtraders.com';
  var LAST_UPDATED = '2026-10-29';     // date of the fallback list below
  var MAX_PICKS = 10;                  // quick-pick buttons under the search bar

  // Fallback list, shown instantly and used only if the live list can't load.
  var IPOS = [
    { name: 'SFC Environmental Technologies', aka: ['SFC Environmental', 'SFC'], board: 'Mainboard', open: '2026-10-27', close: '2026-10-29', listing: '2026-11-03', band: '₹313 – ₹330', hasReport: true, score: 59 },
    { name: 'BLS Polymers', aka: ['BLS Polymer'], board: 'Mainboard', open: '2026-10-27', close: '2026-10-29', listing: '2026-11-03', band: '₹142 – ₹150', hasReport: true, score: 70 },
    { name: 'Wiscon Industries', aka: [], board: 'SME', open: '2026-10-27', close: '2026-10-29', listing: '2026-11-03', band: '₹194 – ₹204', hasReport: true, score: 66 },
    { name: 'M.K.Sons Fine Jewels', aka: ['MK Sons', 'MK Sons Jewellers', 'MK Sons Fine Jewels'], board: 'Mainboard', open: '2026-10-28', close: '2026-10-30', listing: '2026-11-04', band: '₹153 – ₹162', hasReport: true, score: 78 },
    { name: 'Carver Roboweld', aka: [], board: 'SME', open: '2026-10-28', close: '2026-10-30', listing: '2026-11-04', band: '₹76 – ₹80', hasReport: true, score: 66 },
    { name: 'Ajwa Projects', aka: [], board: 'SME', open: '2026-10-28', close: '2026-10-30', listing: '2026-11-04', band: '₹203', hasReport: true, score: 69 },
    { name: 'Bombay Coated & Special Steels', aka: ['Bombay Coated Steels', 'BCSS', 'Bombay Coated'], board: 'Mainboard', open: '2026-10-29', close: '2026-11-02', listing: '2026-11-05', band: '₹78 – ₹82', hasReport: true, score: 65 },
    { name: 'Antala Industries', aka: [], board: 'SME', open: '2026-10-29', close: '2026-11-02', listing: '2026-11-05', band: '₹63 – ₹67', hasReport: true, score: 73 },
    { name: 'Maxwell Engineering Solutions', aka: ['Maxwell Engineering'], board: 'SME', open: '2026-10-30', close: '2026-11-03', listing: '2026-11-06', band: '₹150 – ₹158', hasReport: true, score: 74 },
    { name: 'Vectras Enprocon', aka: [], board: 'SME', open: '2026-10-30', close: '2026-11-03', listing: '2026-11-06', band: '₹99 – ₹105' },
    { name: 'HGS (India)', aka: ['HGS India'], board: 'SME', open: '2026-10-30', close: '2026-11-03', listing: '2026-11-06', band: '₹114 – ₹120' },
    { name: 'Johnsoncab Electricals', aka: ['Johnsoncab'], board: 'SME', open: '2026-10-30', close: '2026-11-03', listing: '2026-11-06', band: '₹190 – ₹200' },
    { name: 'Acko', aka: ['Acko General Insurance'], board: 'Mainboard' },
    { name: 'OYO', aka: ['Oravel Stays', 'PRISM', 'OYO Rooms'], board: 'Mainboard' },
    { name: 'Parle Products', aka: ['Parle', 'Parle G'], board: 'Mainboard' },
    { name: 'MakeMyTrip', aka: ['Make My Trip', 'MMT'], board: 'Mainboard' },
    { name: 'boAt', aka: ['Imagine Marketing', 'Boat Lifestyle'], board: 'Mainboard' },
    { name: 'Zepto', aka: ['Kiranakart'], board: 'Mainboard' },
    { name: 'PhonePe', aka: ['Phone Pe'], board: 'Mainboard' },
    { name: 'Cult.fit', aka: ['Cultfit', 'Curefit', 'Cure.fit'], board: 'Mainboard' },
    { name: 'Kuku FM', aka: ['Mebigo Labs', 'Kuku TV'], board: 'Mainboard' },
    { name: 'Tata Sons', aka: ['Tata'], board: 'Mainboard' },
    { name: 'Upstox', aka: ['RKSV'], board: 'Mainboard' },
    { name: 'Inox Clean Energy', aka: ['Inox Clean', 'Inox Solar'], board: 'Mainboard' }
  ];

  // Optional calendars. A tab only appears when its list has rows.
  var SPLITS = [];    // { company, ratio, record: 'YYYY-MM-DD', exchange }
  var DIVIDENDS = []; // { company, amount, exDate: 'YYYY-MM-DD', type }
  var BONUSES = [];   // { company, ratio, record: 'YYYY-MM-DD', exchange }
  var RESULTS = [];   // { company, quarter, date: 'YYYY-MM-DD', sector }

  function ck(name, category, status, finding) { return { name: name, category: category, status: status, finding: finding, source: '' }; }
  var SAMPLE_REPORT = {
    name: 'Sample Co. A Ltd', board: 'Mainboard', sector: '[Sector]', exchange: 'NSE, BSE', band: '₹[low] – ₹[high]',
    issueSizeCr: null, freshCr: null, ofsCr: null, lotSize: null,
    summary: 'This sample shows the full report layout. Pick a real IPO from the list or search above to see its report.',
    score: 72, counts: { pass: 21, caution: 6, flag: 4, na: 2 }, totalChecks: 33, confidence: 'normal',
    categories: [
      { name: 'Financial health', score: 75, detail: '4 of 6 checks passed · 1 flag' }, { name: 'Profitability', score: 80, detail: '3 of 5 checks passed' },
      { name: 'Valuation vs peers', score: 50, detail: '1 of 4 checks passed · 1 flag' }, { name: 'Promoter & governance', score: 88, detail: '3 of 4 checks passed' },
      { name: 'Issue structure', score: 50, detail: '1 of 3 checks passed · 1 flag' }, { name: 'Use of proceeds', score: 63, detail: '2 of 4 checks passed · 1 flag' },
      { name: 'Legal & litigation', score: 83, detail: '2 of 3 checks passed' }, { name: 'Risk factors', score: 75, detail: '2 of 4 checks passed · 2 not found' }
    ],
    checks: [
      ck('Revenue growth over 3 years', 'Financial health', 'pass', 'Revenue grew about 24% a year over 3 years.'),
      ck('Positive operating cash flow', 'Financial health', 'flag', 'Cash from operations was negative in the latest year.'),
      ck('Offer for sale share of the issue', 'Issue structure', 'flag', 'About 68% of the issue is offer for sale.'),
      ck('Promoter holding after the issue', 'Promoter & governance', 'pass', 'Promoters keep about 58% after listing.'),
      ck('No pledged promoter shares', 'Promoter & governance', 'pass', 'No pledge reported.'),
      ck('P/E vs listed peers', 'Valuation vs peers', 'flag', 'Post-issue P/E of 46× vs peer median of 34.5×.'),
      ck('Related-party transactions', 'Promoter & governance', 'caution', 'Related-party sales are close to 10% of revenue.'),
      ck('Auditor remarks', 'Risk factors', 'pass', 'Clean audit opinion.'),
      ck('No repayment to promoter entities', 'Use of proceeds', 'flag', 'Part of the issue repays a promoter group loan.'),
      ck('Customer concentration', 'Risk factors', 'na', 'Not found in public sources.')
    ],
    peers: ['Listed Peer 1', 'Listed Peer 2', 'Listed Peer 3', 'Listed Peer 4'],
    metrics: [
      ['Revenue growth, 3-yr CAGR', '%', 'high', 24.0, [18.0, 21.0, 12.0, 15.0]],
      ['Net profit margin', '%', 'high', 9.2, [11.5, 8.1, 7.4, 10.2]],
      ['Return on equity', '%', 'high', 17.8, [19.4, 14.2, 12.9, 16.5]],
      ['Return on capital employed', '%', 'high', 15.1, [21.0, 16.3, 13.8, 18.2]],
      ['Debt to equity', 'x', 'low', 0.62, [0.35, 0.48, 0.81, 0.40]],
      ['P/E (post-issue, upper band)', 'x', 'low', 46, [38, 31, 27, 42]],
      ['Price to book', 'x', 'low', 7.9, [6.8, 4.2, 3.1, 6.0]]
    ],
    sources: [], generatedAt: null
  };
  /* =================== END SETTINGS =================== */

  var root = document.getElementById('ipo-scan');
  var $ = function (s) { return root.querySelector(s); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var ist = function (d, t) { return new Date(d + 'T' + (t || '00:00:00') + '+05:30'); };
  var fmtDate = function (d) { return d ? ist(String(d).slice(0, 10)).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }) : 'TBA'; };
  var shortDate = function (d) { return ist(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata' }); };
  var slug = function (s) { return String(s).toLowerCase().replace(/&/g, ' ').replace(/\b(ltd|limited|ipo|pvt|private|the|and)\b/g, ' ').replace(/[^a-z0-9]+/g, ''); };
  var stamp = function () { return '?v=' + Math.floor(Date.now() / 300000); }; // matches GitHub's 5-minute cache
  var now = new Date();

  function statusOf(ipo) {
    if (ipo.sample) return 'sample';
    if (!ipo.open) return 'tba';
    if (now < ist(ipo.open)) return 'upcoming';
    if (!ipo.close || now <= ist(ipo.close, '23:59:59')) return 'open';
    if (ipo.listing && now >= ist(ipo.listing, '10:00:00')) return 'listed';
    return 'closed';
  }
  var STATUS = { open: 'Open now', upcoming: 'Opening soon', closed: 'Closed · awaiting listing', listed: 'Listed', tba: 'Dates not announced', sample: 'Sample report' };
  var RANK = { open: 0, upcoming: 1, closed: 2, listed: 3, tba: 4, sample: 5 };

  var SAMPLE = { id: 'sample', name: 'Sample Co. A Ltd', aka: [], board: 'Mainboard', band: '₹[low] – ₹[high]', sample: true, hasReport: true };
  var ALL, byId, REPORTS = { sample: SAMPLE_REPORT };
  function setList(list) {
    IPOS = list.map(function (i) { return Object.assign({ aka: [] }, i, { id: slug(i.name) }); });
    ALL = IPOS.concat([SAMPLE]);
    byId = {}; ALL.forEach(function (i) { byId[i.id] = i; });
  }
  function addIpo(i) { i.id = slug(i.name); if (!byId[i.id]) { ALL.push(i); byId[i.id] = i; } return byId[i.id]; }
  setList(IPOS);

  async function getJSON(url, ms) {
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, ms) : null;
    try {
      var res = await fetch(url, { credentials: 'omit', cache: 'no-store', signal: ctl ? ctl.signal : undefined });
      var data = null; try { data = await res.json(); } catch (e) {}
      return { status: res.status, data: data };
    } finally { if (timer) clearTimeout(timer); }
  }

  /* ---------- Spelling-tolerant search ---------- */
  var STOP = { ltd: 1, limited: 1, ipo: 1, pvt: 1, private: 1, the: 1, and: 1, co: 1, company: 1 };
  function sound(w) { return w.replace(/ph/g, 'f').replace(/ck/g, 'k').replace(/q/g, 'k').replace(/z/g, 's').replace(/w/g, 'v').replace(/y/g, 'i').replace(/ee/g, 'i').replace(/oo/g, 'u').replace(/(.)\1+/g, '$1'); }
  function tokens(s) { return String(s).toLowerCase().replace(/&/g, ' ').replace(/[^a-z0-9]+/g, ' ').trim().split(' ').filter(function (t) { return t && !STOP[t]; }); }
  function lev(a, b) {
    if (a === b) return 0; if (!a.length) return b.length; if (!b.length) return a.length;
    var prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) { cur = [i]; for (j = 1; j <= b.length; j++) cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); prev = cur; }
    return prev[b.length];
  }
  function nameScore(q, name) {
    var raw = String(q).toLowerCase().replace(/[^a-z0-9]+/g, ''), rawName = String(name).toLowerCase().replace(/[^a-z0-9]+/g, '');
    if (raw && rawName.indexOf(raw) === 0) return 0;          // first letters typed: "b", "bl", "m.k" ...
    if (raw.length < 3) return tokens(name).some(function (w) { return w.indexOf(raw) === 0; }) ? 0.02 : 1; // 1–2 letters: a word must start with them
    var qt = tokens(q).map(sound), nt = tokens(name).map(sound);
    if (!qt.length || !nt.length) return 1;
    var qc = qt.join(''), nc = nt.join('');
    if (nc.indexOf(qc) === 0) return 0;
    if (nc.indexOf(qc) > 0) return 0.05;
    var bests = qt.map(function (t) {
      var best = 1;
      nt.forEach(function (n) { var pre = n.slice(0, Math.max(t.length, 3)); best = Math.min(best, n.indexOf(t) === 0 ? 0 : lev(t, pre) / Math.max(t.length, pre.length), lev(t, n) / Math.max(t.length, n.length)); });
      return best;
    });
    var avg = bests.reduce(function (a, b) { return a + b; }, 0) / bests.length;
    var whole = lev(qc, nc.slice(0, qc.length + 1)) / Math.max(qc.length, 3);
    return Math.min(0.7 * Math.min.apply(null, bests) + 0.3 * avg, whole);
  }
  function search(q) {
    return ALL.map(function (ipo) {
      var short = String(q).replace(/[^a-z0-9]+/gi, '').length < 3;
      var s = [ipo.name].concat(short ? [] : (ipo.aka || [])).reduce(function (m, n) { return Math.min(m, nameScore(q, n)); }, 1);
      if (ipo.sample) s += 0.15;
      return { ipo: ipo, s: s };
    }).sort(function (a, b) {
      return (a.s - b.s) || ((b.ipo.hasReport ? 1 : 0) - (a.ipo.hasReport ? 1 : 0)) || (RANK[statusOf(a.ipo)] - RANK[statusOf(b.ipo)]) || a.ipo.name.localeCompare(b.ipo.name);
    });
  }
  function highlight(name, q) {
    var raw = String(q).trim().toLowerCase();
    var i = raw ? name.toLowerCase().indexOf(raw) : -1, len = raw.length;
    if (i < 0) { var t = tokens(q)[0]; if (!t) return esc(name); i = name.toLowerCase().indexOf(t); len = t.length; }
    return i < 0 ? esc(name) : esc(name.slice(0, i)) + '<mark>' + esc(name.slice(i, i + len)) + '</mark>' + esc(name.slice(i + len));
  }

  var input = $('#is-q'), list = $('#is-sugg'), active = -1, shown = [];
  function picks() {
    var withReport = IPOS.filter(function (i) { return i.hasReport && statusOf(i) !== 'listed'; });
    var rest = IPOS.filter(function (i) { return !i.hasReport && (statusOf(i) === 'open' || statusOf(i) === 'upcoming'); });
    var byRank = function (a, b) { return (RANK[statusOf(a)] - RANK[statusOf(b)]) || ((b.score || 0) - (a.score || 0)); };
    return withReport.sort(byRank).concat(rest.sort(byRank)).slice(0, MAX_PICKS);
  }
  function defaultSugg() { return picks().slice(0, 8).map(function (i) { return { ipo: i }; }); }
  function renderSugg() {
    var q = input.value.trim();
    shown = q ? search(q).filter(function (r) { return r.s <= 0.45; }).slice(0, 8) : defaultSugg();
    var html = (q ? '' : '<li class="hint" role="presentation">Tap one to see its report</li>') + shown.map(function (r, k) {
      var st = statusOf(r.ipo);
      return '<li role="option" id="is-opt-' + k + '" data-id="' + r.ipo.id + '" aria-selected="' + (k === active) + '"><span>' + highlight(r.ipo.name, q) + '</span><span class="meta">' +
        (r.ipo.score != null ? '<span class="sc">' + r.ipo.score + '</span>' : '') + '<span class="tag t-' + st + '">' + STATUS[st] + '</span></span></li>';
    }).join('');
    if (q && !shown.length) html = '<li class="hint" role="presentation">No IPO starts with "' + esc(q) + '". Press Get report to see the closest names.</li>';
    list.innerHTML = html;
    list.hidden = !html; input.setAttribute('aria-expanded', html ? 'true' : 'false');
    if (active >= 0) input.setAttribute('aria-activedescendant', 'is-opt-' + active); else input.removeAttribute('aria-activedescendant');
  }
  function closeSugg() { list.hidden = true; active = -1; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); }
  var userChose = false;
  function choose(id) { var ipo = byId[id]; if (!ipo) return; userChose = true; input.value = ipo.sample ? '' : ipo.name; closeSugg(); input.blur(); $('#is-dym').innerHTML = ''; openReport(id, true); }

  input.addEventListener('input', function () { active = -1; renderSugg(); });
  input.addEventListener('focus', function () { renderSugg(); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (list.hidden) renderSugg();
      if (!shown.length) return;
      active = (active + (e.key === 'ArrowDown' ? 1 : shown.length - 1)) % shown.length; renderSugg(); e.preventDefault();
    } else if (e.key === 'Escape') closeSugg();
    else if (e.key === 'Enter' && active >= 0 && shown[active]) { e.preventDefault(); choose(shown[active].ipo.id); }
  });
  list.addEventListener('mousedown', function (e) { var li = e.target.closest('li[data-id]'); if (li) { e.preventDefault(); choose(li.dataset.id); } });
  list.addEventListener('touchend', function (e) { var li = e.target.closest('li[data-id]'); if (li) { e.preventDefault(); choose(li.dataset.id); } });
  document.addEventListener('click', function (e) { if (!e.target.closest('#ipo-scan .combo')) closeSugg(); });

  function didYouMean(q, lead) {
    var near = search(q).filter(function (r) { return !r.ipo.sample; }).slice(0, 3);
    $('#is-dym').innerHTML = '<p class="dym">' + lead + ' Did you mean ' + near.map(function (r) { return '<button type="button" data-pick="' + r.ipo.id + '">' + esc(r.ipo.name) + '</button>'; }).join(', ') +
      '? Still missing? <a href="mailto:' + REQUEST_EMAIL + '?subject=' + encodeURIComponent('IPO report request: ' + q) + '" style="color:#FFC2B8">Ask us to add it</a>.</p>';
  }

  $('#is-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var q = input.value.trim(); if (!q) { input.focus(); return; }
    if (active >= 0 && shown[active]) { choose(shown[active].ipo.id); return; }
    var res = search(q);
    if (res[0].s <= 0.25) { choose(res[0].ipo.id); return; }
    closeSugg();
    didYouMean(q, 'No IPO matches "' + esc(q) + '".');
  });

  /* ---------- Quick picks under the search bar ---------- */
  function renderPicks() {
    var items = picks();
    $('#is-picks').innerHTML = items.map(function (i) {
      var st = statusOf(i);
      var sub = i.score != null ? '<b aria-label="score ' + i.score + '">' + i.score + '</b>' : '<em>' + (st === 'upcoming' ? 'Opens ' + shortDate(i.open) : 'Report soon') + '</em>';
      return '<button type="button" class="pick" data-pick="' + i.id + '" aria-pressed="' + (currentId === i.id) + '">' + esc(i.name) + sub + '</button>';
    }).join('');
  }

  /* ---------- Upcoming column (desktop) ---------- */
  var currentId = 'sample';
  function renderSide() {
    renderPicks();
    var groups = [['open', 'Open now'], ['upcoming', 'Opening soon'], ['closed', 'Closed · awaiting listing'], ['tba', 'Expected']];
    $('#is-side').innerHTML = groups.map(function (g) {
      var items = IPOS.filter(function (i) { return statusOf(i) === g[0]; });
      if (!items.length) return '';
      return '<h3>' + g[1] + '</h3><ul>' + items.map(function (i) {
        var sub = g[0] === 'open' && i.close ? 'Closes ' + shortDate(i.close) : g[0] === 'upcoming' ? 'Opens ' + shortDate(i.open) : g[0] === 'closed' && i.listing ? 'Lists ' + shortDate(i.listing) : '';
        if (i.score != null) sub = (sub ? sub + ' · ' : '') + 'Score ' + i.score;
        if (i.sub && i.sub.retail != null) sub += ' · Retail ' + i.sub.retail.toFixed(1) + '×';
        return '<li><button type="button" data-pick="' + i.id + '" aria-current="' + (currentId === i.id) + '">' + esc(i.name) + (sub ? '<small>' + sub + '</small>' : '') + '</button></li>';
      }).join('') + '</ul>';
    }).join('') + '<h3>Example</h3><ul><li><button type="button" data-pick="sample" aria-current="' + (currentId === 'sample') + '">Sample full report</button></li></ul>';
    $('#is-upd').textContent = 'List updated ' + fmtDate(LAST_UPDATED);
  }

  var listReady = null;
  function loadList() {
    listReady = getJSON(DATA + '/ipos.json' + stamp(), 20000).then(function (r) {
      if (r.status === 200 && r.data && r.data.ipos && r.data.ipos.length) {
        var extra = ALL.filter(function (x) { return x.adhoc; });
        setList(r.data.ipos); extra.forEach(addIpo);
        if (r.data.updated) LAST_UPDATED = r.data.updated;
        if (!byId[currentId]) currentId = 'sample';
        renderSide(); if (!list.hidden) renderSugg();
      }
    }).catch(function () {});
    return listReady;
  }

  /* ---------- Report ---------- */
  var checkFilter = 'all', peersOn = [];
  function band(s) { return s <= 25 ? ['Weak', '#A61B1B'] : s <= 50 ? ['Okay', '#8A5300'] : s <= 75 ? ['Good', '#2F5DA8'] : ['Strong', '#14254A']; }
  function fmtVal(v, u) { return v == null ? '—' : u === '%' ? v.toFixed(1) + '%' : (v < 10 ? v.toFixed(2) : v.toFixed(1)) + '×'; }
  function median(xs) { var s = xs.slice().sort(function (a, b) { return a - b; }), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; }
  function cr(v) { return '₹' + Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 }) + ' cr'; }
  function host(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return 'source'; } }
  var infoIcon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none;margin-top:2px"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>';
  var flagIcon = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#C62828" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none;margin-top:2px"><path d="M12 9v4"></path><path d="M12 17h.01"></path><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"></path></svg>';
  var studyNote = '<div class="note" role="note">' + infoIcon + '<p><strong>A good score does not mean you should apply.</strong> It only shows how many issues we found in public information about the issue. Always study the RHP, the business and the price yourself before deciding.</p></div>';


  function pct(c) { return c >= 99.95 ? '100%' : c >= 10 ? Math.round(c) + '%' : c.toFixed(1) + '%'; }
  function times(v) { return v == null ? '—' : v.toFixed(2) + '×'; }
  function subHtml(ipo) {
    if (!ipo || ipo.sample) return '';
    var st = statusOf(ipo), sub = ipo.sub, a = ipo.allot;
    var head = '<div class="subx"><h3 style="margin:0 0 4px">Subscription and your allotment chance</h3>';
    if (!sub) {
      if (st === 'upcoming') return head + '<p class="sub" style="margin:0">Subscription figures appear here once bidding opens on ' + fmtDate(ipo.open) + '.</p></div>';
      if (st === 'open') return head + '<p class="sub" style="margin:0">Subscription figures for this IPO are added in the next morning update.</p></div>';
      return '';
    }
    var sme = ipo.board === 'SME', rl = sme ? 'Individual investors' : 'Retail';
    var live = !sub.final && st === 'open';
    var big = '—', line = '', note = '';
    if (a) {
      var lower = a.basis === 'estimate' && a.chance < 100;
      big = (lower ? 'At least ' : '') + pct(a.chance);
      if (a.basis === 'undersubscribed') line = 'The ' + rl.toLowerCase() + ' portion is ' + (live ? 'not fully subscribed so far' : 'not fully subscribed') + ', so every valid application ' + (live ? 'would get' : 'gets') + ' the shares it applied for.';
      else if (a.chance >= 100) line = 'There are enough shares for every ' + rl.toLowerCase() + ' applicant to get at least the minimum application.';
      else line = (lower ? 'At least ' : 'About ') + (a.chance >= 15 ? Math.round(a.chance / 10) + ' in 10 ' : '1 in ' + a.oneIn.toLocaleString('en-IN') + ' ') + rl.toLowerCase() + ' applicants ' + (live || st === 'upcoming' ? 'would get' : 'get') + ' shares' + (live ? ' at the current subscription' : '') + '.';
      if (lower) note = 'The exact chance depends on how many applications were made, which isn\'t published yet, so this is the lowest it can be.';
    }
    var cats = [['QIB', sub.qib], ['NII (HNI)', sub.nii], [rl, sub.retail], ['Total', sub.total]].filter(function (c) { return c[1] != null; });
    var when = (sub.asOf ? 'As of ' + esc(sub.asOf) : '') + (sub.final ? ' · final figures' : live ? ' · bidding is still open, so these will change' : '');
    return head + '<div class="subx-grid"><div class="chance"><span class="chance-lbl">' + (st === 'listed' ? 'Chance a ' + rl.toLowerCase() + ' applicant got shares' : 'Chance a ' + rl.toLowerCase() + ' applicant gets shares') + '</span>' +
      '<strong>' + big + '</strong><p>' + line + '</p>' + (note ? '<p class="mute">' + note + '</p>' : '') + '</div>' +
      '<div class="times">' + cats.map(function (c) { return '<div' + (c[0] === rl ? ' class="hl"' : '') + '><span>' + c[0] + '</span><b>' + times(c[1]) + '</b></div>'; }).join('') + '</div></div>' +
      '<p class="updated">' + when + (sub.source ? ' · <a href="' + esc(sub.source) + '" target="_blank" rel="nofollow noopener">' + esc(host(sub.source)) + '</a>' : '') + '</p>' +
      '<p class="updated">How it works: when the ' + rl.toLowerCase() + ' portion is oversubscribed, SEBI rules give the minimum application to as many applicants as possible, picked by lottery. Applying for more than the minimum doesn\'t raise your chance.</p></div>';
  }
  function headerHtml(ipo, R) {
    R = R || {};
    var x = Object.assign({}, ipo, { band: R.band || ipo.band, open: R.open || ipo.open, close: R.close || ipo.close, listing: R.listing || ipo.listing, board: R.board || ipo.board });
    var s = statusOf(x);
    var tbd = ipo.sample ? '[dates]' : 'To be announced';
    var facts = [['Price band', x.band || (ipo.sample ? '[band]' : 'To be announced')], ['Opens · Closes', x.open ? fmtDate(x.open) + ' · ' + fmtDate(x.close) : tbd],
      ['Listing date', x.listing ? fmtDate(x.listing) : tbd], ['Exchange', R.exchange || (x.board === 'SME' ? 'NSE Emerge / BSE SME' : 'NSE, BSE')]];
    if (R.issueSizeCr != null) facts.push(['Issue size', cr(R.issueSizeCr)]);
    if (R.freshCr != null) facts.push(['Fresh issue vs OFS', R.ofsCr ? cr(R.freshCr) + ' fresh · ' + cr(R.ofsCr) + ' OFS' : 'All fresh issue, no OFS']);
    if (R.lotSize) facts.push(['Lot size', R.lotSize + ' shares']);
    if (R.sector) facts.push(['Sector', R.sector]);
    var by = R.generatedAt ? '<p class="byline">Built by AI from public sources on ' + fmtDate(R.generatedAt) + '. Figures may contain errors, so verify them in the RHP.</p>' : '';
    return '<div class="pills" style="gap:8px"><span class="tag t-upcoming">' + esc(x.board) + '</span><span class="tag ' + (ipo.sample ? 't-sample' : 't-' + s) + '">' + STATUS[s] + '</span></div>' +
      '<h2 id="is-rep-h" style="margin-top:12px;font-size:clamp(22px,4vw,34px)">' + esc(R.name && !ipo.sample ? R.name : ipo.name) + ' IPO Report</h2>' + by +
      '<dl class="facts">' + facts.map(function (f) { return '<div><dt>' + f[0] + '</dt><dd>' + esc(f[1]) + '</dd></div>'; }).join('') + '</dl>' + subHtml(byId[ipo.id] || ipo);
  }

  function peerHtml(R) {
    if (!R.peers || !R.peers.length) return '<div class="card"><h3>Key numbers vs listed peers</h3><div class="empty">Listed peer figures were not found in public sources for this IPO.</div></div>';
    var idx = []; peersOn.forEach(function (on, i) { if (on) idx.push(i); });
    var chips = R.peers.map(function (p, i) { return '<button type="button" class="pill" data-peer="' + i + '" aria-pressed="' + !!peersOn[i] + '">' + esc(p) + '</button>'; }).join('');
    var head = '<tr><th scope="col">Metric</th><th scope="col" class="num ipo-col" style="color:#C62828">This IPO</th>' + idx.map(function (i) { return '<th scope="col" class="num">' + esc(R.peers[i]) + '</th>'; }).join('') + '<th scope="col" class="num">Peer median</th><th scope="col">IPO vs peers</th></tr>';
    var body = R.metrics.map(function (m) {
      var vals = idx.map(function (i) { return m[4][i]; }), known = vals.filter(function (v) { return v != null; });
      var verdict = '<span class="tag t-tba">' + (idx.length ? 'No data' : 'Pick a peer') + '</span>', med = '—';
      if (known.length) {
        var md = median(known); med = fmtVal(md, m[1]);
        if (m[3] != null && md !== 0) {
          var diff = (m[3] - md) / Math.abs(md);
          if (Math.abs(diff) <= 0.05) verdict = '<span class="tag t-tba">In line</span>';
          else { var good = m[2] === 'high' ? diff > 0 : diff < 0; verdict = '<span class="tag ' + (good ? 't-good' : 't-bad') + '">' + (good ? 'Better by ' : 'Weaker by ') + Math.round(Math.abs(diff) * 100) + '%</span>'; }
        }
      }
      return '<tr><th scope="row">' + esc(m[0]) + '<div style="font-size:12px;font-weight:500;color:#5B6474">' + (m[2] === 'high' ? 'Higher is better' : 'Lower is better') + '</div></th><td class="num ipo-col">' + fmtVal(m[3], m[1]) + '</td>' +
        vals.map(function (v) { return '<td class="num">' + fmtVal(v, m[1]) + '</td>'; }).join('') + '<td class="num"><strong>' + med + '</strong></td><td>' + verdict + '</td></tr>';
    }).join('');
    return '<div class="card"><h3>Key numbers vs listed peers</h3><p class="sub">Tap a peer to include or drop it from the median.</p>' +
      '<div class="pills" role="group" aria-label="Peers to compare">' + chips + '</div><div class="tbl"><table style="min-width:760px"><thead>' + head + '</thead><tbody>' + body + '</tbody></table></div>' +
      '<p class="updated">Valuation uses the upper price band, after the issue. Within 5% of the median counts as in line.</p></div>';
  }

  function checksHtml(R) {
    var CH = { pass: ['Passed', 't-good'], caution: ['Caution', 't-warn'], flag: ['Red flag', 't-bad'], na: ['Not found', 't-tba'] };
    var rows = R.checks.filter(function (c) { return checkFilter === 'all' || c.status === checkFilter; });
    var pills = [['all', 'All'], ['flag', 'Red flags'], ['caution', 'Caution'], ['pass', 'Passed'], ['na', 'Not found']].map(function (f) { return '<button type="button" class="pill" data-check="' + f[0] + '" aria-pressed="' + (checkFilter === f[0]) + '">' + f[1] + '</button>'; }).join('');
    return '<div class="card"><div class="row"><h3 style="margin:0">Every check, with its source</h3><div class="pills" role="group" aria-label="Filter checks">' + pills + '</div></div>' +
      '<div class="tbl"><table style="min-width:640px"><thead><tr><th scope="col">Check</th><th scope="col">Category</th><th scope="col">What we found</th><th scope="col">Result</th><th scope="col">Source</th></tr></thead><tbody>' +
      (rows.length ? rows.map(function (c) {
        var src = c.source ? '<a href="' + esc(c.source) + '" target="_blank" rel="nofollow noopener">' + esc(host(c.source)) + '</a>' : '—';
        return '<tr><td><strong>' + esc(c.name) + '</strong></td><td style="color:#5B6474">' + esc(c.category) + '</td><td>' + esc(c.finding) + '</td><td><span class="tag ' + CH[c.status][1] + '">' + CH[c.status][0] + '</span></td><td style="white-space:nowrap">' + src + '</td></tr>';
      }).join('') : '<tr><td colspan="5">No checks in this group.</td></tr>') +
      '</tbody></table></div><p class="updated">Showing ' + rows.length + ' of ' + R.checks.length + ' checks.</p></div>';
  }

  function sourcesHtml(R) {
    if (!R.sources || !R.sources.length) return '';
    return '<div class="card"><h3>Sources</h3><ul style="margin:0;padding-left:20px">' + R.sources.slice(0, 12).map(function (s) {
      return '<li style="margin:6px 0"><a href="' + esc(s.url) + '" target="_blank" rel="nofollow noopener">' + esc(s.title || host(s.url)) + '</a> <span style="color:#5B6474;font-size:14px">' + esc(host(s.url)) + '</span></li>';
    }).join('') + '</ul></div>';
  }

  function renderFull(ipo, R) {
    var banners = '';
    if (ipo.sample) banners += '<div class="banner"><span><strong>Sample report.</strong> Search above or pick an IPO to get its real report.</span></div>';
    if (R.stale) banners += '<div class="banner"><span>Showing the last saved report from ' + fmtDate(R.generatedAt) + '. A fresh one couldn\'t be built right now.</span></div>';
    if (R.confidence === 'low') banners += '<div class="banner"><span><strong>Limited public data.</strong> ' + R.counts.na + ' of ' + R.totalChecks + ' checks couldn\'t be verified, so treat this score as provisional.</span></div>';
    var hasScore = R.score != null, b = hasScore ? band(R.score) : ['Not enough data', '#5B6474'];
    var dash = hasScore ? (R.score / 100 * 364.4).toFixed(1) : '0';
    var cats = R.categories.map(function (c) {
      var v = c.score, col = v == null ? '#C9CFDA' : v >= 76 ? '#14254A' : v >= 51 ? '#2F5DA8' : v >= 26 ? '#E08A00' : '#C62828';
      return '<div class="cat"><div class="cat-top"><span>' + esc(c.name) + '</span><b>' + (v == null ? '—' : v) + '</b></div><div class="bar" aria-hidden="true"><i style="width:' + (v || 0) + '%;background:' + col + '"></i></div><p>' + esc(c.detail) + '</p></div>';
    }).join('');
    var flagged = R.checks.filter(function (c) { return c.status === 'flag'; });
    var flags = flagged.length ? flagged.map(function (c) {
      return '<div class="flag">' + flagIcon + '<div><strong>' + esc(c.name) + '</strong><p>' + esc(c.finding) + '</p>' + (c.source ? '<a href="' + esc(c.source) + '" target="_blank" rel="nofollow noopener" style="font-size:14px">' + esc(host(c.source)) + '</a>' : '') + '</div></div>';
    }).join('') : '<div class="empty">No red flags found in public sources. Checks marked "not found" could still hide problems, so read the RHP.</div>';
    var c = R.counts;
    $('#is-report').innerHTML = banners + '<div class="card" aria-labelledby="is-rep-h">' + headerHtml(ipo, R) +
      (R.summary ? '<p style="margin:18px 0 0;font-size:16px;color:#3B4352">' + esc(R.summary) + '</p>' : '') +
      '<div class="score"><svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label="' + (hasScore ? 'IPO Scan score ' + R.score + ' out of 100, ' + b[0] : 'Not enough data for a score') + '">' +
      '<circle cx="70" cy="70" r="58" fill="none" stroke="#E3E6EB" stroke-width="14"></circle><circle cx="70" cy="70" r="58" fill="none" stroke="' + b[1] + '" stroke-width="14" stroke-linecap="round" stroke-dasharray="' + dash + ' 364.4" transform="rotate(-90 70 70)"></circle>' +
      '<text x="70" y="78" text-anchor="middle" font-size="38" font-weight="800" fill="#14254A">' + (hasScore ? R.score : '—') + '</text><text x="70" y="100" text-anchor="middle" font-size="13" fill="#5B6474">out of 100</text></svg>' +
      '<div><div class="score-label">IPO Scan score</div><div class="band-name" style="color:' + b[1] + '">' + b[0] + '</div><div class="counts">' +
      '<span><i class="dot" style="background:#14254A"></i><strong>' + c.pass + '</strong> passed</span><span><i class="dot" style="background:#E08A00"></i><strong>' + c.caution + '</strong> caution</span><span><i class="dot" style="background:#C62828"></i><strong>' + c.flag + '</strong> red flags</span>' +
      (c.na ? '<span><i class="dot" style="background:#C9CFDA"></i><strong>' + c.na + '</strong> not found</span>' : '') + '</div></div></div>' +
      (hasScore ? '<div class="scale"><span class="marker" style="left:' + R.score + '%" aria-hidden="true">' + R.score + '</span><div class="scale-grid">' +
      '<div><div class="scale-bar" style="background:#F3C6C3;border-radius:6px 0 0 6px"></div><strong style="color:#A61B1B">Weak</strong><span>0 – 25</span></div>' +
      '<div><div class="scale-bar" style="background:#F8DDB0"></div><strong style="color:#8A5300">Okay</strong><span>26 – 50</span></div>' +
      '<div><div class="scale-bar" style="background:#2F5DA8"></div><strong style="color:#2F5DA8">Good</strong><span>51 – 75</span></div>' +
      '<div><div class="scale-bar" style="background:#C9D2E6;border-radius:0 6px 6px 0"></div><strong style="color:#14254A">Strong</strong><span>76 – 100</span></div></div></div>' : '') +
      studyNote + '</div>' +
      '<div class="card"><h3>Scores by category</h3><div class="cats">' + cats + '</div></div>' +
      '<div class="card"><h3 style="color:#C62828">Red flags</h3>' + flags + '</div>' +
      peerHtml(R) + checksHtml(R) + sourcesHtml(R);
  }

  function renderLoading(ipo) {
    $('#is-report').innerHTML = '<div class="card" aria-labelledby="is-rep-h" aria-busy="true">' + headerHtml(ipo) +
      '<div class="loading"><span class="spin" aria-hidden="true"></span><div><strong>Loading the report…</strong></div></div></div>';
  }
  function renderNotCovered(ipo) {
    var mail = 'mailto:' + REQUEST_EMAIL + '?subject=' + encodeURIComponent('IPO report request: ' + ipo.name);
    var when = statusOf(ipo) === 'tba' ? 'Its dates are not announced yet. We add the report once the issue opens for bidding soon.' : 'We add new reports every morning, starting with open and upcoming mainboard IPOs.';
    $('#is-report').innerHTML = '<div class="card" aria-labelledby="is-rep-h">' + headerHtml(ipo) +
      '<div class="empty" style="margin-top:20px"><strong>The IPO Scan report for ' + esc(ipo.name) + ' isn\'t ready yet.</strong> ' + when +
      ' Meanwhile, here are five checks you can do yourself in the RHP:' +
      '<ol><li>How much of the issue is offer for sale (OFS), and how much is fresh money for the company?</li><li>What will the fresh money be used for? Watch for repayment of promoter-linked loans.</li><li>What is the promoter holding after the issue, and are any shares pledged?</li><li>What is the P/E at the upper price band compared with listed peers?</li><li>How large are pending legal cases compared with net worth?</li></ol>' +
      '<p style="margin:14px 0 0;display:flex;flex-wrap:wrap;gap:10px"><a class="btn btn-line" href="' + mail + '">Ask us to cover it</a><button type="button" class="btn btn-line" data-pick="sample">See a sample report</button></p></div>' + studyNote + '</div>';
  }
  function renderError(ipo, msg) {
    $('#is-report').innerHTML = '<div class="card" aria-labelledby="is-rep-h">' + headerHtml(ipo) +
      '<div class="empty" style="margin-top:20px"><strong>' + esc(msg) + '</strong>' +
      '<p style="margin:14px 0 0;display:flex;flex-wrap:wrap;gap:10px"><button type="button" class="btn btn-line" data-retry="' + ipo.id + '">Try again</button><button type="button" class="btn btn-line" data-pick="sample">See a sample report</button></p></div>' + studyNote + '</div>';
  }

  function renderCurrent() {
    var ipo = byId[currentId], R = REPORTS[currentId];
    if (R) renderFull(ipo, R);
  }

  async function fetchReport(ipo) {
    if (REPORTS[ipo.id]) { renderCurrent(); return; }
    renderLoading(ipo);
    var r = null;
    try { r = await getJSON(DATA + '/reports/' + ipo.id + '.json' + stamp(), 20000); } catch (e) {}
    if (currentId !== ipo.id) return;
    if (r && r.status === 200 && r.data && r.data.checks) {
      REPORTS[ipo.id] = r.data;
      peersOn = (r.data.peers || []).map(function () { return true; });
      renderCurrent(); return;
    }
    if (listReady) await listReady;
    if (currentId !== ipo.id) return;
    ipo = byId[ipo.id] || ipo;
    if (r && r.status === 404 || !ipo.hasReport) { renderNotCovered(ipo); return; }
    renderError(ipo, 'The report could not be loaded. Please check your connection and try again.');
  }

  function openReport(id, scroll) {
    var ipo = byId[id]; if (!ipo) return;
    currentId = id; checkFilter = 'all';
    peersOn = REPORTS[id] ? (REPORTS[id].peers || []).map(function () { return true; }) : [];
    renderSide();
    if (REPORTS[id]) renderCurrent(); else fetchReport(ipo);
    try { var u = new URL(window.location.href); if (ipo.sample) u.searchParams.delete('ipo'); else u.searchParams.set('ipo', ipo.name); history.replaceState(null, '', u.toString()); } catch (e) {}
    if (scroll) { var el = $('#is-report'); setTimeout(function () { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.focus({ preventScroll: true }); }, 30); }
  }

  /* ---------- Calendar (only tabs that have data) ---------- */
  var CAL = [
    ['split', 'Stock splits', ['Company', 'Split ratio', 'Record date', 'Exchange'], SPLITS.map(function (r) { return [r.company, r.ratio, fmtDate(r.record), r.exchange]; })],
    ['div', 'Dividends', ['Company', 'Dividend per share', 'Ex-date', 'Type'], DIVIDENDS.map(function (r) { return [r.company, r.amount, fmtDate(r.exDate), r.type]; })],
    ['bonus', 'Bonus issues', ['Company', 'Bonus ratio', 'Record date', 'Exchange'], BONUSES.map(function (r) { return [r.company, r.ratio, fmtDate(r.record), r.exchange]; })],
    ['res', 'Quarterly results', ['Company', 'Quarter', 'Board meeting', 'Sector'], RESULTS.map(function (r) { return [r.company, r.quarter, fmtDate(r.date), r.sector]; })]
  ].filter(function (c) { return c[3].length; });
  var tab = CAL.length ? CAL[0][0] : null;
  function renderCal() {
    if (!CAL.length) return;
    $('#is-cal').hidden = false;
    $('#is-tabs').innerHTML = CAL.map(function (t) { return '<button type="button" role="tab" id="is-tab-' + t[0] + '" aria-controls="is-panel" aria-selected="' + (tab === t[0]) + '" tabindex="' + (tab === t[0] ? 0 : -1) + '" data-tab="' + t[0] + '">' + t[1] + '</button>'; }).join('');
    $('#is-panel').setAttribute('aria-labelledby', 'is-tab-' + tab);
    var c = CAL.filter(function (t) { return t[0] === tab; })[0];
    $('#is-panel').innerHTML = '<table style="min-width:520px"><thead><tr>' + c[2].map(function (h) { return '<th scope="col">' + h + '</th>'; }).join('') + '</tr></thead><tbody>' +
      c[3].map(function (r) { return '<tr>' + r.map(function (v, j) { return j ? '<td>' + esc(v) + '</td>' : '<td><strong>' + esc(v) + '</strong></td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>';
  }

  /* ---------- Events ---------- */
  root.addEventListener('click', function (e) {
    var t = e.target.closest('button'); if (!t || !root.contains(t)) return;
    if (t.dataset.pick) { choose(t.dataset.pick); return; }
    if (t.dataset.retry) { var ipo = byId[t.dataset.retry]; if (ipo) fetchReport(ipo); return; }
    if (t.dataset.check) { checkFilter = t.dataset.check; renderCurrent(); return; }
    if (t.dataset.peer) { var i = +t.dataset.peer; peersOn[i] = !peersOn[i]; renderCurrent(); return; }
    if (t.dataset.tab) { tab = t.dataset.tab; renderCal(); $('#is-tab-' + tab).focus(); }
  });
  $('#is-tabs').addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    var ids = CAL.map(function (t) { return t[0]; }), k = ids.indexOf(tab);
    tab = ids[(k + (e.key === 'ArrowRight' ? 1 : ids.length - 1)) % ids.length]; renderCal(); $('#is-tab-' + tab).focus(); e.preventDefault();
  });

  // Start: an IPO from the link (?ipo=...), otherwise the top open IPO that has a report.
  var start = null;
  try { var p = new URL(window.location.href).searchParams.get('ipo'); if (p) { var hit = search(p)[0]; start = hit && hit.s <= 0.25 ? hit.ipo.id : addIpo({ name: p.slice(0, 80), aka: [], board: 'Mainboard', adhoc: true }).id; } } catch (e) {}
  function firstPick() { var f = picks().filter(function (i) { return i.hasReport; })[0]; return f ? f.id : 'sample'; }
  loadList();
  if (start) openReport(start, false);
  else {
    openReport(firstPick(), false);
    listReady.then(function () { if (userChose) return; if (!REPORTS[currentId] || currentId === 'sample') { var f = firstPick(); if (f !== currentId) openReport(f, false); } });
  }
  renderCal();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
