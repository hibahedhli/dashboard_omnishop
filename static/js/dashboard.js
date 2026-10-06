const state = {
  summary: null,
  ordersPage: 1,
  perPage: 10,
  charts: {},
  productMatches: []
};

const PALETTE = [
  '#6366f1', '#8b5cf6', '#a78bfa', '#f43f5e', '#fb923c',
  '#facc15', '#34d399', '#38bdf8', '#e879f9', '#f472b6'
];

const DISPLAY_CATEGORY_NAMES = {
  'Accessoire': 'Accessories',
  'Peripherique': 'Peripherals',
  'Informatique': 'Computing',
  'Stockage': 'Storage',
  'Wearable': 'Wearables',
  'Audio': 'Audio',
  'Mobile': 'Mobile',
  'Affichage': 'Displays'
};

const DISPLAY_PRODUCT_NAMES = {
  'Tapis de souris XL': 'XL Mouse Pad',
  'Chargeur USB-C': 'USB-C Charger',
  'Souris Razer': 'Razer Mouse',
  'Laptop Dell': 'Dell Laptop',
  'Clavier Logitech': 'Logitech Keyboard',
  'Disque SSD 1TB': '1TB SSD',
  'Montre Apple Watch': 'Apple Watch',
  'Casque Bose': 'Bose Headphones',
  'Webcam Logitech': 'Logitech Webcam',
  'Smartphone Samsung': 'Samsung Smartphone',
  'Ecouteurs Sony': 'Sony Earbuds',
  'Hub USB': 'USB Hub',
  'Imprimante HP': 'HP Printer',
  'Ecran LG 27': 'LG 27" Monitor',
  'Tablette iPad': 'iPad Tablet'
};

function displayCategoryName(name) {
  return DISPLAY_CATEGORY_NAMES[name] || name;
}

function displayProductName(name) {
  return DISPLAY_PRODUCT_NAMES[name] || name;
}

function getCurrencyConfig() {
  return state.summary?.currency || {
    currency: 'TND',
    symbol: 'DT',
    locale: 'fr-TN'
  };
}

function getCurrencySymbol() {
  return getCurrencyConfig().symbol || 'DT';
}

function updateCurrencyLabels() {
  const label = document.getElementById('simPriceLabel');
  if (label) {
    label.textContent = `Unit price (${getCurrencySymbol()})`;
  }
}

function fmtCurrency(value) {
  const config = getCurrencyConfig();
  const number = Number(value) || 0;

  try {
    return new Intl.NumberFormat(config.locale || 'en-GB', {
      style: 'currency',
      currency: config.currency || 'TND',
      maximumFractionDigits: 2
    }).format(number);
  } catch (error) {
    return `${number.toLocaleString('en-US', {
      maximumFractionDigits: 2
    })} ${config.symbol || ''}`.trim();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadSummary();
  setupNav();
  setupOrderSearch();
  setupSimulator();
  setupUpload();
});

async function loadSummary() {
  try {
    const res = await fetch('/api/summary');
    if (!res.ok) throw new Error('Summary request failed');

    state.summary = await res.json();
    updateCurrencyLabels();

    renderOverview();
    renderProducts();
    renderAnalytics();
    renderDatasetQuality();
    populateCategoryFilter();
    setupProductSearch();
  } catch (error) {
    console.error(error);
    showToast('Error loading data', 'error');
  }
}

function renderDatasetQuality() {
  const profile = state.summary?.profile;
  if (!profile) return;

  const rows = document.getElementById('qualityRows');
  const validRows = document.getElementById('qualityValidRows');
  const invalidRows = document.getElementById('qualityInvalidRows');
  const columns = document.getElementById('qualityColumns');
  const encoding = document.getElementById('qualityEncoding');

  if (rows) rows.textContent = profile.rows ?? 'N/D';
  if (validRows) validRows.textContent = profile.valid_rows ?? 'N/D';
  if (invalidRows) invalidRows.textContent = profile.invalid_rows ?? 'N/D';
  if (columns) columns.textContent = profile.original_columns?.length ?? 'N/D';
  if (encoding) encoding.textContent = profile.encoding || 'N/D';
}

function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', event => {
      event.preventDefault();

      const section = item.dataset.section;

      document.querySelectorAll('.nav-item')
        .forEach(nav => nav.classList.remove('active'));

      document.querySelectorAll('.section')
        .forEach(sec => sec.classList.remove('active'));

      item.classList.add('active');
      document.getElementById(`section-${section}`)?.classList.add('active');

      const title = item.querySelector('span')?.textContent;
      if (title) {
        document.getElementById('pageTitle').textContent = title;
      }

      if (section === 'orders') {
        state.ordersPage = 1;
        loadOrders();
      }

      if (section === 'products') {
        renderProducts();
      }

      if (section === 'analytics') {
        renderAnalytics();
      }

      if (section === 'simulator') {
        simulate();
      }

      if (window.innerWidth < 768) {
        document.getElementById('sidebar')?.classList.remove('open');
      }
    });
  });

  document.getElementById('menuToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('open');
  });
}

function renderOverview() {
  const s = state.summary;
  if (!s) return;

  animateValue('kpiCANet', s.ca_total || 0, getCurrencySymbol());
  const ordersKpi = document.getElementById('kpiOrders');
  const avgKpi = document.getElementById('kpiAvg');

  if (s.has_order_id) {
    animateValue('kpiOrders', s.total_orders ?? 0, '');
    animateValue('kpiAvg', s.avg_order || 0, getCurrencySymbol());
  } else {
    if (ordersKpi) ordersKpi.textContent = 'N/D';
    if (avgKpi) avgKpi.textContent = 'N/D';
  }
  const vatAvailable = s.tva_total !== null && s.tva_total !== undefined;

  if (vatAvailable) {
    animateValue('kpiTVA', s.tva_total, getCurrencySymbol());
  } else {
    const vatKpi = document.getElementById('kpiTVA');
    if (vatKpi) vatKpi.textContent = 'N/D';
  }

  const netRatio = s.ca_brut_total > 0
    ? (s.ca_total / s.ca_brut_total) * 100
    : 0;

  const vatRate = vatAvailable && s.ca_total > 0
    ? (s.tva_total / s.ca_total) * 100
    : null;

  const canetDelta = document.getElementById('kpiCANetDelta');
  const ordersDelta = document.getElementById('kpiOrdersDelta');
  const avgDelta = document.getElementById('kpiAvgDelta');
  const tvaDelta = document.getElementById('kpiTVADelta');

  if (canetDelta) canetDelta.textContent = `${netRatio.toFixed(1)}% of gross revenue`;
  if (ordersDelta) ordersDelta.textContent = `${s.total_rows ?? 0} sales rows`;
  if (avgDelta) avgDelta.textContent = s.has_order_id ? 'Per order' : 'Order ID unavailable';
  if (tvaDelta) {
    tvaDelta.textContent = vatRate !== null
      ? `${vatRate.toFixed(1)}% of net revenue`
      : 'Not available in this dataset';
  }

  const bestName = document.getElementById('bestName');
  const bestValue = document.getElementById('bestValue');

  if (bestName) {
    bestName.textContent = s.has_order_id && s.best_order_id != null
      ? `Order #${s.best_order_id}`
      : 'N/D';
  }

  if (bestValue) {
    bestValue.textContent = s.has_order_id && s.best_order_ca != null
      ? fmt(s.best_order_ca)
      : 'N/D';
  }

  renderChartMonthly();
  renderChartCategories();
  renderInsights(s.insights);
}

function displayInsightText(text) {
  let result = String(text ?? "");

  for (const [rawName, displayName] of Object.entries(DISPLAY_PRODUCT_NAMES)) {
    result = result.split(rawName).join(displayName);
  }

  for (const [rawName, displayName] of Object.entries(DISPLAY_CATEGORY_NAMES)) {
    result = result.split(rawName).join(displayName);
  }

  return result;
}

function renderInsights(insights) {
  const container = document.getElementById("insightsGrid");
  if (!container) return;

  if (!Array.isArray(insights) || insights.length === 0) {
    container.innerHTML = `
      <div class="insight-card insight-info">
        <div class="insight-content">
          <h3>No insights available</h3>
          <p>The available data is not sufficient to generate an automatic analysis yet.</p>
        </div>
      </div>
    `;
    return;
  }

  const iconByType = {
    success: "✓",
    warning: "!",
    info: "i",
    danger: "!"
  };

  container.innerHTML = insights.map(insight => {
    const type = ["success", "warning", "info", "danger"].includes(insight.type)
      ? insight.type
      : "info";

    const icon = iconByType[type];

    return `
      <article class="insight-card insight-${type}">
        <div class="insight-icon">${icon}</div>
        <div class="insight-content">
          <h3>${escapeHtml(displayInsightText(insight.title || "Commercial Insight"))}</h3>
          <p>${escapeHtml(displayInsightText(insight.message || ""))}</p>
          ${insight.action
            ? `<div class="insight-action">→ ${escapeHtml(displayInsightText(insight.action))}</div>`
            : ""}
        </div>
      </article>
    `;
  }).join("");
}

function animateValue(id, to, suffix) {
  const el = document.getElementById(id);
  if (!el) return;

  const target = Number(to) || 0;
  const isFloat = target % 1 !== 0;
  const duration = 700;
  const start = performance.now();

  function update(timestamp) {
    const progress = Math.min((timestamp - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const value = target * ease;

    if (suffix) {
      el.textContent = fmtCurrency(value);
    } else if (isFloat) {
      el.textContent = value.toFixed(1);
    } else {
      el.textContent = Math.floor(value).toLocaleString('fr-FR');
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

function fmt(value) {
  return fmtCurrency(value);
}

function axisStyle() {
  return {
    color: '#94a3b8',
    grid: { color: 'rgba(148,163,184,0.08)' },
    ticks: {
      color: '#94a3b8',
      font: { size: 11 }
    }
  };
}

function tooltipStyle() {
  return {
    backgroundColor: '#111827',
    titleColor: '#f8fafc',
    bodyColor: '#cbd5e1',
    borderColor: 'rgba(148,163,184,0.15)',
    borderWidth: 1,
    padding: 10
  };
}

function destroyChart(name) {
  if (state.charts[name]) {
    state.charts[name].destroy();
    state.charts[name] = null;
  }
}

function renderChartMonthly() {
  const ctx = document.getElementById('chartMonthly');
  const s = state.summary;

  if (!ctx || !s) return;

  destroyChart('monthly');

  const monthly = s.monthly_ca || {};
  const labels = Object.keys(monthly);
  const values = Object.values(monthly);

  if (!s.has_date || labels.length === 0) {
    const container = ctx.parentElement;

    if (container) {
      container.classList.add('chart-unavailable');

      const existingMessage = container.querySelector('.chart-unavailable-message');

      if (!existingMessage) {
        const message = document.createElement('p');
        message.className = 'chart-unavailable-message';
        message.textContent =
          "Monthly analysis unavailable: no date column was detected in this dataset.";
        container.appendChild(message);
      }
    }

    state.charts.monthly = null;
    return;
  }

  state.charts.monthly = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: `Net Revenue (${getCurrencySymbol()})`,
        data: values,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.15)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: '#6366f1',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: tooltipStyle()
      },
      scales: {
        x: axisStyle(),
        y: {
          ...axisStyle(),
          ticks: {
            ...axisStyle().ticks,
            callback: value => `${(value / 1000).toFixed(0)}k${getCurrencySymbol()}`
          }
        }
      }
    }
  });
}

function renderChartCategories() {
  const ctx = document.getElementById('chartCategories');
  const s = state.summary;

  if (!ctx || !s) return;

  destroyChart('categories');

  const cats = s.by_category || {};
  const labels = Object.keys(cats).map(displayCategoryName);

  if (!s.has_category || labels.length === 0) {
    const container = ctx.parentElement;
    if (container) {
      container.classList.add('chart-unavailable');
    }
    return;
  }

  state.charts.categories = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: Object.values(cats),
        backgroundColor: PALETTE,
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { size: 11 },
            padding: 10
          }
        },
        tooltip: tooltipStyle()
      }
    }
  });
}

function renderProducts() {
  const s = state.summary;
  if (!s) return;

  const products = s.top5_products || [];
  const maxValue = products[0]?.revenue || 1;

  const ctx = document.getElementById('chartTopProducts');

  if (ctx) {
    destroyChart('topProducts');

    state.charts.topProducts = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: products.map(product =>
          displayProductName(
            product.product_name ||
            product.product_id ||
            'Unknown product'
          )
        ),
        datasets: [{
          label: 'Net Revenue',
          data: products.map(product => product.revenue || 0),
          backgroundColor: PALETTE.slice(0, products.length),
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: tooltipStyle()
        },
        scales: {
          x: {
            ...axisStyle(),
            ticks: {
              ...axisStyle().ticks,
              callback: value => `${(value / 1000).toFixed(0)}k${getCurrencySymbol()}`
            }
          },
          y: axisStyle()
        }
      }
    });
  }

  const ctx2 = document.getElementById('chartBrutNet');

  if (ctx2) {
    destroyChart('brutNet');

    state.charts.brutNet = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Gross Revenue', 'Net Revenue', 'VAT'],
        datasets: [{
          data: [
            s.ca_brut_total || 0,
            s.ca_total || 0,
            s.tva_total || 0
          ],
          backgroundColor: ['#6366f1', '#8b5cf6', '#f59e0b'],
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: tooltipStyle()
        },
        scales: {
          x: axisStyle(),
          y: {
            ...axisStyle(),
            ticks: {
              ...axisStyle().ticks,
              callback: value => `${(value / 1000).toFixed(0)}k${getCurrencySymbol()}`
            }
          }
        }
      }
    });
  }

  const grid = document.getElementById('productsGrid');

  if (grid) {
    if (products.length === 0) {
      grid.innerHTML = '<p>No products available.</p>';
      return;
    }

    grid.innerHTML = products.map((product, index) => {
        const name = displayProductName(
          product.product_name ||
          product.product_id ||
          'Unknown product'
        );

      const revenue = Number(product.revenue) || 0;

      return `
        <div class="product-card">
          <div class="product-rank">#${index + 1}</div>
          <div class="product-name">${escapeHtml(name)}</div>
          <div class="product-ca">${fmt(revenue)}</div>
          <div class="product-bar">
            <div class="product-bar-fill"
                 style="width:${Math.min(revenue / maxValue * 100, 100).toFixed(1)}%">
            </div>
          </div>
        </div>
      `;
    }).join('');
  }
}

function renderAnalytics() {
  const s = state.summary;
  if (!s) return;

  const retention =
    s.ca_brut_total > 0
      ? ((s.ca_total / s.ca_brut_total) * 100).toFixed(1)
      : '0.0';

  const metrics = [
    {
      label: 'Total Gross Revenue',
      value: fmt(s.ca_brut_total),
      desc: 'Before Discounts'
    },
    {
      label: 'Total Net Revenue',
      value: fmt(s.ca_total),
      desc: 'After Discounts'
    },
    {
      label: 'Collected VAT',
      value: s.tva_total != null ? fmt(s.tva_total) : 'N/D',
      desc: 'Calculated from Net Revenue'
    },
    {
      label: 'Total Revenue incl. VAT',
      value: s.ca_ttc_total != null ? fmt(s.ca_ttc_total) : 'N/D',
      desc: 'Net Revenue + VAT'
    },
    {
      label: 'Net/Gross Rate',
      value: `${retention}%`,
      desc: 'Revenue retained after discounts'
    },
    {
      label: 'Average Order Value',
      value: s.has_order_id ? fmt(s.avg_order) : 'N/D',
      desc: s.has_order_id ? 'Per order' : 'Order ID unavailable'
    },
    {
      label: 'Top Order',
      value: s.has_order_id && s.best_order_id != null
        ? `#${s.best_order_id}`
        : 'N/D',
      desc: s.has_order_id
        ? fmt(s.best_order_ca)
        : 'Order ID unavailable'
    },
    {
      label: 'Number of Orders',
      value: s.has_order_id ? s.total_orders : 'N/D',
      desc: s.has_order_id
        ? 'Distinct Orders'
        : 'Order ID unavailable'
    }
  ];

  const grid = document.getElementById('analyticsGrid');

  if (grid) {
    grid.innerHTML = metrics.map(metric => `
      <div class="analytics-card">
        <div class="analytics-label">${metric.label}</div>
        <div class="analytics-value">${metric.value}</div>
        <div class="analytics-desc">${metric.desc}</div>
      </div>
    `).join('');
  }

  const categoryCard = document.getElementById('categoryAnalyticsCard');
  const categoryMessage = document.getElementById('categoryUnavailableMessage');
  const ctx = document.getElementById('chartCatBar');

  if (categoryCard && ctx) {
    destroyChart('categoryBar');

    const cats = s.by_category || {};
    const labels = Object.keys(cats).map(displayCategoryName);
    const categoryAvailable = s.has_category && labels.length > 0;

    if (!categoryAvailable) {
      ctx.style.display = 'none';

      if (categoryMessage) {
        categoryMessage.style.display = 'block';
      }

      categoryCard.querySelector('.chart-header h3').textContent =
        'Category Analysis';
    } else {
      ctx.style.display = 'block';

      if (categoryMessage) {
        categoryMessage.style.display = 'none';
      }

      categoryCard.querySelector('.chart-header h3').textContent =
        'Revenue by Category';

      state.charts.categoryBar = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            data: Object.values(cats),
            backgroundColor: PALETTE,
            borderRadius: 8,
            borderSkipped: false
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: tooltipStyle()
          },
          scales: {
            x: axisStyle(),
            y: {
              ...axisStyle(),
              ticks: {
                ...axisStyle().ticks,
                callback: value => `${(value / 1000).toFixed(0)}k${getCurrencySymbol()}`
              }
            }
          }
        }
      });
    }
  }
}

async function loadOrders() {
  try {
    const search =
      document.getElementById('orderSearch')?.value || '';

    const category =
      document.getElementById('orderFilter')?.value || '';

    const params = new URLSearchParams({
      page: state.ordersPage,
      per_page: state.perPage,
      search,
      category
    });

    const res = await fetch(`/api/orders?${params.toString()}`);

    if (!res.ok) throw new Error('Orders request failed');

    const data = await res.json();

    renderOrdersTable(data);
    renderPagination(data.total || 0);
  } catch (error) {
    console.error(error);
    showToast('Error loading orders', 'error');
  }
}

function renderOrdersTable(data) {
  const tbody = document.getElementById('ordersBody');
  if (!tbody) return;

  const rows = data.rows || [];

  if (rows.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" style="text-align:center;padding:2rem;">
          No data found.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = rows.map(row => {
    const price = Number(row.price) || 0;
    const quantity = Number(row.quantity) || 0;
    const discount = Number(row.discount) || 0;

    const orderId = row.order_id ?? 'N/D';
    const productId = row.product_id ?? 'N/D';
    const productName = row.product_name ?? 'N/D';
    const category = row.category ?? 'N/D';
    const date = row.date ?? 'N/D';

    return `
      <tr>
        <td>
          <span class="badge badge-indigo">
            ${escapeHtml(String(orderId))}
          </span>
        </td>

        <td>
          <span class="badge badge-violet">
            ${escapeHtml(String(productId))}
          </span>
        </td>

        <td>${escapeHtml(String(displayProductName(productName)))}</td>

        <td>
          <span class="badge badge-indigo">
            ${escapeHtml(String(displayCategoryName(category)))}
          </span>
        </td>

        <td>${fmt(price)}</td>

        <td>${quantity}</td>

        <td>
          ${
            discount > 0
              ? `<span class="badge badge-amber">-${discount}%</span>`
              : '—'
          }
        </td>

        <td class="mono">${fmt(row.CA_Brut)}</td>

        <td class="mono">${fmt(row.CA_Net)}</td>

        <td class="mono">${row.TVA != null ? fmt(row.TVA) : 'N/D'}</td>

        <td class="mono">${row.CA_TTC != null ? fmt(row.CA_TTC) : 'N/D'}</td>
      </tr>
    `;
  }).join('');
}

function renderPagination(total) {
  const pagination = document.getElementById('pagination');
  if (!pagination) return;

  const pages = Math.ceil(total / state.perPage);

  if (pages <= 1) {
    pagination.innerHTML = '';
    return;
  }

  let html = '';

  const delta = 2;
  const left = Math.max(1, state.ordersPage - delta);
  const right = Math.min(pages, state.ordersPage + delta);

  if (left > 1) {
    html += `<button class="page-btn" onclick="gotoPage(1)">1</button>`;

    if (left > 2) {
      html += `<span style="color:var(--text-muted);padding:0 .3rem">…</span>`;
    }
  }

  for (let page = left; page <= right; page++) {
    html += `
      <button class="page-btn ${page === state.ordersPage ? 'active' : ''}"
              onclick="gotoPage(${page})">
        ${page}
      </button>
    `;
  }

  if (right < pages) {
    if (right < pages - 1) {
      html += `<span style="color:var(--text-muted);padding:0 .3rem">…</span>`;
    }

    html += `
      <button class="page-btn" onclick="gotoPage(${pages})">
        ${pages}
      </button>
    `;
  }

  pagination.innerHTML = html;
}

function gotoPage(page) {
  state.ordersPage = page;
  loadOrders();
}

function setupOrderSearch() {
  const input = document.getElementById('orderSearch');

  input?.addEventListener('input', debounce(() => {
    state.ordersPage = 1;
    loadOrders();
  }, 300));

  const select = document.getElementById('orderFilter');

  select?.addEventListener('change', () => {
    state.ordersPage = 1;
    loadOrders();
  });
}

async function populateCategoryFilter() {
  const select = document.getElementById('orderFilter');
  const s = state.summary;

  if (!select || !s) return;

  if (!s.has_category) {
    select.innerHTML = '<option value="">Category unavailable</option>';
    select.disabled = true;
    return;
  }

  select.disabled = false;

  try {
    const res = await fetch('/api/categories');

    if (!res.ok) return;

    const categories = await res.json();

    select.innerHTML = '<option value="">All categories</option>';

    categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = displayCategoryName(category);
      select.appendChild(option);
    });
  } catch (error) {
    console.error(error);
  }
}


async function searchProduct() {
  const input = document.getElementById('simSearch');
  const suggestions = document.getElementById('simSuggestions');

  if (!input || !suggestions) return;

  const query = input.value.trim();

  if (!query) {
    suggestions.innerHTML = '';
    suggestions.style.display = 'none';
    return;
  }

  try {
    const res = await fetch(
      `/api/orders?search=${encodeURIComponent(query)}&page=1&per_page=10`
    );

    if (!res.ok) {
      throw new Error('Product search failed');
    }

    const data = await res.json();
    const rows = data.rows || [];

    const products = [];
    const seen = new Set();

    rows.forEach(row => {
      const id = String(row.product_id || '').trim();
      const name = String(row.product_name || '').trim();

      const key = `${id}|${name}`;

      if (!seen.has(key) && (id || name)) {
        seen.add(key);
        products.push({ id, name });
      }
    });

    if (!products.length) {
      suggestions.innerHTML =
        '<div style="padding:.75rem;color:var(--text-secondary);">No product found</div>';
      suggestions.style.display = 'block';
      return;
    }

    suggestions.innerHTML = products.map(product => `
      <div
        class="sim-product-suggestion"
        data-product-id="${product.id.replace(/"/g, '&quot;')}"
        data-product-name="${product.name.replace(/"/g, '&quot;')}"
        style="padding:.65rem .8rem;cursor:pointer;"
      >
        <strong>${product.name || 'Unnamed product'}</strong>
        ${product.id ? `<small style="display:block;color:var(--text-secondary);">${product.id}</small>` : ''}
      </div>
    `).join('');

    suggestions.style.display = 'block';

    suggestions.querySelectorAll('.sim-product-suggestion').forEach(item => {
      item.addEventListener('click', () => {
        input.value = item.dataset.productName || item.dataset.productId || '';
        input.dataset.productId = item.dataset.productId || '';
        suggestions.style.display = 'none';
      });
    });

  } catch (error) {
    console.error(error);
    suggestions.innerHTML =
      '<div style="padding:.75rem;color:#ef4444;">Search failed</div>';
    suggestions.style.display = 'block';
  }
}

async function selectProductFromSearch() {
  const input = document.getElementById('simSearch');

  if (!input) return;

  const query = input.value.trim();

  if (!query) {
    showToast('Enter a product name or ID first.', 'error');
    return;
  }

  try {
    const res = await fetch(
      `/api/orders?search=${encodeURIComponent(query)}&page=1&per_page=1`
    );

    if (!res.ok) {
      throw new Error('Product search failed');
    }

    const data = await res.json();
    const row = (data.rows || [])[0];

    if (!row) {
      showToast('Product not found.', 'error');
      return;
    }

    const price = parseFloat(row.price);

    if (Number.isFinite(price) && price > 0) {
      const priceInput = document.getElementById('simPrice');

      if (priceInput) {
        priceInput.value = price;
      }
    }

    input.value = row.product_name || row.product_id || query;
    input.dataset.productId = row.product_id || '';

    const label = document.getElementById('simPriceLabel');

    if (label) {
      label.textContent = `Unit price (${getCurrencyConfig().symbol || '?'})`;
    }

    document.getElementById('simSuggestions')?.style.setProperty(
      'display',
      'none'
    );

    simulate();

  } catch (error) {
    console.error(error);
    showToast('Unable to analyze this product.', 'error');
  }
}

function setupSimulator() {
  const range = document.getElementById('simDiscount');

  range?.addEventListener('input', () => {
    const value = document.getElementById('remiseVal');
    if (value) {
      value.textContent = `${range.value}%`;
    }

    simulate();
  });

  document.getElementById('simQte')
    ?.addEventListener('input', simulate);
}

window.simulate = async function simulate() {
  const price =
    parseFloat(document.getElementById('simPrice')?.value) || 0;

  const quantity =
    parseInt(document.getElementById('simQte')?.value) || 1;

  const discount =
    parseFloat(document.getElementById('simDiscount')?.value) || 0;

  if (price <= 0 || quantity <= 0) return;

  try {
    console.log('SIMULATOR INPUT:', {
      price,
      quantity,
      discount
    });

    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prix: price,
        quantite: quantity,
        remise: discount
      })
    });

    const data = await res.json();

    console.log('SIMULATOR RESPONSE:', data);

    if (!res.ok || data.error) {
      throw new Error(data.error || 'Simulation failed');
    }

    document.getElementById('simCaBrut').textContent =
      fmt(data.ca_brut);

    document.getElementById('simDiscountMnt').textContent =
      `- ${fmt(data.remise_montant)}`;

    document.getElementById('simCaNet').textContent =
      fmt(data.ca_net);

    document.getElementById('simTva').textContent =
      fmt(data.tva);

    document.getElementById('simCaTtc').textContent =
      fmt(data.ca_ttc);

    renderSimChart(data);
  } catch (error) {
    console.error(error);
  }
}

function renderSimChart(data) {
  const ctx = document.getElementById('chartSim');
  if (!ctx) return;

  destroyChart('simulator');

  /*
   * These values are not components of one additive total:
   * CA Net + discount + TVA would mix different bases.
   *
   * We therefore compare the two revenue states and VAT.
   */
  state.charts.simulator = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Gross Revenue', 'Net Revenue', 'VAT'],
      datasets: [{
        data: [
          data.ca_brut || 0,
          data.ca_net || 0,
          data.tva || 0
        ],
        backgroundColor: ['#6366f1', '#8b5cf6', '#f59e0b'],
        borderRadius: 8,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: tooltipStyle()
      },
      scales: {
        x: axisStyle(),
        y: {
          ...axisStyle(),
          ticks: {
            ...axisStyle().ticks,
            callback: value => `${(value / 1000).toFixed(0)}k${getCurrencySymbol()}`
          }
        }
      }
    }
  });
}

function setupUpload() {
  const input = document.getElementById('csvUpload');

  input?.addEventListener('change', async () => {
    if (!input.files?.[0]) return;

    const form = new FormData();
    form.append('file', input.files[0]);

    const status = document.getElementById('importStatus');

    if (status) {
      status.textContent = 'Import en cours…';
    }

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: form
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Import failed');
      }

      if (status) {
        const profile = data.profile || {};
        const fields = profile.fields || {};

        const analyses = [
          {
            label: 'Orders',
            available: fields.order_id?.detected === true
          },
          {
            label: 'Products',
            available:
              fields.product_name?.detected === true ||
              fields.product_id?.detected === true
          },
          {
            label: 'Categories',
            available: fields.category?.detected === true
          },
          {
            label: 'Dates',
            available: fields.date?.detected === true
          },
          {
            label: 'TVA',
            available: fields.vat_rate?.detected === true
          }
        ];

        const analysisText = analyses
          .map(item => `${item.available ? '✓' : '⚠'} ${item.label}`)
          .join(' · ');

        status.innerHTML =
          `<strong>File imported and analyzed!</strong><br>` +
          `${profile.rows ?? 'N/D'} lignes · ` +
          `${profile.valid_rows ?? 'N/D'} valides · ` +
          `${profile.invalid_rows ?? 'N/D'} ignorées · ` +
          `${profile.original_columns?.length ?? 'N/D'} colonnes<br>` +
          `<span style="font-size:.78rem;">${analysisText}</span>`;
      }

      await loadSummary();
      showToast('CSV imported successfully', 'success');
    } catch (error) {
      console.error(error);

      if (status) {
        status.textContent =
          `Error: ${error.message}`;
      }

      showToast('CSV import failed', 'error');
    } finally {
      input.value = '';
    }
  });
}

function setupProductSearch() {
  const input =
    document.getElementById('simSearch');

  const suggestions =
    document.getElementById('simSuggestions');

  if (!input || !suggestions) return;

  input.addEventListener('input', debounce(() => {
    const query = input.value.trim().toLowerCase();

    if (!query || !state.summary) {
      suggestions.innerHTML = '';
      state.productMatches = [];
      return;
    }

    const products =
      state.summary.top5_products ||
      [];

    const allProducts =
      Object.keys(state.summary.by_product || {});

    const matches = [
      ...allProducts.filter(product =>
        product.toLowerCase().includes(query)
      ),
      ...products
        .map(product =>
          product.product_name ||
          product.product_id
        )
        .filter(Boolean)
    ];

    state.productMatches =
      [...new Set(matches)].slice(0, 8);

    suggestions.innerHTML =
      state.productMatches.map((product, index) => `
        <div
          class="sug-item"
          data-idx="${index}"
          style="
            padding:.65rem 1rem;
            cursor:pointer;
            font-size:.85rem;
            color:#f0f4ff;
            border-bottom:1px solid rgba(255,255,255,0.05);
          "
        >
          ${escapeHtml(displayProductName(product))}
        </div>
      `).join('');

    suggestions.querySelectorAll('.sug-item')
      .forEach(item => {
        item.addEventListener('click', () => {
          const index = Number(item.dataset.idx);
          const product = state.productMatches[index];

          input.value = product;
          suggestions.innerHTML = '';

          loadProductAnalysis(product);
        });
      });
  }, 200));
}

function findProductName(query) {
  const s = state.summary;
  if (!s) return null;

  const normalized =
    String(query).trim().toLowerCase();

  const names =
    Object.keys(s.by_product || {});

  let name = names.find(product =>
    product.toLowerCase() === normalized
  );

    if (!name) {
      name = names.find(product =>
        displayProductName(product).toLowerCase() === normalized
      );
    }

  if (!name) {
    name = names.find(product =>
      product.toLowerCase().includes(normalized)
    );
  }

  if (!name && s.rows) {
    const row = s.rows.find(record =>
      String(record.product_id || '').toLowerCase() === normalized
    );

    if (row) {
      name = row.product_name;
    }
  }

  return name || null;
}

function loadProductAnalysis(query) {
  const name = findProductName(query);

  if (!name) {
    showToast('Product not found', 'error');
    return;
  }

  const input =
    document.getElementById('simSearch');

  if (input) {
    input.value = name;
  }

  const rows =
    (state.summary.rows || [])
      .filter(row => row.product_name === name);

  if (rows.length === 0) {
    showToast('No rows found for this product', 'error');
    return;
  }

  const averagePrice =
    rows.reduce(
      (sum, row) => sum + (Number(row.price) || 0),
      0
    ) / rows.length;

  const simPrice =
    document.getElementById('simPrix');

  if (simPrice) {
    simPrice.value = averagePrice.toFixed(2);
  }

  simulate();
  renderProductCharts(name, rows);
}

function renderProductCharts(name, rows) {
  const labels = rows.map((row, index) =>
    row.date || `Ligne ${index + 1}`
  );

  const caBrutValues =
    rows.map(row => Number(row.CA_Brut) || 0);

  const caNetValues =
    rows.map(row => Number(row.CA_Net) || 0);

  const totalCaNet =
    caNetValues.reduce((sum, value) => sum + value, 0);

  const totalCaBrut =
    caBrutValues.reduce((sum, value) => sum + value, 0);

  const totalTva =
    rows.reduce(
      (sum, row) => sum + (Number(row.TVA) || 0),
      0
    );

  const totalDiscount =
    rows.reduce(
      (sum, row) =>
        sum + (Number(row.Remise_Montant) || 0),
      0
    );

  const ctx1 =
    document.getElementById('chartProdHist');

  if (ctx1) {
    destroyChart('productHistory');

    state.charts.productHistory = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Gross Revenue',
            data: caBrutValues,
            backgroundColor: 'rgba(139,92,246,0.7)',
            borderRadius: 6,
            borderSkipped: false
          },
          {
            label: 'Net Revenue',
            data: caNetValues,
            backgroundColor: 'rgba(99,102,241,0.9)',
            borderRadius: 6,
            borderSkipped: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#94a3b8',
              font: { size: 11 }
            }
          },
          tooltip: tooltipStyle()
        },
        scales: {
          x: {
            ...axisStyle(),
            ticks: {
              ...axisStyle().ticks,
              maxTicksLimit: 10
            }
          },
          y: {
            ...axisStyle(),
            ticks: {
              ...axisStyle().ticks,
              callback: value =>
                `${(value / 1000).toFixed(0)}k`
            }
          }
        }
      }
    });
  }

  const ctx2 =
    document.getElementById('chartProdDonut');

  if (ctx2) {
    destroyChart('productDonut');

    state.charts.productDonut = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Gross Revenue', 'Net Revenue', 'Discount', 'VAT'],
        datasets: [{
          data: [
            totalCaBrut,
            totalCaNet,
            totalDiscount,
            totalTva
          ],
          backgroundColor: [
            '#6366f1',
            '#8b5cf6',
            '#f43f5e',
            '#f59e0b'
          ],
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: tooltipStyle()
        },
        scales: {
          x: axisStyle(),
          y: {
            ...axisStyle(),
            ticks: {
              ...axisStyle().ticks,
              callback: value =>
                `${(value / 1000).toFixed(0)}k`
            }
          }
        }
      }
    });
  }

  showToast(`Analysis loaded: ${name}`, 'success');
}

async function loadMatplotlibChart() {
  const input =
    document.getElementById('mplSearch');

  const query =
    input?.value.trim() || '';

  if (!query) {
    showToast('Enter a product name or ID', 'error');
    return;
  }

  const container =
    document.getElementById('mplChartContainer');

  if (!container) return;

  container.innerHTML =
    '<p style="color:var(--text-secondary)">Generating chart?</p>';

  try {
    const res =
      await fetch(
        `/api/chart_product?name=${encodeURIComponent(query)}`
      );

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Unable to generate chart');
    }

    container.innerHTML = `
      <img
        src="${data.image_url}?t=${Date.now()}"
        alt="Detailed product revenue analysis"
        style="width:100%;max-width:1200px;border-radius:12px;"
      >
    `;
  } catch (error) {
    console.error('Product chart error:', error);

    container.innerHTML = '';

    showToast(
      error.message || 'Unable to generate chart',
      'error'
    );
  }
}

function debounce(fn, delay) {
  let timer;

  return (...args) => {
    clearTimeout(timer);

    timer = setTimeout(() => {
      fn(...args);
    }, delay);
  };
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  let container =
    document.getElementById('toastContainer');

  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';

    container.style.cssText = `
      position:fixed;
      right:20px;
      bottom:20px;
      z-index:9999;
    `;

    document.body.appendChild(container);
  }

  const toast = document.createElement('div');

  toast.style.cssText = `
    margin-top:8px;
    padding:12px 16px;
    border-radius:10px;
    background:#111827;
    color:#f8fafc;
    border:1px solid rgba(148,163,184,.2);
    box-shadow:0 10px 30px rgba(0,0,0,.25);
    font-size:.85rem;
  `;

  toast.textContent = message;

  if (type === 'error') {
    toast.style.borderColor = 'rgba(244,63,94,.5)';
  }

  if (type === 'success') {
    toast.style.borderColor = 'rgba(52,211,153,.5)';
  }

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3500);
}

document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');

  style.textContent =
    '.mono { font-family: var(--mono); font-size: .78rem; }';

  document.head.appendChild(style);
});
