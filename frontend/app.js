// ═══════════════════════════════════════════════════════════════════════════
// 🌊 Oota Aquamorphic Dashboard — Application Logic
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = window.location.origin;
const POLL_INTERVAL = 30000; // 30 seconds

// ── State ──────────────────────────────────────────────────────────────────
let chatHistory = [];
let isAgentTyping = false;

// ── Theme ──────────────────────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('oota-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('oota-theme', next);
}

// ── Clock ──────────────────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('header-clock');
  if (!el) return;
  const now = new Date();
  const opts = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
  el.textContent = now.toLocaleTimeString('en-IN', opts);
}

// ── API Helpers ────────────────────────────────────────────────────────────
async function fetchJSON(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`API fetch failed: ${path}`, e);
    return null;
  }
}

async function postJSON(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`API post failed: ${path}`, e);
    return null;
  }
}

// ══════════════════════════════════════════════════════════════════════════
// PANEL UPDATERS
// ══════════════════════════════════════════════════════════════════════════

// ── System Status ──────────────────────────────────────────────────────────
async function updateStatus() {
  const data = await fetchJSON('/api/dashboard/status');
  const container = document.getElementById('status-content');
  if (!data || !container) return;

  const statusBadge = document.getElementById('status-badge');
  if (statusBadge) {
    statusBadge.textContent = data.status === 'ok' ? '● Online' : '● Error';
    statusBadge.className = `card-badge ${data.status === 'ok' ? 'badge-ok' : 'badge-error'}`;
  }

  container.innerHTML = `
    <div class="status-grid">
      <div class="status-item">
        <div class="status-dot ${data.status === 'ok' ? 'online' : 'offline'}"></div>
        <div>
          <div class="status-label">API Server</div>
          <div class="status-value">${data.status === 'ok' ? 'Running' : 'Down'}</div>
        </div>
      </div>
      <div class="status-item">
        <div class="status-dot ${data.db_connected ? 'online' : 'offline'}"></div>
        <div>
          <div class="status-label">SQLite DB</div>
          <div class="status-value">${data.db_connected ? 'Connected' : 'Disconnected'}</div>
        </div>
      </div>
      <div class="status-item">
        <div class="status-dot ${data.chroma_connected ? 'online' : 'warning'}"></div>
        <div>
          <div class="status-label">ChromaDB</div>
          <div class="status-value">${data.chroma_connected ? 'Active' : 'Unavailable'}</div>
        </div>
      </div>
      <div class="status-item">
        <div class="status-dot ${data.telegram_configured ? 'online' : 'warning'}"></div>
        <div>
          <div class="status-label">Telegram</div>
          <div class="status-value">${data.telegram_configured ? 'Configured' : 'Not Set'}</div>
        </div>
      </div>
    </div>
    <div class="mt-sm" style="font-size:0.7rem;color:var(--text-muted);text-align:right;">
      🕐 ${new Date(data.timestamp).toLocaleTimeString('en-IN')} · ${data.cities_count || 0} cities · ${data.pois_count || 0} POIs
    </div>
  `;
}

// ── Agent Hierarchy ────────────────────────────────────────────────────────
async function updateAgents() {
  const data = await fetchJSON('/api/dashboard/agents');
  const container = document.getElementById('agents-content');
  if (!data || !container) return;

  const agentEmoji = { root: '🧠', travel_planner: '🗺️', expense_tracker: '💸', curation_agent: '📦' };

  let html = `
    <div class="agent-tree">
      <div class="agent-node root">
        <span class="agent-emoji">${agentEmoji.root}</span>
        <div class="agent-info">
          <div class="agent-name">${data.root.name}</div>
          <div class="agent-desc">${data.root.description}</div>
        </div>
        <span class="agent-status">Active</span>
      </div>
      <div class="sub-agents">
  `;

  for (const sub of data.sub_agents) {
    const emoji = agentEmoji[sub.name] || '🤖';
    html += `
      <div class="agent-node">
        <span class="agent-emoji">${emoji}</span>
        <div class="agent-info">
          <div class="agent-name">${sub.name}</div>
          <div class="agent-desc">${sub.description}</div>
        </div>
        <span class="agent-status">Ready</span>
      </div>
    `;
  }

  html += `</div></div>`;
  container.innerHTML = html;
}

// ── Tools Panel ────────────────────────────────────────────────────────────
async function updateTools() {
  const data = await fetchJSON('/api/dashboard/tools');
  const container = document.getElementById('tools-content');
  if (!data || !container) return;

  const toolEmojis = {
    'search_points_of_interest': '📍', 'get_area_info': '🏘️', 'find_midpoint_pois': '📐',
    'calculate_group_midpoint': '📐', 'estimate_auto_fare': '🛺', 'calculate_metro_ticket_fare': '🎫',
    'search_mall_shops': '🛍️', 'search_movies': '🎬', 'save_itinerary': '📝', 'get_active_itineraries': '📅',
    'get_transit_route': '🚇', 'search_events': '🎭', 'estimate_travel_time': '⏱️',
    'get_weather_forecast': '🌦️', 'get_weather_radar_warning': '🌧️', 'log_shared_expense': '💳',
    'get_expense_balances': '💰', 'get_budget_status': '📊', 'export_local_backup': '📦',
    'list_supported_cities': '🏙️', 'get_poi_details': '🔍', 'update_itinerary_status': '✏️',
    'get_transit_station_nearby': '🚉', 'search_local_documents': '📄', 'get_city_traffic_rules': '🚦',
    'save_preference': '❤️', 'recall_preferences': '🔮', 'calculate_departure_time': '🕐',
    'check_weather_recommendation': '☀️', 'execute_hybrid_routing': '🔀',
    'manage_vault_encryption': '🔐', 'run_document_indexer': '📑',
    'generate_dating_plan': '💕', 'collect_post_event_feedback': '⭐',
    'execute_travel_workflow': '🗂️',
  };

  let html = '<div class="tools-grid">';
  const allTools = [...(data.mcp_tools || []), ...(data.custom_tools || [])];

  for (const tool of allTools) {
    const emoji = toolEmojis[tool.name] || '🔧';
    const source = tool.source === 'mcp' ? 'MCP' : 'ADK';
    html += `
      <div class="tool-chip" title="${tool.description || tool.name}">
        <span class="tool-emoji">${emoji}</span>
        <span class="tool-name">${tool.name.replace(/_/g, ' ')}</span>
        <span class="tool-source">${source}</span>
      </div>
    `;
  }

  html += '</div>';
  container.innerHTML = html;
}

// ── History & Suggestions ──────────────────────────────────────────────────
async function updateHistory() {
  const data = await fetchJSON('/api/dashboard/history');
  const container = document.getElementById('history-content');
  if (!data || !container) return;

  if ((!data.itineraries || data.itineraries.length === 0) && (!data.memories || data.memories.length === 0)) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-emoji">📜</div>
        <p>No history yet. Start chatting to create itineraries!</p>
      </div>
    `;
    return;
  }

  let html = '<div class="timeline">';

  for (const it of (data.itineraries || [])) {
    html += `
      <div class="timeline-item">
        <span class="tl-emoji">${it.status === 'completed' ? '✅' : it.status === 'planned' ? '📅' : '⏳'}</span>
        <div class="tl-content">
          <div class="tl-title">${it.destination_name || 'Unknown Destination'}</div>
          <div class="tl-desc">${it.city_name || ''} · ${it.origin_area || ''}</div>
          <div class="tl-time">Status: ${it.status} · Meeting: ${it.meeting_time || '—'}</div>
        </div>
      </div>
    `;
  }

  for (const mem of (data.memories || [])) {
    html += `
      <div class="timeline-item">
        <span class="tl-emoji">🧠</span>
        <div class="tl-content">
          <div class="tl-title">${mem.category}</div>
          <div class="tl-desc">Accessed ${mem.access_count}x</div>
          <div class="tl-time">${mem.last_accessed || ''}</div>
        </div>
      </div>
    `;
  }

  html += '</div>';
  container.innerHTML = html;
}

// ── Weather Widget ─────────────────────────────────────────────────────────
async function updateWeather() {
  const data = await fetchJSON('/api/dashboard/weather');
  const container = document.getElementById('weather-content');
  if (!data || !container) return;

  if (!data.forecasts || data.forecasts.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-emoji">🌤️</div>
        <p>No weather data available</p>
      </div>
    `;
    return;
  }

  let html = '<div class="weather-cards">';

  for (const f of data.forecasts) {
    const wxEmoji = getWeatherEmoji(f.condition, f.precipitation_probability);
    const hourLabel = formatHour(f.hour_of_day);

    let badges = '';
    if (f.precipitation_probability > 50) {
      badges += `<span class="wx-badge rain">💧${f.precipitation_probability}%</span>`;
    }
    if (f.uv_index > 6) {
      badges += `<span class="wx-badge uv">UV ${f.uv_index}</span>`;
    }

    html += `
      <div class="weather-card">
        <div class="wx-emoji">${wxEmoji}</div>
        <div class="wx-temp">${Math.round(f.temp_celsius)}°</div>
        <div class="wx-condition">${f.condition}</div>
        <div class="wx-hour">${hourLabel}</div>
        <div class="wx-badges">${badges}</div>
      </div>
    `;
  }

  html += '</div>';
  html += `<div class="mt-sm" style="font-size:0.7rem;color:var(--text-muted);text-align:center;">📍 ${data.city_name || 'Default City'}</div>`;
  container.innerHTML = html;
}

function getWeatherEmoji(condition, precip) {
  const c = (condition || '').toLowerCase();
  if (c.includes('rain') || precip > 70) return '🌧️';
  if (c.includes('cloud') || c.includes('overcast')) return '☁️';
  if (c.includes('storm') || c.includes('thunder')) return '⛈️';
  if (c.includes('haze') || c.includes('fog') || c.includes('mist')) return '🌫️';
  if (c.includes('hot') || c.includes('sunny') || c.includes('clear')) return '☀️';
  if (precip > 40) return '🌦️';
  return '⛅';
}

function formatHour(h) {
  if (h === 0 || h === 24) return '12 AM';
  if (h === 12) return '12 PM';
  if (h < 12) return `${h} AM`;
  return `${h - 12} PM`;
}

// ── Expense Tracker ────────────────────────────────────────────────────────
async function updateExpenses() {
  const data = await fetchJSON('/api/dashboard/expenses');
  const container = document.getElementById('expenses-content');
  if (!data || !container) return;

  const budget = data.budget || {};
  const limit = budget.monthly_limit_rupees || 5000;
  const spent = budget.active_spent_rupees || 0;
  const remaining = limit - spent;
  const pct = Math.min((spent / limit) * 100, 100);

  let html = `
    <div class="budget-gauge">
      <div class="gauge-fill" style="width:${pct}%"></div>
    </div>
    <div class="budget-labels">
      <span>₹<span class="budget-spent">${spent.toLocaleString('en-IN')}</span> spent</span>
      <span>₹${remaining.toLocaleString('en-IN')} left of ₹${limit.toLocaleString('en-IN')}</span>
    </div>
  `;

  if (data.recent_expenses && data.recent_expenses.length > 0) {
    html += '<div class="expense-list">';
    for (const exp of data.recent_expenses) {
      html += `
        <div class="expense-item">
          <span class="exp-emoji">💳</span>
          <span class="exp-desc">${exp.description}</span>
          <span class="exp-amount">₹${exp.total_amount_rupees.toLocaleString('en-IN')}</span>
        </div>
      `;
    }
    html += '</div>';
  }

  if (data.balances && data.balances.length > 0) {
    html += `<div class="wave-divider mt-sm"></div>`;
    html += '<div class="mt-sm" style="font-size:0.75rem;font-weight:600;color:var(--text-secondary);">⚖️ Settlements</div>';
    html += '<div class="expense-list mt-sm">';
    for (const b of data.balances) {
      html += `
        <div class="expense-item">
          <span class="exp-emoji">⚖️</span>
          <span class="exp-desc">${b}</span>
          <span class="exp-amount"></span>
        </div>
      `;
    }
    html += '</div>';
  }

  container.innerHTML = html;
}

// ── Telegram Status ────────────────────────────────────────────────────────
async function updateTelegram() {
  const data = await fetchJSON('/api/dashboard/telegram');
  const container = document.getElementById('telegram-content');
  if (!data || !container) return;

  container.innerHTML = `
    <div class="telegram-info">
      <div class="tg-row">
        <span class="tg-label">Status</span>
        <span class="tg-value">${data.configured ? '🟢 Configured' : '🔴 Not Configured'}</span>
      </div>
      <div class="tg-row">
        <span class="tg-label">Bot Token</span>
        <span class="tg-value">${data.token_masked || '—'}</span>
      </div>
      <div class="tg-row">
        <span class="tg-label">Allowed IDs</span>
        <span class="tg-value">${data.allowed_users || 'All (dev mode)'}</span>
      </div>
      <div class="tg-row">
        <span class="tg-label">Mode</span>
        <span class="tg-value">${data.mode || 'Unknown'}</span>
      </div>
      <div class="tg-row">
        <span class="tg-label">Proactive</span>
        <span class="tg-value">${data.jobs_scheduled ? '✅ Departure · Feedback · Check-in' : '❌ None'}</span>
      </div>
    </div>
  `;
}

// ── Autonomous Decisions ───────────────────────────────────────────────────
function updateDecisions(newDecision) {
  const container = document.getElementById('decisions-content');
  if (!container) return;

  // On initial load show placeholder
  if (!newDecision && container.children.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-emoji">🧠</div>
        <p>Agent autonomous decisions will appear here as they happen</p>
      </div>
    `;
    return;
  }

  if (newDecision) {
    // Remove empty state if present
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'decision-item';
    item.innerHTML = `
      <span class="dec-emoji">${newDecision.emoji || '🧠'}</span>
      <div class="dec-content">
        <div class="dec-action">${newDecision.action}</div>
        <div class="dec-reason">${newDecision.reason}</div>
        <div class="dec-time">${new Date().toLocaleTimeString('en-IN')}</div>
      </div>
    `;
    container.prepend(item);

    // Keep max 20 entries
    while (container.children.length > 20) {
      container.removeChild(container.lastChild);
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════
// CHAT
// ══════════════════════════════════════════════════════════════════════════

function initChat() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');

  if (!input || !sendBtn) return;

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  // Welcome message
  addChatBubble('agent', '🍛 Namaste! I\'m Oota, your India Urban Concierge. Ask me about restaurants, routes, expenses, weather, or anything about your city! 🌊');
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const msg = (input.value || '').trim();
  if (!msg || isAgentTyping) return;

  // Add user bubble
  addChatBubble('user', msg);
  input.value = '';

  // Show typing
  isAgentTyping = true;
  sendBtn.disabled = true;
  showTyping(true);

  // Log decision
  updateDecisions({
    emoji: '💬',
    action: `User asked: "${msg.slice(0, 50)}${msg.length > 50 ? '…' : ''}"`,
    reason: 'Chat message routed to root agent via /api/dashboard/chat',
  });

  // Call API
  const data = await postJSON('/api/dashboard/chat', { message: msg });

  showTyping(false);
  isAgentTyping = false;
  sendBtn.disabled = false;

  if (data && data.response) {
    addChatBubble('agent', data.response);
    updateDecisions({
      emoji: '🤖',
      action: 'Agent responded',
      reason: `Response length: ${data.response.length} chars · Tools used: ${data.tools_used || 'unknown'}`,
    });
  } else {
    addChatBubble('agent', '😓 Sorry, I couldn\'t process that right now. Please try again.');
  }

  // Refresh panels after chat (agent may have changed data)
  setTimeout(() => {
    updateHistory();
    updateExpenses();
  }, 1000);
}

function addChatBubble(role, text) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  const label = role === 'user' ? '👤 You' : '🍛 Oota';
  bubble.innerHTML = `
    <div class="bubble-label">${label}</div>
    <div>${escapeHtml(text)}</div>
  `;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function showTyping(show) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const existing = container.querySelector('.typing-indicator');
  if (existing) existing.remove();

  if (show) {
    const el = document.createElement('div');
    el.className = 'typing-indicator';
    el.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ══════════════════════════════════════════════════════════════════════════

async function refreshAll() {
  await Promise.allSettled([
    updateStatus(),
    updateAgents(),
    updateTools(),
    updateHistory(),
    updateWeather(),
    updateExpenses(),
    updateTelegram(),
  ]);
  updateDecisions(null); // Initialize empty state if needed
}

function init() {
  initTheme();
  initChat();
  updateClock();
  setInterval(updateClock, 1000);

  // Initial load
  refreshAll();

  // Auto-refresh every 30s
  setInterval(refreshAll, POLL_INTERVAL);

  // Theme toggle
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  // Refresh button
  const refreshBtn = document.getElementById('refresh-all');
  if (refreshBtn) refreshBtn.addEventListener('click', refreshAll);

  // Log startup decision
  setTimeout(() => {
    updateDecisions({
      emoji: '🚀',
      action: 'Dashboard initialized',
      reason: 'Connected to backend API. Auto-refresh every 30s enabled.',
    });
  }, 500);
}

// Wait for DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
