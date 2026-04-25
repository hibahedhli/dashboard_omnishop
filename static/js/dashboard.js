/* ───  Dashboard — JavaScript ─── */
 
// ─── State ──────────────────────────────────────────────────────
let summaryData = null;
let ordersPage = 1;
const PER_PAGE = 10;
let chartMonthly = null, chartCat = null, chartTop = null, chartBrutNet = null, chartCatBar = null, chartSim = null;
 
const PALETTE = ['#6366f1','#8b5cf6','#a78bfa','#f43f5e','#fb923c','#facc15','#34d399','#38bdf8','#e879f9','#f472b6'];
 
// ─── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadSummary();
  setupNav();
  setupOrderSearch();
  setupSimulator();
  setupUpload();
});
 
// ─── Navigation ──────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      const sec = item.dataset.section;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      item.classList.add('active');
      document.getElementById(`section-${sec}`)?.classList.add('active');
      document.getElementById('pageTitle').textContent = item.querySelector('span').textContent;
      if (sec === 'orders') loadOrders();
      if (sec === 'products') renderProducts();
      if (sec === 'analytics') renderAnalytics();
      if (sec === 'simulator') { simulate(); }
      if (window.innerWidth < 768) document.getElementById('sidebar').classList.remove('open');
    });
  });
  document.getElementById('menuToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}
 
// ─── Load Summary ────────────────────────────────────────────────
async function loadSummary() {
  try {
    const res = await fetch('/api/summary');
    summaryData = await res.json();
    renderOverview();
  } catch(e) { showToast('Erreur chargement données', 'error'); }
}
 
// ─── Overview ───────────────────────────────────────────────────
function renderOverview() {
  if (!summaryData) return;
  const s = summaryData;
  animateValue('kpiCANet', 0, s.ca_total, 'DT');
  animateValue('kpiOrders', 0, s.total_orders, '');
  animateValue('kpiAvg', 0, s.avg_order, 'DT');
  animateValue('kpiTVA', 0, s.tva_total, 'DT');
 
  document.getElementById('bestName').textContent = `${s.best_product_name} (ID Produit : #${s.best_product_id})`;
  document.getElementById('bestValue').textContent = fmt(s.best_product_ca);
 
  renderChartMonthly();
  renderChartCategories();
}
 
function animateValue(id, from, to, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  const isFloat = to % 1 !== 0;
  const duration = 800;
  const start = performance.now();
  function update(ts) {
    const progress = Math.min((ts - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const val = from + (to - from) * ease;
    el.textContent = isFloat || suffix === 'DT' ? fmt(val) : Math.floor(val).toLocaleString('fr-FR');
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
 
function fmt(v) {
  return new Intl.NumberFormat('fr-TN', { style:'currency', currency:'TND', maximumFractionDigits:3 }).format(v);
}
 
// ─── Charts ──────────────────────────────────────────────────────
const chartDefaults = {
  color: '#94a3b8',
  font: { family: "'DM Sans', sans-serif", size: 11 },
};
 
function renderChartMonthly() {
  const ctx = document.getElementById('chartMonthly');
  if (!ctx || !summaryData) return;
  const monthly = summaryData.monthly_ca;
  if (chartMonthly) chartMonthly.destroy();
  chartMonthly = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Object.keys(monthly),
      datasets: [{
        label: 'CA Net (DT)',
        data: Object.values(monthly),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.15)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'white',
        pointBorderColor: '#6366f1',
        pointRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipStyle() },
      scales: {
        x: axisStyle(), y: { ...axisStyle(), ticks: { ...axisStyle().ticks, callback: v => (v/1000).toFixed(0)+'kDT' } }
      }
    }
  });
}
 
function renderChartCategories() {
  const ctx = document.getElementById('chartCategories');
  if (!ctx || !summaryData) return;
  const cats = summaryData.by_category;
  if (chartCat) chartCat.destroy();
  chartCat = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(cats),
      datasets: [{ data: Object.values(cats), backgroundColor: PALETTE, borderWidth: 0, hoverOffset: 8 }]
    },
    options: {
      responsive: true, cutout: '65%',
      plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 }, padding: 10 } }, tooltip: tooltipStyle() }
    }
  });
}
 
// ─── Products ────────────────────────────────────────────────────
function renderProducts() {
  if (!summaryData) return;
  const top5 = summaryData.top5_products;
  const maxVal = top5[0]?.[1] || 1;
 
  // Top products bar chart
  const ctx = document.getElementById('chartTopProducts');
  if (ctx) {
    if (chartTop) chartTop.destroy();
    chartTop = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: top5.map(t => t[0].length > 18 ? t[0].substring(0,18)+'…' : t[0]),
        datasets: [{
          data: top5.map(t => t[1]),
          backgroundColor: PALETTE.slice(0,5),
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        indexAxis: 'y', responsive: true,
        plugins: { legend: { display: false }, tooltip: tooltipStyle() },
        scales: { x: axisStyle(), y: axisStyle() }
      }
    });
  }
 
  // Brut vs Net
  const ctx2 = document.getElementById('chartBrutNet');
  if (ctx2 && summaryData) {
    if (chartBrutNet) chartBrutNet.destroy();
    chartBrutNet = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['CA Brut', 'CA Net', 'TVA'],
        datasets: [{
          data: [summaryData.ca_brut_total, summaryData.ca_total, summaryData.tva_total],
          backgroundColor: ['#6366f1','#8b5cf6','#f59e0b'],
          borderRadius: 8, borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: tooltipStyle() },
        scales: { x: axisStyle(), y: { ...axisStyle(), ticks: { ...axisStyle().ticks, callback: v => (v/1000).toFixed(0)+'kDT' } } }
      }
    });
  }
 
  // Products grid
  const grid = document.getElementById('productsGrid');
  if (grid) {
    const allProds = Object.entries(summaryData.by_product)
      .sort((a,b) => b[1]-a[1]).slice(0,12);
    grid.innerHTML = allProds.map(([name, ca], i) => `
      <div class="product-card">
        <div class="product-rank">#${i+1}</div>
        <div class="product-name">${name}</div>
        <div class="product-ca">${fmt(ca)}</div>
        <div class="product-bar"><div class="product-bar-fill" style="width:${(ca/maxVal*100).toFixed(1)}%"></div></div>
      </div>
    `).join('');
  }
}
 
// ─── Analytics ───────────────────────────────────────────────────
function renderAnalytics() {
  if (!summaryData) return;
  const s = summaryData;
  const margin = s.ca_brut_total > 0 ? ((s.ca_total/s.ca_brut_total)*100).toFixed(1) : 0;
  const metrics = [
    { label: 'CA Brut Total', value: fmt(s.ca_brut_total), desc: 'Avant remises' },
    { label: 'CA Net Total', value: fmt(s.ca_total), desc: 'Après remises' },
    { label: 'TVA Collectée', value: fmt(s.tva_total), desc: '20% sur CA Net' },
    { label: 'CA TTC Total', value: fmt(s.ca_total + s.tva_total), desc: 'CA Net + TVA' },
    { label: 'Taux Net/Brut', value: margin + '%', desc: 'Efficacité remises' },
    { label: 'Panier Moyen', value: fmt(s.avg_order), desc: 'Par commande' },
    { label: 'Meilleures ventes', value: `#${s.best_product_id}`, desc: s.best_product_name },
    { label: 'Nb Transactions', value: s.total_orders, desc: 'Total commandes' },
  ];
 
  document.getElementById('analyticsGrid').innerHTML = metrics.map(m => `
    <div class="analytics-card">
      <div class="analytics-label">${m.label}</div>
      <div class="analytics-value">${m.value}</div>
      <div class="analytics-desc">${m.desc}</div>
    </div>
  `).join('');
 
  // Category bar chart
  const ctx = document.getElementById('chartCatBar');
  if (ctx) {
    if (chartCatBar) chartCatBar.destroy();
    const cats = summaryData.by_category;
    chartCatBar = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(cats),
        datasets: [{ data: Object.values(cats), backgroundColor: PALETTE, borderRadius: 8, borderSkipped: false }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: tooltipStyle() },
        scales: {
          x: axisStyle(),
          y: { ...axisStyle(), ticks: { ...axisStyle().ticks, callback: v => (v/1000).toFixed(0)+'kDT' } }
        }
      }
    });
  }
}
 
// ─── Orders ──────────────────────────────────────────────────────
async function loadOrders() {
  const search = document.getElementById('orderSearch')?.value || '';
  const category = document.getElementById('orderFilter')?.value || '';
  const res = await fetch(`/api/orders?page=${ordersPage}&per_page=${PER_PAGE}&search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}`);
  const data = await res.json();
  renderOrdersTable(data);
  renderPagination(data.total);
  populateCategoryFilter();
}
 
function renderOrdersTable(data) {
  const BADGE_MAP = { Mobile:'indigo', Informatique:'violet', Audio:'rose', Wearable:'amber', 'Périphérique':'green', Peripherique:'green', Stockage:'indigo', Affichage:'violet', Accessoire:'amber', Autre:'rose' };
  const tbody = document.getElementById('ordersBody');
  tbody.innerHTML = data.rows.map(r => `
    <tr>
      <td><span class="badge badge-indigo">#${r.ID_Commande || r.ID}</span></td>
      <td><span class="badge badge-violet">#${r.ID_Produit || ''}</span></td>
      <td>${r.Produit || '—'}</td>
      <td><span class="badge badge-${BADGE_MAP[r.Categorie]||'indigo'}">${r.Categorie||'—'}</span></td>
      <td class="mono">${parseFloat(r.Prix).toFixed(2)} DT</td>
      <td>${r.Quantite}</td>
      <td>${r.Remise > 0 ? `<span class="badge badge-amber">-${r.Remise}%</span>` : '—'}</td>
      <td class="mono">${fmt(r.CA_Brut)}</td>
      <td class="mono" style="color:#a5b4fc;font-weight:600">${fmt(r.CA_Net)}</td>
      <td class="mono" style="color:#fcd34d">${fmt(r.TVA)}</td>
      <td class="mono" style="color:#6ee7b7">${fmt(r.CA_TTC)}</td>
    </tr>
  `).join('');
}
 
function renderPagination(total) {
  const pages = Math.ceil(total / PER_PAGE);
  const pag = document.getElementById('pagination');
  let html = '';

  const delta = 2;
  const left = Math.max(1, ordersPage - delta);
  const right = Math.min(pages, ordersPage + delta);

  if (left > 1) {
    html += `<button class="page-btn" onclick="gotoPage(1)">1</button>`;
    if (left > 2) html += `<span style="color:var(--text-muted);padding:0 .3rem">…</span>`;
  }

  for (let i = left; i <= right; i++) {
    html += `<button class="page-btn ${i===ordersPage?'active':''}" onclick="gotoPage(${i})">${i}</button>`;
  }

  if (right < pages) {
    if (right < pages - 1) html += `<span style="color:var(--text-muted);padding:0 .3rem">…</span>`;
    html += `<button class="page-btn" onclick="gotoPage(${pages})">${pages}</button>`;
  }

  pag.innerHTML = html;
}
 
function gotoPage(p) { ordersPage = p; loadOrders(); }
 
function setupOrderSearch() {
  const inp = document.getElementById('orderSearch');
  inp?.addEventListener('input', debounce(() => { ordersPage = 1; loadOrders(); }, 300));
  const sel = document.getElementById('orderFilter');
  sel?.addEventListener('change', () => { ordersPage = 1; loadOrders(); });
}
 
async function populateCategoryFilter() {
  const sel = document.getElementById('orderFilter');
  if (!sel || sel.options.length > 1) return;
  try {
    const res = await fetch('/api/categories');
    const cats = await res.json();
    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c; opt.textContent = c;
      sel.appendChild(opt);
    });
  } catch(e) {}
}
 
// ─── Simulator ───────────────────────────────────────────────────
function setupSimulator() {
  const range = document.getElementById('simRemise');
  range?.addEventListener('input', () => {
    document.getElementById('remiseVal').textContent = range.value + '%';
    simulate();
  });
  document.getElementById('simPrix')?.addEventListener('input', simulate);
  document.getElementById('simQte')?.addEventListener('input', simulate);
}
 
async function simulate() {
  const prix = parseFloat(document.getElementById('simPrix')?.value) || 0;
  const qte = parseInt(document.getElementById('simQte')?.value) || 1;
  const remise = parseFloat(document.getElementById('simRemise')?.value) || 0;
  if (prix <= 0) return;
  try {
    const res = await fetch('/api/simulate', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ prix, quantite: qte, remise })
    });
    const d = await res.json();
    document.getElementById('simCaBrut').textContent = fmt(d.ca_brut);
    document.getElementById('simRemiseMnt').textContent = `- ${fmt(d.remise_montant)}`;
    document.getElementById('simCaNet').textContent = fmt(d.ca_net);
    document.getElementById('simTva').textContent = fmt(d.tva);
    document.getElementById('simCaTtc').textContent = fmt(d.ca_ttc);
    renderSimChart(d);
  } catch(e) {}
}
 
function renderSimChart(d) {
  const ctx = document.getElementById('chartSim');
  if (!ctx) return;
  if (chartSim) chartSim.destroy();
  chartSim = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['CA Net', 'Remise', 'TVA'],
      datasets: [{
        data: [d.ca_net, d.remise_montant, d.tva],
        backgroundColor: ['#6366f1','#f43f5e','#f59e0b'],
        borderWidth: 0, hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 }, padding: 10 } },
        tooltip: tooltipStyle()
      }
    }
  });
}
 
// ─── Data Generation & Upload ────────────────────────────────────
async function generateData() {
  const n = parseInt(document.getElementById('genN')?.value) || 50;
  document.getElementById('importStatus').textContent = '⏳ Génération en cours…';
  const res = await fetch('/api/generate', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ n })
  });
  const d = await res.json();
  if (d.success) {
    document.getElementById('importStatus').textContent = `✅ ${d.rows_generated} lignes générées avec succès !`;
    await loadSummary();
    showToast(`${d.rows_generated} lignes générées`, 'success');
  }
}
 
function setupUpload() {
  const inp = document.getElementById('csvUpload');
  inp?.addEventListener('change', async () => {
    if (!inp.files[0]) return;
    const form = new FormData();
    form.append('file', inp.files[0]);
    document.getElementById('importStatus').textContent = '⏳ Import en cours…';
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    const d = await res.json();
    if (d.success) {
      document.getElementById('importStatus').textContent = '✅ Fichier importé et analysé !';
      await loadSummary();
      showToast('CSV importé avec succès', 'success');
    } else {
      document.getElementById('importStatus').textContent = `❌ Erreur : ${d.error}`;
    }
  });
}
 
async function refreshData() {
  showToast('Actualisation…', 'success');
  await loadSummary();
}
 
// ─── Helpers ─────────────────────────────────────────────────────
function tooltipStyle() {
  return {
    backgroundColor: '#111c30',
    borderColor: 'rgba(255,255,255,0.07)',
    borderWidth: 1,
    titleColor: '#f0f4ff',
    bodyColor: '#94a3b8',
    padding: 10,
    callbacks: {
      label: ctx => ' ' + (typeof ctx.raw === 'number' ? fmt(ctx.raw) : ctx.raw)
    }
  };
}
 
function axisStyle() {
  return {
    grid: { color: 'rgba(255,255,255,0.04)' },
    ticks: { color: '#7989a8', font: { size: 11 } },
    border: { color: 'rgba(255,255,255,0.06)' }
  };
}
 
function debounce(fn, delay) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}
 
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast show ${type}`;
  setTimeout(() => t.className = 'toast', 2800);
}
 
// Add mono class helper used in table
document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = '.mono { font-family: var(--mono); font-size: .78rem; }';
  document.head.appendChild(style);

});

// ─── Simulator Product Search ─────────────────────────────────
function searchProduct() {
  const query = document.getElementById('simSearch').value.toLowerCase().trim();
  const suggestions = document.getElementById('simSuggestions');
  if (!summaryData || query.length < 2) { suggestions.style.display = 'none'; return; }

  if (!summaryData.rows) { suggestions.style.display = 'none'; return; }

  const nameMatches = Object.keys(summaryData.by_product || {})
    .filter(p => p.toLowerCase().includes(query));

  const idMatches = [...new Set(
    summaryData.rows
      .filter(r => String(r.ID_Produit || '').includes(query))
      .map(r => r.Produit)
      .filter(Boolean)
  )];

  window._simMatches = [...new Set([...nameMatches, ...idMatches])].slice(0, 6);

  if (window._simMatches.length === 0) { suggestions.style.display = 'none'; return; }

  suggestions.style.display = 'block';
  suggestions.innerHTML = window._simMatches.map((p, idx) => {
    const ca = summaryData.by_product[p] || 0;
    const idProd = (summaryData.rows.find(r => r.Produit === p) || {}).ID_Produit || '';
    return '<div class="sug-item" data-idx="' + idx + '" style="padding:.65rem 1rem;cursor:pointer;font-size:.85rem;color:#f0f4ff;border-bottom:1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background=\'rgba(99,102,241,0.15)\'" onmouseout="this.style.background=\'none\'">'
      + '<span style="font-weight:600">' + p + '</span>'
      + '<span style="color:#7989a8;font-size:.75rem;margin-left:.5rem">ID: #' + idProd + '</span>'
      + '<span style="color:#a5b4fc;float:right">' + fmt(ca) + '</span>'
      + '</div>';
  }).join('');

  document.querySelectorAll('.sug-item').forEach(el => {
    el.addEventListener('click', () => {
      const idx = parseInt(el.dataset.idx);
      selectProduct(window._simMatches[idx]);
    });
  });
}

function selectProductFromSearch() {
  const query = document.getElementById('simSearch').value.trim();
  if (!query || !summaryData) return;

  let name = Object.keys(summaryData.by_product)
    .find(p => p.toLowerCase() === query.toLowerCase());

  if (!name) {
    name = Object.keys(summaryData.by_product)
      .find(p => p.toLowerCase().includes(query.toLowerCase()));
  }

  if (!name && summaryData.rows) {
    const row = summaryData.rows.find(r => String(r.ID_Produit || '') === query);
    if (row) name = row.Produit;
  }

  if (!name) { showToast('Produit non trouvé', 'error'); return; }

  document.getElementById('simSearch').value = name;
  document.getElementById('simSuggestions').style.display = 'none';
  selectProduct(name);
}

function selectProduct(name) {
  document.getElementById('simSearch').value = name;
  document.getElementById('simSuggestions').style.display = 'none';

  if (!summaryData || !summaryData.rows) {
    showToast('Données non chargées, veuillez patienter', 'error');
    return;
  }

  const rows = summaryData.rows.filter(r => r.Produit === name);
  if (rows.length === 0) { showToast('Aucune commande pour ce produit', 'error'); return; }

  // Remplir le simulateur avec le prix moyen
  const avgPrix = rows.reduce((s, r) => s + parseFloat(r.Prix), 0) / rows.length;
  document.getElementById('simPrix').value = avgPrix.toFixed(2);

  // Lancer le calcul du simulateur
  simulate();

  // Afficher la section graphiques
  const section = document.getElementById('prodChartsSection');
  if (section) {
    section.style.display = 'block';
    setTimeout(() => {
      if (window.chartProdHist) window.chartProdHist.resize();
      if (window.chartProdDonutInst) window.chartProdDonutInst.resize();
    }, 100);
  }
  const titleEl = document.getElementById('simChartTitle');
  if (titleEl) titleEl.textContent = 'Analyse CA — ' + name;

  // Données
  const labels = rows.map((_, i) => 'Cmd ' + (i + 1));
  const caBrutVals = rows.map(r => parseFloat(r.CA_Brut));
  const caNetVals  = rows.map(r => parseFloat(r.CA_Net));
  const totalCaBrut = caBrutVals.reduce((a, b) => a + b, 0);
  const totalCaNet  = caNetVals.reduce((a, b) => a + b, 0);
  const totalTva    = rows.reduce((s, r) => s + parseFloat(r.TVA), 0);
  const totalRemise = totalCaBrut - totalCaNet;

  // Graphique barres CA Brut vs CA Net
  const ctx1 = document.getElementById('chartProdHistory');
  if (ctx1) {
    if (window.chartProdHist) window.chartProdHist.destroy();
    window.chartProdHist = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: 'CA Brut', data: caBrutVals, backgroundColor: 'rgba(139,92,246,0.7)', borderRadius: 6, borderSkipped: false },
          { label: 'CA Net',  data: caNetVals,  backgroundColor: 'rgba(99,102,241,0.9)',  borderRadius: 6, borderSkipped: false }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, labels: { color: '#94a3b8', font: { size: 11 } } },
          tooltip: tooltipStyle()
        },
        scales: {
          x: { ...axisStyle(), ticks: { ...axisStyle().ticks, maxTicksLimit: 10 } },
          y: { ...axisStyle(), ticks: { ...axisStyle().ticks, callback: function(v) { return (v/1000).toFixed(0) + 'k'; } } }
        }
      }
    });
  }

  // Graphique donut
  const ctx2 = document.getElementById('chartProdDonut');
  if (ctx2) {
    if (window.chartProdDonutInst) window.chartProdDonutInst.destroy();
    window.chartProdDonutInst = new Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: ['CA Net', 'Remise', 'TVA'],
        datasets: [{ data: [totalCaNet, totalRemise, totalTva], backgroundColor: ['#6366f1','#f43f5e','#f59e0b'], borderWidth: 0, hoverOffset: 8 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, padding: 8 } },
          tooltip: tooltipStyle()
        }
      }
    });
  }

  showToast('Analyse de ' + name + ' chargee', 'success');
}


// ─── Mono style helper ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = '.mono { font-family: var(--mono); font-size: .78rem; }';
  document.head.appendChild(style);


});


async function loadMatplotlibChart() {
  const query = document.getElementById('mplSearch').value.trim();
  if (!query) { showToast('Entrez un nom de produit', 'error'); return; }

  // Chercher le nom exact
  let name = Object.keys(summaryData.by_product || {})
    .find(p => p.toLowerCase() === query.toLowerCase());

  if (!name) {
    name = Object.keys(summaryData.by_product || {})
      .find(p => p.toLowerCase().includes(query.toLowerCase()));
  }

  if (!name) {
    // Chercher par ID produit
    const row = (summaryData.rows || [])
      .find(r => String(r.ID_Produit || '') === query);
    if (row) name = row.Produit;
  }

  if (!name) { showToast('Produit non trouvé', 'error'); return; }

  const container = document.getElementById('mplChartContainer');
  container.innerHTML = '<p style="color:var(--text-secondary)">⏳ Génération du graphique...</p>';

  const res = await fetch(`/api/chart_product?name=${encodeURIComponent(name)}`);
  const data = await res.json();

  if (data.error) {
    container.innerHTML = `<p style="color:#f43f5e">${data.error}</p>`;
    return;
  }

  container.innerHTML = `
    <p style="color:#a5b4fc; margin-bottom:.75rem; font-weight:600">${name}</p>
    <img src="${data.image_url}?t=${Date.now()}" style="width:100%; border-radius:10px;" alt="Graphique ${name}"/>
  `;
}

