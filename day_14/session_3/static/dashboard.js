/**
 * Agentic Observability Hub - Client-Side Analytics & Canvas Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

let cachedTraces = [];
let cachedTimeSeries = [];

async function initDashboard() {
  setupEventListeners();
  await refreshData();
}

function setupEventListeners() {
  const refreshBtn = document.getElementById('refreshBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => refreshData());
  }

  const searchInput = document.getElementById('traceSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', () => filterTracesTable());
  }

  const categoryFilter = document.getElementById('categoryFilter');
  if (categoryFilter) {
    categoryFilter.addEventListener('change', () => filterTracesTable());
  }

  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const traceModal = document.getElementById('traceModal');
  if (modalCloseBtn && traceModal) {
    modalCloseBtn.addEventListener('click', () => {
      traceModal.classList.add('hidden');
    });
    traceModal.addEventListener('click', (e) => {
      if (e.target === traceModal) {
        traceModal.classList.add('hidden');
      }
    });
  }
}

async function refreshData() {
  try {
    await Promise.all([
      loadMetricSummary(),
      loadAlerts(),
      loadTimeSeries(),
      loadTracesTable()
    ]);
  } catch (err) {
    console.error('Error fetching dashboard telemetry:', err);
  }
}

async function loadMetricSummary() {
  const res = await fetch('/api/summary');
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpiPassRate').textContent = `${data.overall_pass_rate}%`;
  document.getElementById('kpiTracesCount').textContent = `${data.total_traces} total traces`;

  const passBadge = document.getElementById('passRateBadge');
  if (data.overall_pass_rate >= 95.0) {
    passBadge.className = 'sla-badge';
    passBadge.textContent = 'SLA ≥ 95% MET';
  } else {
    passBadge.className = 'badge-status';
    passBadge.style.background = 'rgba(244, 63, 94, 0.2)';
    passBadge.style.color = '#f43f5e';
    passBadge.textContent = 'SLA BREACH';
  }

  document.getElementById('kpiP95Latency').textContent = `${data.p95_latency_ms}ms`;
  document.getElementById('kpiLatencyPercentiles').textContent = `p50: ${data.p50_latency_ms}ms • p90: ${data.p90_latency_ms}ms`;

  document.getElementById('kpiTotalCost').textContent = `$${data.total_cost_usd.toFixed(2)}`;
  document.getElementById('kpiAvgCost').textContent = `Avg: $${data.avg_cost_per_trace_usd.toFixed(4)} / query`;

  document.getElementById('kpiGroundedness').textContent = data.avg_groundedness.toFixed(3);
  document.getElementById('kpiHallucinationRate').textContent = `Hallucinations: ${data.hallucination_rate}%`;

  document.getElementById('kpiCSAT').textContent = `${data.positive_feedback_ratio}%`;

  const decayStatusEl = document.getElementById('kpiDecayStatus');
  const decayBadgeEl = document.getElementById('decayBadge');
  if (data.silent_decay_detected) {
    decayStatusEl.textContent = 'DECAY DETECTED';
    decayStatusEl.style.color = '#f43f5e';
    decayBadgeEl.textContent = 'ACTION REQUIRED';
    decayBadgeEl.style.background = 'rgba(244, 63, 94, 0.2)';
    decayBadgeEl.style.color = '#f43f5e';
  } else {
    decayStatusEl.textContent = 'HEALTHY';
    decayStatusEl.style.color = '#10b981';
    decayBadgeEl.textContent = 'NORMAL DRIFT';
    decayBadgeEl.style.background = 'rgba(16, 185, 129, 0.15)';
    decayBadgeEl.style.color = '#10b981';
  }
}

async function loadAlerts() {
  const container = document.getElementById('alertsContainer');
  const res = await fetch('/api/alerts?active_only=true');
  if (!res.ok) return;
  const alerts = await res.json();

  container.innerHTML = '';
  if (alerts.length === 0) return;

  alerts.forEach(alert => {
    const banner = document.createElement('div');
    const isCrit = alert.severity === 'CRITICAL';
    banner.className = `alert-banner ${isCrit ? 'critical' : 'warning'}`;
    banner.innerHTML = `
      <div class="alert-left">
        <span class="alert-badge">${alert.severity}</span>
        <span class="alert-message">${escapeHtml(alert.message)}</span>
      </div>
      <button class="btn-ack" onclick="acknowledgeAlert('${alert.alert_id}')">Acknowledge</button>
    `;
    container.appendChild(banner);
  });
}

window.acknowledgeAlert = async function(alertId) {
  try {
    const res = await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
    if (res.ok) {
      await loadAlerts();
    }
  } catch (err) {
    console.error('Failed to acknowledge alert:', err);
  }
};

async function loadTimeSeries() {
  const res = await fetch('/api/timeseries');
  if (!res.ok) return;
  cachedTimeSeries = await res.json();

  renderPassRateChart(cachedTimeSeries);
  renderLatencyChart(cachedTimeSeries);
  renderCostChart(cachedTimeSeries);
  renderFailureChart(cachedTimeSeries);
}

// ============================================================================
// Canvas Visualizations
// ============================================================================

function renderPassRateChart(series) {
  const canvas = document.getElementById('passRateCanvas');
  if (!canvas || series.length === 0) return;
  const ctx = canvas.getContext('2d');
  setupCanvasDPI(canvas, ctx);

  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 45;
  const padBottom = 30;
  const padTop = 20;
  const padRight = 20;

  const chartW = W - padLeft - padRight;
  const chartH = H - padTop - padBottom;

  const minVal = 60.0;
  const maxVal = 100.0;

  drawGridAndAxes(ctx, padLeft, padTop, chartW, chartH, ['60%', '70%', '80%', '90%', '100%']);

  // Draw 95% SLA Target Line (Dashed Rose)
  const slaY = padTop + chartH - ((95.0 - minVal) / (maxVal - minVal)) * chartH;
  ctx.save();
  ctx.strokeStyle = '#f43f5e';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(padLeft, slaY);
  ctx.lineTo(padLeft + chartW, slaY);
  ctx.stroke();
  ctx.restore();

  // Draw Pass Rate Line
  const stepX = chartW / (series.length - 1);
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 2.5;
  ctx.beginPath();

  series.forEach((d, idx) => {
    const x = padLeft + idx * stepX;
    const y = padTop + chartH - ((d.pass_rate - minVal) / (maxVal - minVal)) * chartH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw Points and Date Labels
  series.forEach((d, idx) => {
    const x = padLeft + idx * stepX;
    const y = padTop + chartH - ((d.pass_rate - minVal) / (maxVal - minVal)) * chartH;

    ctx.fillStyle = d.pass_rate >= 95.0 ? '#10b981' : '#f43f5e';
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    // Day label on bottom
    if (idx % 2 === 0 || idx === series.length - 1) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      const label = d.timestamp_bucket.slice(5); // MM-DD
      ctx.fillText(label, x, H - 10);
    }
  });
}

function renderLatencyChart(series) {
  const canvas = document.getElementById('latencyCanvas');
  if (!canvas || series.length === 0) return;
  const ctx = canvas.getContext('2d');
  setupCanvasDPI(canvas, ctx);

  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 45;
  const padBottom = 30;
  const padTop = 20;
  const padRight = 20;

  const chartW = W - padLeft - padRight;
  const chartH = H - padTop - padBottom;

  const maxVal = 3000.0;
  const minVal = 0.0;

  drawGridAndAxes(ctx, padLeft, padTop, chartW, chartH, ['0', '750', '1500', '2250', '3000ms']);

  const stepX = chartW / (series.length - 1);

  // Helper for drawing latency line
  const drawLine = (prop, color) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    series.forEach((d, idx) => {
      const x = padLeft + idx * stepX;
      const y = padTop + chartH - (d[prop] / maxVal) * chartH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  };

  drawLine('p50_latency_ms', '#00f0ff');
  drawLine('p90_latency_ms', '#8b5cf6');
  drawLine('p95_latency_ms', '#f43f5e');

  // Bottom date labels
  series.forEach((d, idx) => {
    if (idx % 2 === 0 || idx === series.length - 1) {
      const x = padLeft + idx * stepX;
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.timestamp_bucket.slice(5), x, H - 10);
    }
  });
}

function renderCostChart(series) {
  const canvas = document.getElementById('costCanvas');
  if (!canvas || series.length === 0) return;
  const ctx = canvas.getContext('2d');
  setupCanvasDPI(canvas, ctx);

  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 45;
  const padBottom = 30;
  const padTop = 20;
  const padRight = 20;

  const chartW = W - padLeft - padRight;
  const chartH = H - padTop - padBottom;

  const maxCost = Math.max(...series.map(d => d.total_cost_usd), 2.5);

  drawGridAndAxes(ctx, padLeft, padTop, chartW, chartH, ['$0', `$${(maxCost * 0.33).toFixed(1)}`, `$${(maxCost * 0.66).toFixed(1)}`, `$${maxCost.toFixed(1)}`]);

  const barWidth = (chartW / series.length) * 0.6;
  const slotW = chartW / series.length;

  series.forEach((d, idx) => {
    const x = padLeft + idx * slotW + (slotW - barWidth) / 2;
    const barH = (d.total_cost_usd / maxCost) * chartH;
    const y = padTop + chartH - barH;

    const grad = ctx.createLinearGradient(0, y, 0, padTop + chartH);
    grad.addColorStop(0, '#f59e0b');
    grad.addColorStop(1, 'rgba(245, 158, 11, 0.15)');

    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barWidth, barH);

    if (idx % 2 === 0 || idx === series.length - 1) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.timestamp_bucket.slice(5), x + barWidth / 2, H - 10);
    }
  });
}

function renderFailureChart(series) {
  const canvas = document.getElementById('failureCanvas');
  if (!canvas || series.length === 0) return;
  const ctx = canvas.getContext('2d');
  setupCanvasDPI(canvas, ctx);

  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 40;
  const padBottom = 30;
  const padTop = 20;
  const padRight = 20;

  const chartW = W - padLeft - padRight;
  const chartH = H - padTop - padBottom;

  const maxFails = Math.max(...series.map(d => d.failed_traces), 25);

  drawGridAndAxes(ctx, padLeft, padTop, chartW, chartH, ['0', `${Math.round(maxFails * 0.5)}`, `${maxFails}`]);

  const stepX = chartW / (series.length - 1);

  // Draw lines for individual categories
  const categories = [
    { key: 'TIMEOUT', color: '#f43f5e' },
    { key: 'TOOL_FAILURE', color: '#f59e0b' },
    { key: 'HALLUCINATION', color: '#8b5cf6' },
    { key: 'RATE_LIMIT_ERROR', color: '#00f0ff' }
  ];

  categories.forEach(cat => {
    ctx.strokeStyle = cat.color;
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    series.forEach((d, idx) => {
      const count = d.failure_category_counts[cat.key] || 0;
      const x = padLeft + idx * stepX;
      const y = padTop + chartH - (count / maxFails) * chartH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });

  series.forEach((d, idx) => {
    if (idx % 2 === 0 || idx === series.length - 1) {
      const x = padLeft + idx * stepX;
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.timestamp_bucket.slice(5), x, H - 10);
    }
  });
}

function drawGridAndAxes(ctx, padLeft, padTop, chartW, chartH, yLabels) {
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;

  // Horizontal Grid Lines
  const steps = yLabels.length - 1;
  for (let i = 0; i <= steps; i++) {
    const y = padTop + (chartH / steps) * i;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(padLeft + chartW, y);
    ctx.stroke();

    ctx.fillStyle = '#64748b';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    const label = yLabels[steps - i];
    ctx.fillText(label, padLeft - 6, y + 3);
  }
}

function setupCanvasDPI(canvas, ctx) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
}

// ============================================================================
// Trace Explorer & Inspection Drawer
// ============================================================================

async function loadTracesTable() {
  const res = await fetch('/api/traces?limit=60');
  if (!res.ok) return;
  cachedTraces = await res.json();
  renderTracesTable(cachedTraces);
}

function filterTracesTable() {
  const query = (document.getElementById('traceSearchInput').value || '').toLowerCase();
  const cat = document.getElementById('categoryFilter').value;

  const filtered = cachedTraces.filter(t => {
    const matchesCat = (cat === 'ALL') || (t.failure_category === cat);
    const matchesQuery = !query || t.query.toLowerCase().includes(query) || t.trace_id.toLowerCase().includes(query);
    return matchesCat && matchesQuery;
  });

  renderTracesTable(filtered);
}

function renderTracesTable(traces) {
  const tbody = document.getElementById('traceTableBody');
  tbody.innerHTML = '';

  if (traces.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: #64748b; padding: 24px;">No traces match filter criteria.</td></tr>`;
    return;
  }

  traces.forEach(t => {
    const tr = document.createElement('tr');
    const isSuccess = t.status === 'SUCCESS';
    const hasFailCat = t.failure_category && t.failure_category !== 'NONE';

    tr.innerHTML = `
      <td class="trace-id-cell">${t.trace_id}</td>
      <td style="color: #64748b;">${formatDate(t.timestamp)}</td>
      <td class="query-cell" title="${escapeHtml(t.query)}">${escapeHtml(t.query)}</td>
      <td><span class="category-pill">${t.model_used}</span></td>
      <td style="font-family: monospace;">${t.latency_ms.toFixed(1)}ms</td>
      <td style="font-family: monospace;">$${t.cost_usd.toFixed(4)}</td>
      <td><span class="status-badge ${isSuccess ? 'success' : 'failure'}">${t.status}</span></td>
      <td><span style="font-family: monospace; color: ${t.groundedness.score >= 0.85 ? '#10b981' : '#f43f5e'};">${t.groundedness.score.toFixed(2)}</span></td>
      <td><span class="category-pill ${hasFailCat ? 'error' : ''}">${t.failure_category}</span></td>
      <td><button class="btn-inspect" onclick="inspectTrace('${t.trace_id}')">Inspect</button></td>
    `;
    tbody.appendChild(tr);
  });
}

window.inspectTrace = async function(traceId) {
  try {
    const res = await fetch(`/api/traces/${traceId}`);
    if (!res.ok) return;
    const trace = await res.json();

    document.getElementById('modalTraceId').textContent = trace.trace_id;
    const statusEl = document.getElementById('modalTraceStatus');
    statusEl.textContent = trace.status;
    statusEl.className = `status-badge ${trace.status === 'SUCCESS' ? 'success' : 'failure'}`;

    document.getElementById('modalQueryText').textContent = trace.query;
    document.getElementById('modalResponseText').textContent = trace.response || 'No response returned.';

    document.getElementById('modalLatency').textContent = `${trace.latency_ms.toFixed(1)}ms`;
    document.getElementById('modalCost').textContent = `$${trace.cost_usd.toFixed(5)}`;
    document.getElementById('modalPromptTokens').textContent = trace.prompt_tokens;
    document.getElementById('modalComplTokens').textContent = trace.completion_tokens;
    document.getElementById('modalGroundedness').textContent = `${trace.groundedness.score.toFixed(2)} (${trace.groundedness.rationale})`;

    // Render Spans Hierarchy
    const spanTreeContainer = document.getElementById('modalSpanTree');
    spanTreeContainer.innerHTML = '';
    if (trace.spans && trace.spans.length > 0) {
      trace.spans.forEach(span => {
        const node = document.createElement('div');
        node.className = 'span-node';
        node.innerHTML = `
          <div>
            <div class="span-name">${escapeHtml(span.name)}</div>
            <div style="font-size: 10px; color: #64748b;">${span.span_type} • ${span.status}</div>
          </div>
          <div class="span-meta">${span.latency_ms.toFixed(1)}ms</div>
        `;
        spanTreeContainer.appendChild(node);
      });
    } else {
      spanTreeContainer.innerHTML = '<div style="color: #64748b;">No sub-spans recorded.</div>';
    }

    // Feedback
    const fbBox = document.getElementById('modalFeedbackBox');
    if (trace.feedback) {
      fbBox.innerHTML = `
        <strong>User Feedback:</strong> ${trace.feedback.thumbs_up ? '👍 Thumbs Up' : '👎 Thumbs Down'} (${trace.feedback.rating}/5 stars)<br>
        <em>"${escapeHtml(trace.feedback.comment || 'No comment provided')}"</em><br>
        <span style="font-size: 11px; color: #64748b;">Escalated to HITL: ${trace.feedback.user_escalated_to_hitl ? 'Yes' : 'No'}</span>
      `;
    } else {
      fbBox.innerHTML = 'No user feedback recorded for this trace.';
    }

    document.getElementById('traceModal').classList.remove('hidden');
  } catch (err) {
    console.error('Failed to inspect trace:', err);
  }
};

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  })[m]);
}
