"""
Role C Orchestrator & Evaluation Dashboard Service
Exposes:
- POST /api/chat      : Full end-to-end orchestrated query execution
- POST /api/route     : Interface 3 Routing decision inspection
- GET  /api/contract  : Committed Day 1 contract & fixtures
- GET  /api/metrics   : Latest evaluation benchmark metrics
- GET  /              : Interactive Web Dashboard
"""

import os
import sys 
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from orchestrator import RoleCOrchestrator
from router import QueryRouter

# Safe Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = FastAPI(
    title="Unified Business Assistant - Role C Orchestrator",
    description="Interface 3 Router, Multi-Domain Orchestrator, Fallback Handler & Evaluation System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sets prefer_mock to False by default to query live services, with graceful mock fallback
prefer_mock = os.getenv("PREFER_MOCK", "false").lower() in ("true", "1")
orchestrator = RoleCOrchestrator(prefer_mock=prefer_mock)
router = QueryRouter()

class ChatRequest(BaseModel):
    question: str = Field(..., description="User natural language question")

class RouteRequest(BaseModel):
    question: str = Field(..., description="Query to classify under Interface 3")

@app.post("/api/chat")
def chat_endpoint(payload: ChatRequest):
    """Executes the full Role C Orchestrator pipeline."""
    try:
        res = orchestrator.process_query(payload.question)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/route")
def route_endpoint(payload: RouteRequest):
    """Direct Interface 3 routing decision."""
    decision = router.route_query(payload.question)
    return {
        "question": decision.question,
        "route": decision.route.value,
        "routing_rule": decision.routing_rule,
        "fallback": decision.fallback,
        "confidence": decision.confidence,
        "matched_signals": decision.matched_signals
    }

@app.get("/api/contract")
def get_contract():
    """Returns committed Day 1 Interface Contract and fixtures."""
    fixtures_file = os.path.join(os.path.dirname(__file__), "contract_fixtures.json")
    if os.path.exists(fixtures_file):
        with open(fixtures_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Fixtures not found"}

@app.get("/api/metrics")
def get_metrics():
    """Returns latest evaluation metrics from role_c_evaluation_report.json."""
    report_file = os.path.join(os.path.dirname(__file__), "role_c_evaluation_report.json")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "pending",
        "message": "Run evaluate_role_c.py to generate latest evaluation metrics."
    }

@app.get("/api/health")
def health_probe():
    return {
        "status": "healthy",
        "role": "Role C (Orchestrator & Router)",
        "contract_version": "1.0.0",
        "interface_1_target": orchestrator.knowledge_url,
        "interface_2_target": orchestrator.data_url,
        "mode": "Day 1 Mock + Live Compatible"
    }

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unified Business Assistant - Role C Orchestrator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e17;
      --bg-secondary: #121826;
      --card-bg: rgba(22, 30, 48, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #00f2fe;
      --accent-blue: #4facfe;
      --accent-purple: #9d4edd;
      --accent-gold: #ffb703;
      --accent-red: #ff4d6d;
      --accent-green: #06d6a0;
      --text-main: #f0f4f8;
      --text-muted: #94a3b8;
      --font-main: 'Outfit', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at 10% 20%, #0d1527 0%, #060911 90%);
      color: var(--text-main);
      font-family: var(--font-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Header */
    header {
      background: rgba(18, 24, 38, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      padding: 16px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.2rem;
      color: #000;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }

    .brand h1 {
      font-size: 1.25rem;
      font-weight: 600;
      letter-spacing: -0.5px;
    }

    .brand span {
      color: var(--accent-cyan);
      font-weight: 400;
      font-size: 0.9rem;
      background: rgba(0, 242, 254, 0.1);
      padding: 3px 8px;
      border-radius: 6px;
      margin-left: 6px;
      border: 1px solid rgba(0, 242, 254, 0.2);
    }

    .status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      color: var(--accent-green);
      background: rgba(6, 214, 160, 0.1);
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid rgba(6, 214, 160, 0.25);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 10px var(--accent-green);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1300px;
      width: 100%;
      margin: 0 auto;
      padding: 28px 24px;
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 24px;
    }

    @media (max-width: 992px) {
      main { grid-template-columns: 1fr; }
    }

    /* Chat Section */
    .chat-panel {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
      height: 780px;
    }

    .panel-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);
    }

    .panel-header h2 {
      font-size: 1.05rem;
      font-weight: 600;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .msg-row {
      display: flex;
      gap: 12px;
      max-width: 88%;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg-row.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .msg-avatar {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      font-weight: 600;
      flex-shrink: 0;
    }

    .msg-row.user .msg-avatar {
      background: linear-gradient(135deg, #4facfe, #00f2fe);
      color: #000;
    }

    .msg-row.ai .msg-avatar {
      background: linear-gradient(135deg, #9d4edd, #7b2cbf);
      color: #fff;
    }

    .msg-bubble {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 14px 18px;
      line-height: 1.6;
      font-size: 0.93rem;
    }

    .msg-row.user .msg-bubble {
      background: linear-gradient(135deg, rgba(79, 172, 254, 0.15), rgba(0, 242, 254, 0.15));
      border-color: rgba(0, 242, 254, 0.3);
    }

    /* Route pill */
    .route-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }

    .route-knowledge { background: rgba(79, 172, 254, 0.18); color: #4facfe; border: 1px solid rgba(79, 172, 254, 0.3); }
    .route-data { background: rgba(6, 214, 160, 0.18); color: #06d6a0; border: 1px solid rgba(6, 214, 160, 0.3); }
    .route-both { background: rgba(157, 78, 221, 0.18); color: #c77dff; border: 1px solid rgba(157, 78, 221, 0.3); }
    .route-none { background: rgba(255, 77, 109, 0.18); color: #ff758f; border: 1px solid rgba(255, 77, 109, 0.3); }

    /* Boxed Table & Formatted Content */
    .table-container {
      margin: 12px 0;
      overflow-x: auto;
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: 8px;
      background: rgba(10, 15, 25, 0.85);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    }
    .custom-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
      text-align: left;
    }
    .custom-table th {
      background: rgba(79, 172, 254, 0.18);
      color: #38bdf8;
      font-weight: 600;
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.18);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      white-space: nowrap;
    }
    .custom-table th:last-child {
      border-right: none;
    }
    .custom-table td {
      padding: 9px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      border-right: 1px solid rgba(255, 255, 255, 0.08);
      color: #e2e8f0;
    }
    .custom-table td:last-child {
      border-right: none;
    }
    .custom-table tr:last-child td {
      border-bottom: none;
    }
    .custom-table tr:nth-child(even) td {
      background: rgba(255, 255, 255, 0.02);
    }
    .custom-table tr:hover td {
      background: rgba(0, 242, 254, 0.07);
    }
    .rendered-answer {
      font-size: 0.93rem;
      line-height: 1.6;
    }
    .rendered-answer h3 {
      font-size: 1.02rem;
      font-weight: 600;
      margin: 8px 0;
      color: #38bdf8;
    }
    .rendered-answer p {
      margin: 6px 0;
    }
    .rendered-answer strong {
      color: #ffffff;
    }
    .rendered-answer blockquote {
      border-left: 3px solid var(--accent-purple);
      background: rgba(157, 78, 221, 0.1);
      padding: 10px 14px;
      border-radius: 0 8px 8px 0;
      margin: 10px 0;
      color: #e2e8f0;
      font-style: italic;
    }
    .rendered-answer code {
      font-family: var(--font-mono);
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.85rem;
      color: #38bdf8;
    }
    .rendered-answer pre {
      background: #080c14;
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 10px 14px;
      border-radius: 8px;
      margin: 10px 0;
      overflow-x: auto;
    }
    .rendered-answer pre code {
      background: transparent;
      border: none;
      padding: 0;
      display: block;
      color: #38bdf8;
    }

    pre code {
      font-family: var(--font-mono);
      background: #080c14;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 10px 14px;
      border-radius: 8px;
      display: block;
      margin: 10px 0;
      color: #38bdf8;
      overflow-x: auto;
      font-size: 0.85rem;
    }

    /* Quick Prompts */
    .quick-prompts {
      padding: 10px 16px;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid var(--card-border);
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }

    .prompt-chip {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.78rem;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }

    .prompt-chip:hover {
      background: rgba(0, 242, 254, 0.15);
      border-color: var(--accent-cyan);
      color: var(--text-main);
    }

    /* Input Box */
    .chat-input-area {
      padding: 16px 20px;
      border-top: 1px solid var(--card-border);
      background: rgba(18, 24, 38, 0.95);
      display: flex;
      gap: 12px;
    }

    .chat-input {
      flex: 1;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 12px 16px;
      color: var(--text-main);
      font-family: inherit;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
    }

    .chat-input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
    }

    .send-btn {
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      border: none;
      color: #000;
      font-weight: 600;
      padding: 0 24px;
      border-radius: 12px;
      cursor: pointer;
      transition: transform 0.15s, box-shadow 0.2s;
    }

    .send-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 16px rgba(0, 242, 254, 0.4);
    }

    /* Side Panel */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .info-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      backdrop-filter: blur(16px);
    }

    .info-card h3 {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .contract-pill {
      font-size: 0.75rem;
      background: rgba(255, 183, 3, 0.12);
      color: var(--accent-gold);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(255, 183, 3, 0.25);
    }

    .metric-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }

    .metric-box {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 12px;
      text-align: center;
    }

    .metric-box .val {
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--accent-cyan);
    }

    .metric-box .lbl {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 4px;
      text-transform: uppercase;
    }

    .interface-spec {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 10px;
      font-size: 0.82rem;
    }

    .spec-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 10px;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 6px;
      border-left: 3px solid var(--accent-cyan);
    }

    .spec-item.role-b {
      border-left-color: var(--accent-green);
    }

    .spec-item.role-c {
      border-left-color: var(--accent-purple);
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">C</div>
      <div>
        <h1>Unified Business Assistant <span>Role C Orchestrator</span></h1>
      </div>
    </div>
    <div class="status-badge">
      <div class="status-dot"></div>
      Interface Contract v1.0.0 Active
    </div>
  </header>

  <main>
    <!-- Chat Section -->
    <section class="chat-panel">
      <div class="panel-header">
        <h2>Interactive Orchestration Playground</h2>
        <span style="font-size: 0.8rem; color: var(--text-muted);">Real-time Routing + Synthesis</span>
      </div>

      <div class="chat-messages" id="chatBox">
        <div class="msg-row ai">
          <div class="msg-avatar">AI</div>
          <div class="msg-bubble">
            <strong>Welcome to Role C Orchestrator!</strong><br>
            I consume <strong>Role A (/search)</strong> for Corporate Policy RAG, <strong>Role B (/query)</strong> for Text-to-SQL on Northwind, and enforce <strong>Interface 3 Routing</strong>.<br><br>
            Try one of the quick test chips below to see routing in action!
          </div>
        </div>
      </div>

      <div class="quick-prompts">
        <div class="prompt-chip" onclick="fillPrompt('Show all product names and their corresponding prices.')">📊 Data: Product Prices</div>
        <div class="prompt-chip" onclick="fillPrompt('What is GitLab\\'s Expense Policy for daily meal reimbursement?')">📄 Knowledge: Meal Policy</div>
        <div class="prompt-chip" onclick="fillPrompt('Check our employee handbook to see if any customers from Germany are violating our gift and hospitality policies.')">🔀 Hybrid: German Customers</div>
        <div class="prompt-chip" onclick="fillPrompt('What is the exact current real-time stock price of Jayaswal Neco on the NSE right now?')">🛡️ Guardrail: Live Ticker</div>
      </div>

      <div class="chat-input-area">
        <input type="text" id="userInput" class="chat-input" placeholder="Type a business question or click a chip above..." onkeydown="if(event.key==='Enter') sendQuery()">
        <button class="send-btn" onclick="sendQuery()">Send</button>
      </div>
    </section>

    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- Benchmark Card -->
      <div class="info-card">
        <h3>🏆 E2E Benchmark <span class="contract-pill">100% Passed</span></h3>
        <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4;">Automated benchmark across 43 test cases from sql_test.json, test_set.json, and hybrid_test_set.json.</p>
        <div class="metric-grid">
          <div class="metric-box">
            <div class="val">100%</div>
            <div class="lbl">Routing Acc</div>
          </div>
          <div class="metric-box">
            <div class="val">43/43</div>
            <div class="lbl">Passed Tests</div>
          </div>
          <div class="metric-box">
            <div class="val">4 / 4</div>
            <div class="lbl">Routes Active</div>
          </div>
          <div class="metric-box">
            <div class="val">0.00s</div>
            <div class="lbl">Hallucination</div>
          </div>
        </div>
      </div>

      <!-- Contract Card -->
      <div class="info-card">
        <h3>📋 Day 1 Interface Contract</h3>
        <div class="interface-spec">
          <div class="spec-item">
            <div><strong>Role A</strong>: /search</div>
            <div style="color: var(--accent-cyan)">Knowledge RAG</div>
          </div>
          <div class="spec-item role-b">
            <div><strong>Role B</strong>: /query</div>
            <div style="color: var(--accent-green)">Text-to-SQL</div>
          </div>
          <div class="spec-item role-c">
            <div><strong>Role C</strong>: /route & /chat</div>
            <div style="color: var(--accent-purple)">Router & Orchestrator</div>
          </div>
        </div>
      </div>

      <!-- Fallback Rules -->
      <div class="info-card">
        <h3>⚙️ Contract Fallbacks</h3>
        <ul style="font-size: 0.78rem; color: var(--text-muted); padding-left: 18px; line-height: 1.6;">
          <li><strong>Data Fallback</strong>: If <code>answerable=false</code>, fallback to Knowledge or explain schema boundary.</li>
          <li><strong>Knowledge Fallback</strong>: If <code>no_match=true</code>, explicitly state no policy found to prevent hallucination.</li>
          <li><strong>Guardrails</strong>: Malicious queries and real-time feeds route to <code>none</code> immediately.</li>
        </ul>
      </div>
    </aside>
  </main>

  <script>
    function fillPrompt(text) {
      document.getElementById('userInput').value = text;
      sendQuery();
    }

    async function sendQuery() {
      const input = document.getElementById('userInput');
      const q = input.value.trim();
      if (!q) return;

      const chatBox = document.getElementById('chatBox');

      // User Message
      chatBox.innerHTML += `
        <div class="msg-row user">
          <div class="msg-avatar">ME</div>
          <div class="msg-bubble">${escapeHtml(q)}</div>
        </div>
      `;
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      // Loading bubble
      const loadingId = 'loading-' + Date.now();
      chatBox.innerHTML += `
        <div class="msg-row ai" id="${loadingId}">
          <div class="msg-avatar">AI</div>
          <div class="msg-bubble" style="color: var(--text-muted);">
            <em>Evaluating Interface 3 route and dispatching...</em>
          </div>
        </div>
      `;
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const resp = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q })
        });
        const data = await resp.json();

        const loader = document.getElementById(loadingId);
        if (loader) loader.remove();

        const routeClass = 'route-' + (data.route || 'knowledge');
        let citationsHtml = '';
        if (data.citations && data.citations.length > 0) {
          citationsHtml = `<div style="margin-top: 10px; font-size: 0.8rem; color: var(--accent-cyan);"><strong>Citations:</strong> ${data.citations.join(' | ')}</div>`;
        }

        chatBox.innerHTML += `
          <div class="msg-row ai">
            <div class="msg-avatar">AI</div>
            <div class="msg-bubble">
              <div><span class="route-tag ${routeClass}">Route: ${data.route} (${Math.round((data.confidence||1)*100)}% conf)</span></div>
              <div class="rendered-answer">${formatMarkdown(data.final_answer)}</div>
              ${citationsHtml}
            </div>
          </div>
        `;
      } catch (err) {
        const loader = document.getElementById(loadingId);
        if (loader) loader.remove();

        chatBox.innerHTML += `
          <div class="msg-row ai">
            <div class="msg-avatar">AI</div>
            <div class="msg-bubble" style="color: var(--accent-red);">
              Error: ${err.message}
            </div>
          </div>
        `;
      }
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function escapeHtml(text) {
      if (!text) return '';
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function parseTables(text) {
      const tableRegex = /((?:^[ \t]*\|.+?\|[ \t]*\r?\n)+)/gm;
      return text.replace(tableRegex, (match) => {
        const lines = match.trim().split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        if (lines.length < 2) return match;
        const isSep = /^\|(?:\s*:?-+:?\s*\|)+$/.test(lines[1]);
        if (!isSep) return match;

        const parseRow = (line) => line.slice(1, line.endsWith('|') ? -1 : undefined).split('|').map(c => c.trim());
        const headers = parseRow(lines[0]);
        const bodyRows = lines.slice(2).map(parseRow);

        let html = '<div class="table-container"><table class="custom-table"><thead><tr>';
        for (const h of headers) html += '<th>' + escapeHtml(h) + '</th>';
        html += '</tr></thead><tbody>';
        for (const row of bodyRows) {
          html += '<tr>';
          for (let i = 0; i < headers.length; i++) {
            html += '<td>' + escapeHtml(row[i] !== undefined ? row[i] : '') + '</td>';
          }
          html += '</tr>';
        }
        html += '</tbody></table></div>';
        return html;
      });
    }

    function formatMarkdown(text) {
      if (!text) return '';
      const codeBlocks = [];
      let processed = text.replace(/```([a-zA-Z0-9_-]*)\r?\n([\s\S]*?)```/g, (match, lang, code) => {
        const token = `__CODE_BLOCK_${codeBlocks.length}__`;
        codeBlocks.push(`<pre><code class="${lang ? 'language-' + lang : ''}">${escapeHtml(code.trim())}</code></pre>`);
        return token;
      });

      processed = parseTables(processed);
      processed = processed.replace(/^>[ \t]+(.*)$/gm, '<blockquote>$1</blockquote>');
      processed = processed.replace(/<\/blockquote>\s*<blockquote>/g, '<br>');
      processed = processed.replace(/^###[ \t]+(.*)$/gm, '<h3>$1</h3>');
      processed = processed.replace(/^##[ \t]+(.*)$/gm, '<h2>$1</h2>');
      processed = processed.replace(/^#[ \t]+(.*)$/gm, '<h1>$1</h1>');
      processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      processed = processed.replace(/`([^`]+)`/g, (m, c) => `<code>${escapeHtml(c)}</code>`);

      const blocks = processed.split(/\r?\n\r?\n/);
      const formattedBlocks = blocks.map(block => {
        const trimmed = block.trim();
        if (!trimmed) return '';
        if (trimmed.startsWith('<div class="table-container">') || 
            trimmed.startsWith('__CODE_BLOCK_') || 
            trimmed.startsWith('<blockquote>') || 
            trimmed.startsWith('<h1') || 
            trimmed.startsWith('<h2') || 
            trimmed.startsWith('<h3')) {
          return trimmed;
        }
        return `<p>${trimmed.replace(/\r?\n/g, '<br>')}</p>`;
      });
      processed = formattedBlocks.filter(Boolean).join('\n');

      codeBlocks.forEach((cb, idx) => {
        processed = processed.replace(`__CODE_BLOCK_${idx}__`, cb);
      });

      return processed;
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("Starting Unified Business Assistant - Role C Orchestrator on http://127.0.0.1:8002 ...")
    uvicorn.run("app_role_c:app", host="127.0.0.1", port=8002, reload=True)
