"""
Role C Orchestrator & Evaluation Dashboard Service
Exposes:
- POST /api/chat      : Full end-to-end orchestrated query execution
- POST /api/route     : Interface 3 Routing decision inspection
- GET  /api/contract  : Committed Day 1 contract & fixtures
- GET  /api/metrics   : Latest evaluation benchmark metrics
- GET  /api/documents : List of all 50 enterprise knowledge documents
- GET  /api/schema    : Northwind Database schema metadata
- GET  /api/health    : Health check probe
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

@app.get("/api/documents")
def get_documents():
    """Returns metadata for all 50 enterprise knowledge documents."""
    doc_path = os.path.join(os.path.dirname(__file__), "data", "documents_metadata.json")
    if os.path.exists(doc_path):
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e), "documents": []}
    return {"total_documents": 0, "documents": []}

@app.get("/api/schema")
def get_database_schema():
    """Returns Northwind database schema metadata for UI explorer."""
    return {
        "database": "Northwind",
        "description": "Relational enterprise store powering text-to-SQL data service.",
        "tables": [
            {
                "name": "Customers",
                "description": "Customer accounts, company names, cities, and countries",
                "columns": ["CustomerID", "CustomerName", "ContactName", "Address", "City", "PostalCode", "Country"],
                "sample_query": "SELECT CustomerName, City, Country FROM Customers LIMIT 5;"
            },
            {
                "name": "Employees",
                "description": "Internal staff, designations, roles, and birth dates",
                "columns": ["EmployeeID", "LastName", "FirstName", "Title", "BirthDate", "Notes"],
                "sample_query": "SELECT FirstName, LastName, Title FROM Employees;"
            },
            {
                "name": "Products",
                "description": "Product catalog, supplier IDs, category IDs, units, and prices",
                "columns": ["ProductID", "ProductName", "SupplierID", "CategoryID", "Unit", "Price"],
                "sample_query": "SELECT ProductName, Price FROM Products ORDER BY Price DESC LIMIT 5;"
            },
            {
                "name": "Orders",
                "description": "Orders log, customer IDs, employee IDs, and order dates",
                "columns": ["OrderID", "CustomerID", "EmployeeID", "OrderDate", "ShipperID"],
                "sample_query": "SELECT OrderID, CustomerID, OrderDate FROM Orders LIMIT 5;"
            },
            {
                "name": "Suppliers",
                "description": "External vendors, contact names, phone numbers, and countries",
                "columns": ["SupplierID", "SupplierName", "ContactName", "City", "Country", "Phone"],
                "sample_query": "SELECT SupplierName, Country, Phone FROM Suppliers LIMIT 5;"
            },
            {
                "name": "Shippers",
                "description": "Logistics providers and shipping contact phones",
                "columns": ["ShipperID", "ShipperName", "Phone"],
                "sample_query": "SELECT * FROM Shippers;"
            }
        ]
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
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unified Business Assistant - Enterprise AI Hub</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #060913;
      --bg-panel: rgba(15, 23, 42, 0.75);
      --bg-card: rgba(22, 32, 54, 0.7);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-highlight: rgba(0, 242, 254, 0.3);
      --accent-cyan: #00f2fe;
      --accent-blue: #38bdf8;
      --accent-purple: #9d4edd;
      --accent-green: #10b981;
      --accent-gold: #f59e0b;
      --accent-red: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-sans: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      height: 100%;
      width: 100%;
      overflow: hidden;
      background: radial-gradient(circle at 15% 15%, #0f172a 0%, #060913 90%);
      color: var(--text-main);
      font-family: var(--font-sans);
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.14); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 242, 254, 0.4); }

    /* 3-Panel Main Layout */
    .app-layout {
      display: grid;
      grid-template-columns: 280px 1fr 360px;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }

    /* =========================================================
       1. LEFT SIDEBAR
       ========================================================= */
    .sidebar-left {
      background: rgba(10, 15, 28, 0.95);
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      height: 100vh;
      padding: 20px 16px;
      backdrop-filter: blur(20px);
      user-select: none;
    }

    .app-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.25rem;
      color: #000;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
      flex-shrink: 0;
    }
    .brand-text h1 {
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: -0.3px;
      color: #ffffff;
      line-height: 1.2;
    }
    .brand-text span {
      font-size: 0.72rem;
      color: var(--accent-cyan);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      font-weight: 600;
    }

    /* New Chat Button */
    .btn-new-chat {
      margin-top: 18px;
      width: 100%;
      padding: 12px 16px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(56, 189, 248, 0.25));
      border: 1px solid rgba(0, 242, 254, 0.4);
      color: #ffffff;
      font-family: inherit;
      font-size: 0.92rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 14px rgba(0, 242, 254, 0.15);
    }
    .btn-new-chat:hover {
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.3), rgba(56, 189, 248, 0.4));
      border-color: var(--accent-cyan);
      box-shadow: 0 6px 20px rgba(0, 242, 254, 0.35);
      transform: translateY(-1px);
    }
    .btn-new-chat svg {
      width: 18px;
      height: 18px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.2;
    }

    /* History Section */
    .history-header {
      margin-top: 24px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 4px;
    }
    .history-title {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.8px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .history-count {
      font-size: 0.7rem;
      background: rgba(255, 255, 255, 0.08);
      padding: 2px 7px;
      border-radius: 10px;
      color: var(--text-muted);
    }

    .sessions-list {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding-right: 4px;
    }
    .session-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid transparent;
      color: #cbd5e1;
    }
    .session-item:hover {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.1);
      color: #ffffff;
    }
    .session-item.active {
      background: rgba(0, 242, 254, 0.12);
      border-color: rgba(0, 242, 254, 0.35);
      color: var(--accent-cyan);
    }
    .session-info {
      display: flex;
      align-items: center;
      gap: 10px;
      overflow: hidden;
      flex: 1;
    }
    .session-icon {
      font-size: 0.9rem;
      opacity: 0.8;
      flex-shrink: 0;
    }
    .session-text-wrap {
      overflow: hidden;
    }
    .session-name {
      font-size: 0.83rem;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }
    .session-time {
      font-size: 0.68rem;
      color: var(--text-muted);
    }
    .session-delete-btn {
      opacity: 0;
      transition: opacity 0.2s;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px 6px;
      border-radius: 6px;
      font-size: 0.85rem;
    }
    .session-item:hover .session-delete-btn {
      opacity: 1;
    }
    .session-delete-btn:hover {
      color: var(--accent-red);
      background: rgba(244, 63, 94, 0.15);
    }

    /* Sidebar Bottom: Logout */
    .sidebar-footer {
      margin-top: auto;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }
    .btn-logout {
      width: 100%;
      padding: 10px 14px;
      border-radius: 10px;
      background: rgba(244, 63, 94, 0.08);
      border: 1px solid rgba(244, 63, 94, 0.25);
      color: #fb7185;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-logout:hover {
      background: rgba(244, 63, 94, 0.18);
      border-color: rgba(244, 63, 94, 0.45);
      color: #ffffff;
      box-shadow: 0 4px 14px rgba(244, 63, 94, 0.2);
    }

    /* =========================================================
       2. CENTER PANEL (CHAT INTERFACE)
       ========================================================= */
    .chat-panel {
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      background: rgba(11, 17, 32, 0.65);
      backdrop-filter: blur(16px);
      position: relative;
    }

    /* Top Title Bar */
    .chat-header {
      padding: 16px 28px;
      background: rgba(15, 23, 42, 0.85);
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      backdrop-filter: blur(12px);
      z-index: 10;
    }
    .chat-header-left h2 {
      font-size: 1.15rem;
      font-weight: 600;
      color: #ffffff;
      letter-spacing: -0.3px;
    }
    .chat-header-left p {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .header-badges {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.8rem;
      color: var(--accent-green);
      background: rgba(16, 185, 129, 0.12);
      padding: 5px 12px;
      border-radius: 20px;
      border: 1px solid rgba(16, 185, 129, 0.3);
      font-weight: 500;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 10px var(--accent-green);
      animation: pulseDot 2s infinite;
    }
    @keyframes pulseDot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.35; transform: scale(0.85); }
    }

    /* Chat Messages Stream */
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 24px 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .msg-row {
      display: flex;
      gap: 14px;
      max-width: 90%;
      animation: fadeInUp 0.28s ease;
    }
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg-row.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .msg-avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.88rem;
      font-weight: 700;
      flex-shrink: 0;
    }
    .msg-row.user .msg-avatar {
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
      color: #000;
      box-shadow: 0 2px 10px rgba(56, 189, 248, 0.3);
    }
    .msg-row.ai .msg-avatar {
      background: linear-gradient(135deg, var(--accent-purple), #7b2cbf);
      color: #fff;
      box-shadow: 0 2px 10px rgba(157, 78, 221, 0.35);
    }

    .msg-bubble {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 16px 20px;
      line-height: 1.6;
      font-size: 0.94rem;
      color: #e2e8f0;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
      max-width: 100%;
      word-break: break-word;
    }
    .msg-row.user .msg-bubble {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(0, 242, 254, 0.18));
      border-color: rgba(0, 242, 254, 0.35);
      color: #ffffff;
    }

    /* Route Pill */
    .route-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 11px;
      border-radius: 12px;
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 10px;
    }
    .route-knowledge { background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }
    .route-data { background: rgba(16, 185, 129, 0.18); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.35); }
    .route-both { background: rgba(157, 78, 221, 0.2); color: #d8b4fe; border: 1px solid rgba(157, 78, 221, 0.4); }
    .route-none { background: rgba(244, 63, 94, 0.18); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.35); }

    /* Boxed Custom Tables */
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
      background: rgba(56, 189, 248, 0.18);
      color: #38bdf8;
      font-weight: 600;
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.18);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      white-space: nowrap;
    }
    .custom-table th:last-child { border-right: none; }
    .custom-table td {
      padding: 9px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      border-right: 1px solid rgba(255, 255, 255, 0.08);
      color: #e2e8f0;
    }
    .custom-table td:last-child { border-right: none; }
    .custom-table tr:last-child td { border-bottom: none; }
    .custom-table tr:nth-child(even) td { background: rgba(255, 255, 255, 0.02); }
    .custom-table tr:hover td { background: rgba(0, 242, 254, 0.07); }

    /* Formatted Markdown Content */
    .rendered-answer {
      font-size: 0.94rem;
      line-height: 1.65;
    }
    .rendered-answer h3 {
      font-size: 1.05rem;
      font-weight: 600;
      margin: 10px 0 6px;
      color: #38bdf8;
    }
    .rendered-answer p { margin: 6px 0; }
    .rendered-answer strong { color: #ffffff; }
    .rendered-answer blockquote {
      border-left: 3px solid var(--accent-purple);
      background: rgba(157, 78, 221, 0.12);
      padding: 10px 16px;
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
      padding: 12px 16px;
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

    /* Citations Bar */
    .citations-bar {
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .citations-title {
      color: var(--text-muted);
      font-size: 0.74rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .citation-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: rgba(0, 242, 254, 0.08);
      border: 1px solid rgba(0, 242, 254, 0.24);
      color: #38bdf8;
      padding: 3px 10px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-family: var(--font-mono);
    }

    /* Quick Prompts Chips */
    .quick-prompts {
      padding: 10px 24px;
      background: rgba(10, 15, 28, 0.6);
      border-top: 1px solid var(--border-subtle);
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }
    .prompt-chip {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.79rem;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
      user-select: none;
    }
    .prompt-chip:hover {
      background: rgba(0, 242, 254, 0.15);
      border-color: var(--accent-cyan);
      color: #ffffff;
      transform: translateY(-1px);
    }

    /* Chat Input Area */
    .chat-input-area {
      padding: 16px 24px 20px;
      border-top: 1px solid var(--border-subtle);
      background: rgba(15, 23, 42, 0.95);
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .chat-input {
      flex: 1;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 14px 18px;
      color: #ffffff;
      font-family: inherit;
      font-size: 0.95rem;
      outline: none;
      transition: all 0.2s ease;
    }
    .chat-input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 14px rgba(0, 242, 254, 0.25);
      background: rgba(255, 255, 255, 0.07);
    }
    .send-btn {
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      border: none;
      color: #000;
      font-weight: 700;
      font-family: inherit;
      font-size: 0.95rem;
      padding: 0 24px;
      height: 48px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(0, 242, 254, 0.3);
    }
    .send-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(0, 242, 254, 0.45);
    }
    .send-btn:active { transform: translateY(0); }

    /* =========================================================
       3. RIGHT SIDEBAR
       ========================================================= */
    .sidebar-right {
      background: rgba(10, 15, 28, 0.95);
      border-left: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      backdrop-filter: blur(20px);
    }

    /* User Profile Card */
    .user-profile-section {
      padding: 20px 20px 16px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .user-profile-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .user-avatar-circle {
      width: 46px;
      height: 46px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.35rem;
      color: #ffffff;
      box-shadow: 0 0 16px rgba(0, 242, 254, 0.45);
      flex-shrink: 0;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    .user-details {
      flex: 1;
      overflow: hidden;
    }
    .user-details h3 {
      font-size: 1rem;
      font-weight: 600;
      color: #ffffff;
      line-height: 1.2;
    }
    .user-role-badge {
      font-size: 0.72rem;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 3px;
    }
    .user-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 6px var(--accent-green);
    }

    /* Middle: Interactive Sample Queries */
    .sample-queries-section {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-subtle);
      max-height: 240px;
      display: flex;
      flex-direction: column;
    }
    .section-title {
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .sample-queries-list {
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-right: 4px;
    }
    .sample-query-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 9px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .sample-query-card:hover {
      background: rgba(0, 242, 254, 0.1);
      border-color: rgba(0, 242, 254, 0.35);
      transform: translateY(-1px);
    }
    .sample-tag {
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .tag-data { color: var(--accent-green); }
    .tag-knowledge { color: var(--accent-blue); }
    .tag-hybrid { color: var(--accent-purple); }
    .tag-guardrail { color: var(--accent-red); }
    .sample-text {
      font-size: 0.81rem;
      color: #e2e8f0;
      line-height: 1.35;
    }

    /* Bottom: Documents & Database Explorer */
    .explorer-section {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 14px 20px 20px;
    }
    .explorer-tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      background: rgba(0, 0, 0, 0.25);
      padding: 4px;
      border-radius: 10px;
      margin-bottom: 12px;
      border: 1px solid var(--border-subtle);
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: rgba(0, 242, 254, 0.18);
      color: #ffffff;
      border: 1px solid rgba(0, 242, 254, 0.3);
    }

    .explorer-content {
      flex: 1;
      overflow-y: auto;
      padding-right: 4px;
    }

    /* Document Search & List */
    .doc-search-box {
      margin-bottom: 10px;
      position: relative;
    }
    .doc-search-input {
      width: 100%;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.8rem;
      color: #ffffff;
      outline: none;
      font-family: inherit;
    }
    .doc-search-input:focus {
      border-color: var(--accent-cyan);
    }
    .doc-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 10px 12px;
      margin-bottom: 8px;
      transition: all 0.2s;
      cursor: pointer;
    }
    .doc-card:hover {
      background: rgba(56, 189, 248, 0.08);
      border-color: rgba(56, 189, 248, 0.3);
    }
    .doc-title {
      font-size: 0.84rem;
      font-weight: 600;
      color: #ffffff;
      line-height: 1.3;
    }
    .doc-filename {
      font-size: 0.72rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .doc-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .doc-badge {
      font-size: 0.67rem;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.06);
      color: #94a3b8;
    }
    .doc-badge.company { background: rgba(56, 189, 248, 0.12); color: #38bdf8; }
    .doc-badge.pages { background: rgba(16, 185, 129, 0.12); color: #10b981; }

    /* Database Schema Cards */
    .table-schema-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 10px 12px;
      margin-bottom: 8px;
    }
    .table-schema-card:hover {
      border-color: rgba(16, 185, 129, 0.35);
    }
    .table-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .table-name {
      font-size: 0.86rem;
      font-weight: 700;
      color: #10b981;
      font-family: var(--font-mono);
    }
    .btn-query-table {
      font-size: 0.7rem;
      background: rgba(16, 185, 129, 0.14);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #10b981;
      padding: 2px 8px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }
    .btn-query-table:hover {
      background: rgba(16, 185, 129, 0.25);
      color: #ffffff;
    }
    .table-columns-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 6px;
    }
    .col-pill {
      font-size: 0.7rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
      color: #cbd5e1;
      font-family: var(--font-mono);
    }

    /* Logout Confirmation Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      animation: fadeIn 0.2s ease;
    }
    .modal-card {
      background: #0f172a;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      padding: 28px;
      width: 90%;
      max-width: 400px;
      text-align: center;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
    }
    .modal-icon {
      font-size: 2.2rem;
      margin-bottom: 12px;
    }
    .modal-card h3 {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .modal-card p {
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 20px;
    }
    .modal-actions {
      display: flex;
      gap: 12px;
    }
    .btn-cancel {
      flex: 1;
      padding: 10px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border-subtle);
      color: #ffffff;
      font-family: inherit;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-confirm-logout {
      flex: 1;
      padding: 10px;
      border-radius: 10px;
      background: linear-gradient(135deg, #f43f5e, #e11d48);
      border: none;
      color: #ffffff;
      font-family: inherit;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
    }

    /* Signed Out Overlay */
    .logged-out-overlay {
      position: fixed;
      inset: 0;
      background: radial-gradient(circle at center, #0f172a 0%, #060913 90%);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999;
    }
    .logged-out-card {
      background: rgba(18, 24, 38, 0.85);
      border: 1px solid var(--border-subtle);
      border-radius: 20px;
      padding: 36px 32px;
      text-align: center;
      max-width: 420px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
    }
    .btn-signin {
      margin-top: 20px;
      width: 100%;
      padding: 12px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      border: none;
      color: #000;
      font-family: inherit;
      font-size: 0.95rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0, 242, 254, 0.3);
    }
  </style>
</head>
<body>

  <!-- App Main 3-Panel Layout -->
  <div class="app-layout">

    <!-- =========================================================
         1. LEFT SIDEBAR: Brand, New Chat, Recent History, Logout
         ========================================================= -->
    <aside class="sidebar-left">
      <!-- App Brand -->
      <div class="app-brand">
        <div class="brand-icon">UB</div>
        <div class="brand-text">
          <h1>Unified Business Assistant</h1>
          <span>AI Enterprise Suite</span>
        </div>
      </div>

      <!-- New Chat Button -->
      <button class="btn-new-chat" onclick="createNewChat()">
        <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
        New Chat
      </button>

      <!-- Recent History Header -->
      <div class="history-header">
        <span class="history-title">
          <span>🕒</span> Recent History
        </span>
        <span class="history-count" id="sessionCount">0</span>
      </div>

      <!-- Scrollable Recent Sessions List -->
      <div class="sessions-list" id="sessionsList">
        <!-- Dynamically rendered via JS from localStorage -->
      </div>

      <!-- Sidebar Bottom: Logout -->
      <div class="sidebar-footer">
        <button class="btn-logout" onclick="openLogoutModal()">
          <span>🚪</span> Logout
        </button>
      </div>
    </aside>

    <!-- =========================================================
         2. CENTER PANEL: Chat Interface
         ========================================================= -->
    <main class="chat-panel">
      <!-- Top Title Bar -->
      <header class="chat-header">
        <div class="chat-header-left">
          <h2>Interactive Orchestration Playground</h2>
          <p>Multi-Domain Router & Synthesis (Knowledge RAG + Northwind SQL + Cross-Domain Hybrid)</p>
        </div>
        <div class="header-badges">
          <div class="status-badge">
            <div class="status-dot"></div>
            Interface Contract v1.0.0 Active
          </div>
        </div>
      </header>

      <!-- Chat Messages Scroll Container -->
      <div class="chat-messages" id="chatBox">
        <!-- Rendered dynamically -->
      </div>

      <!-- Suggested Quick Prompt Chips -->
      <div class="quick-prompts">
        <div class="prompt-chip" data-prompt="Show all product names and their corresponding prices.">📊 Data: Product Prices</div>
        <div class="prompt-chip" data-prompt="What is GitLab's Expense Policy for daily meal reimbursement?">📄 Knowledge: Meal Policy</div>
        <div class="prompt-chip" data-prompt="Check our employee handbook to see if any customers from Germany are violating our gift and hospitality policies.">🔀 Hybrid: German Customers</div>
        <div class="prompt-chip" data-prompt="What is the exact current real-time stock price of Jayaswal Neco on the NSE right now?">🛡️ Guardrail: Live Ticker</div>
      </div>

      <!-- Chat Input Area -->
      <div class="chat-input-area">
        <input type="text" id="userInput" class="chat-input" placeholder="Type a business question or click a query from the right sidebar..." onkeydown="if(event.key==='Enter') sendQuery()">
        <button class="send-btn" id="sendBtn" onclick="sendQuery()">
          <span>Send</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
      </div>
    </main>

    <!-- =========================================================
         3. RIGHT SIDEBAR: Profile, Sample Queries, Knowledge & DB
         ========================================================= -->
    <aside class="sidebar-right">
      <!-- Top: User Profile Card -->
      <div class="user-profile-section">
        <div class="user-profile-card">
          <div class="user-avatar-circle">U</div>
          <div class="user-details">
            <h3>User</h3>
            <div class="user-role-badge">
              <div class="user-status-dot"></div>
              <span>Enterprise User</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Middle: Sample Queries to Execute -->
      <div class="sample-queries-section">
        <div class="section-title">
          <span>⚡ Sample Queries</span>
          <span style="font-size: 0.68rem; color: var(--accent-cyan);">Click to Run</span>
        </div>
        <div class="sample-queries-list">
          <div class="sample-query-card" onclick="executeSample('Show all product names and their corresponding prices.')">
            <span class="sample-tag tag-data">📊 Data Service (SQL)</span>
            <span class="sample-text">Show all product names and their corresponding prices.</span>
          </div>
          <div class="sample-query-card" onclick="executeSample('What is GitLab\'s Expense Policy for daily meal reimbursement?')">
            <span class="sample-tag tag-knowledge">📄 Knowledge Service (RAG)</span>
            <span class="sample-text">What is GitLab's Expense Policy for daily meal reimbursement?</span>
          </div>
          <div class="sample-query-card" onclick="executeSample('Check our employee handbook to see if any customers from Germany are violating our gift and hospitality policies.')">
            <span class="sample-tag tag-hybrid">🔀 Cross-Domain Hybrid</span>
            <span class="sample-text">Check handbook to see if customers from Germany violate gift policies.</span>
          </div>
          <div class="sample-query-card" onclick="executeSample('Can we hire a relative of a Government Official if they are currently listed as an active employee in our Northwind system?')">
            <span class="sample-tag tag-hybrid">👥 Entity + Policy Hybrid</span>
            <span class="sample-text">Can we hire a relative of a Government Official active in Northwind?</span>
          </div>
          <div class="sample-query-card" onclick="executeSample('What is the exact current real-time stock price of Jayaswal Neco on the NSE right now?')">
            <span class="sample-tag tag-guardrail">🛡️ Guardrail Fallback</span>
            <span class="sample-text">What is the exact real-time stock price of Jayaswal Neco on NSE?</span>
          </div>
        </div>
      </div>

      <!-- Bottom: Knowledge Documents & Data Service Explorer -->
      <div class="explorer-section">
        <div class="explorer-tabs">
          <button class="tab-btn active" id="tabDocsBtn" onclick="switchExplorerTab('docs')">📄 Knowledge Docs (<span id="docCountBadge">50</span>)</button>
          <button class="tab-btn" id="tabDbBtn" onclick="switchExplorerTab('db')">🗄️ Database (Northwind)</button>
        </div>

        <!-- Tab 1: Knowledge Documents -->
        <div class="explorer-content" id="tabContentDocs">
          <div class="doc-search-box">
            <input type="text" id="docSearchInput" class="doc-search-input" placeholder="🔍 Search 50 documents..." oninput="filterDocuments()">
          </div>
          <div id="docsContainer">
            <!-- Rendered dynamically -->
          </div>
        </div>

        <!-- Tab 2: Database Schema -->
        <div class="explorer-content" id="tabContentDb" style="display: none;">
          <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 10px;">
            Northwind SQLite database schema powering Role B text-to-SQL.
          </div>
          <div id="schemaContainer">
            <!-- Rendered dynamically -->
          </div>
        </div>
      </div>
    </aside>

  </div>

  <!-- Logout Confirmation Modal -->
  <div id="logoutModal" class="modal-overlay" style="display: none;">
    <div class="modal-card">
      <div class="modal-icon">🚪</div>
      <h3>Sign Out</h3>
      <p>Are you sure you want to log out? Your current chat history is safely preserved in local session storage.</p>
      <div class="modal-actions">
        <button class="btn-cancel" onclick="closeLogoutModal()">Cancel</button>
        <button class="btn-confirm-logout" onclick="confirmLogout()">Log Out</button>
      </div>
    </div>
  </div>

  <!-- Signed Out Screen Overlay -->
  <div id="loggedOutOverlay" class="logged-out-overlay" style="display: none;">
    <div class="logged-out-card">
      <div class="user-avatar-circle" style="width: 58px; height: 58px; font-size: 1.8rem; margin: 0 auto 16px;">U</div>
      <h2 style="font-size: 1.3rem; margin-bottom: 8px;">Signed Out</h2>
      <p style="font-size: 0.88rem; color: var(--text-muted);">You have safely signed out of Unified Business Assistant.</p>
      <button class="btn-signin" onclick="signInAgain()">Sign In as User</button>
    </div>
  </div>

  <script>
    // State
    let sessions = [];
    let activeSessionId = null;
    let allDocuments = [];
    let databaseSchema = [];

    // Initialize application on load
    window.addEventListener('DOMContentLoaded', function() {
      initAuth();
      initSessions();
      loadDocuments();
      loadDatabaseSchema();
      setupChipListeners();
    });

    // -------------------------------------------------------------
    // Session & History Management (localStorage)
    // -------------------------------------------------------------
    function initSessions() {
      try {
        const stored = localStorage.getItem('uba_sessions');
        if (stored) {
          sessions = JSON.parse(stored);
        }
      } catch (e) {
        sessions = [];
      }

      if (!sessions || sessions.length === 0) {
        createNewChat(false);
      } else {
        const storedActive = localStorage.getItem('uba_active_session_id');
        const found = sessions.find(s => s.id === storedActive);
        activeSessionId = found ? found.id : sessions[0].id;
        renderSessionsList();
        renderActiveChat();
      }
    }

    function saveSessions() {
      try {
        localStorage.setItem('uba_sessions', JSON.stringify(sessions));
        localStorage.setItem('uba_active_session_id', activeSessionId);
      } catch (e) {}
    }

    function createNewChat(autoFocus = true) {
      const newSession = {
        id: 'session_' + Date.now(),
        title: 'New Conversation',
        createdAt: Date.now(),
        messages: []
      };
      sessions.unshift(newSession);
      activeSessionId = newSession.id;
      saveSessions();
      renderSessionsList();
      renderActiveChat();

      if (autoFocus) {
        const inp = document.getElementById('userInput');
        if (inp) inp.focus();
      }
    }

    function switchSession(id) {
      activeSessionId = id;
      saveSessions();
      renderSessionsList();
      renderActiveChat();
    }

    function deleteSession(id, event) {
      if (event) event.stopPropagation();
      sessions = sessions.filter(s => s.id !== id);
      if (sessions.length === 0) {
        createNewChat(false);
      } else {
        if (activeSessionId === id) {
          activeSessionId = sessions[0].id;
        }
        saveSessions();
        renderSessionsList();
        renderActiveChat();
      }
    }

    function renderSessionsList() {
      const container = document.getElementById('sessionsList');
      const countEl = document.getElementById('sessionCount');
      if (countEl) countEl.innerText = sessions.length;

      if (!container) return;
      container.innerHTML = '';

      sessions.forEach(s => {
        const isActive = s.id === activeSessionId;
        const timeAgo = formatTimeAgo(s.createdAt);

        const item = document.createElement('div');
        item.className = 'session-item' + (isActive ? ' active' : '');
        item.onclick = function() { switchSession(s.id); };

        item.innerHTML = `
          <div class="session-info">
            <span class="session-icon">💬</span>
            <div class="session-text-wrap">
              <div class="session-name">${escapeHtml(s.title)}</div>
              <div class="session-time">${escapeHtml(timeAgo)}</div>
            </div>
          </div>
          <button class="session-delete-btn" title="Delete conversation" onclick="deleteSession('${s.id}', event)">✕</button>
        `;
        container.appendChild(item);
      });
    }

    function formatTimeAgo(timestamp) {
      if (!timestamp) return 'Just now';
      const diff = Math.floor((Date.now() - timestamp) / 1000);
      if (diff < 60) return 'Just now';
      if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
      if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
      return Math.floor(diff / 86400) + 'd ago';
    }

    // -------------------------------------------------------------
    // Chat Rendering
    // -------------------------------------------------------------
    function renderActiveChat() {
      const chatBox = document.getElementById('chatBox');
      if (!chatBox) return;

      const activeSession = sessions.find(s => s.id === activeSessionId);
      if (!activeSession || !activeSession.messages || activeSession.messages.length === 0) {
        chatBox.innerHTML = `
          <div class="msg-row ai">
            <div class="msg-avatar">AI</div>
            <div class="msg-bubble">
              <strong>Welcome, User!</strong><br>
              Unified Business Assistant is ready. This enterprise orchestrator combines:<br>
              • <strong>Role A (/search)</strong>: Corporate Policy RAG across 50 enterprise PDFs.<br>
              • <strong>Role B (/query)</strong>: Text-to-SQL data analytics on Northwind.<br>
              • <strong>Role C (/route & /chat)</strong>: Interface 3 multi-domain routing & cross-domain synthesis.<br><br>
              Try asking a question below or click any sample query from the right panel!
            </div>
          </div>
        `;
        return;
      }

      chatBox.innerHTML = '';
      activeSession.messages.forEach(msg => {
        if (msg.role === 'user') {
          chatBox.innerHTML += `
            <div class="msg-row user">
              <div class="msg-avatar">ME</div>
              <div class="msg-bubble">${escapeHtml(msg.content)}</div>
            </div>
          `;
        } else {
          const routeClass = 'route-' + (msg.route || 'knowledge');
          let citationsHtml = '';
          if (msg.citations && msg.citations.length > 0) {
            const pills = msg.citations.map(function(c) {
              return '<span class="citation-pill">📄 ' + escapeHtml(c) + '</span>';
            }).join(' ');
            citationsHtml = '<div class="citations-bar"><span class="citations-title">Sources:</span> ' + pills + '</div>';
          }

          chatBox.innerHTML += `
            <div class="msg-row ai">
              <div class="msg-avatar">AI</div>
              <div class="msg-bubble">
                <div><span class="route-tag ${routeClass}">Route: ${escapeHtml(msg.route || 'knowledge')} (${Math.round((msg.confidence||1)*100)}% conf)</span></div>
                <div class="rendered-answer">${formatMarkdown(msg.content)}</div>
                ${citationsHtml}
              </div>
            </div>
          `;
        }
      });

      chatBox.scrollTop = chatBox.scrollHeight;
    }

    // -------------------------------------------------------------
    // Query Execution
    // -------------------------------------------------------------
    async function sendQuery() {
      const input = document.getElementById('userInput');
      const q = input.value.trim();
      if (!q) return;

      const chatBox = document.getElementById('chatBox');
      const activeSession = sessions.find(s => s.id === activeSessionId);
      if (!activeSession) return;

      // Update session title if first message
      if (activeSession.messages.length === 0) {
        activeSession.title = q.length > 28 ? q.substring(0, 28) + '...' : q;
        renderSessionsList();
      }

      // Add user message to state
      activeSession.messages.push({ role: 'user', content: q, timestamp: Date.now() });
      saveSessions();

      // Render user message
      chatBox.innerHTML += `
        <div class="msg-row user">
          <div class="msg-avatar">ME</div>
          <div class="msg-bubble">${escapeHtml(q)}</div>
        </div>
      `;
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      // Render loading indicator
      const loadingId = 'loading-' + Date.now();
      chatBox.innerHTML += `
        <div class="msg-row ai" id="${loadingId}">
          <div class="msg-avatar">AI</div>
          <div class="msg-bubble" style="color: var(--text-muted);">
            <em>Evaluating Interface 3 route and synthesizing response...</em>
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

        const answerText = data.final_answer || 'No response returned.';
        const route = data.route || 'knowledge';
        const confidence = data.confidence || 1.0;
        const citations = data.citations || [];

        // Save AI message to state
        activeSession.messages.push({
          role: 'ai',
          content: answerText,
          route: route,
          confidence: confidence,
          citations: citations,
          timestamp: Date.now()
        });
        saveSessions();

        const routeClass = 'route-' + route;
        let citationsHtml = '';
        if (citations.length > 0) {
          const pills = citations.map(function(c) {
            return '<span class="citation-pill">📄 ' + escapeHtml(c) + '</span>';
          }).join(' ');
          citationsHtml = '<div class="citations-bar"><span class="citations-title">Sources:</span> ' + pills + '</div>';
        }

        chatBox.innerHTML += `
          <div class="msg-row ai">
            <div class="msg-avatar">AI</div>
            <div class="msg-bubble">
              <div><span class="route-tag ${routeClass}">Route: ${escapeHtml(route)} (${Math.round(confidence * 100)}% conf)</span></div>
              <div class="rendered-answer">${formatMarkdown(answerText)}</div>
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
              Error: ${escapeHtml(err.message)}
            </div>
          </div>
        `;
      }

      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function executeSample(queryText) {
      const input = document.getElementById('userInput');
      if (input) {
        input.value = queryText;
        sendQuery();
      }
    }

    function setupChipListeners() {
      document.querySelectorAll('.prompt-chip').forEach(function(chip) {
        chip.addEventListener('click', function() {
          const text = this.getAttribute('data-prompt');
          if (text) {
            executeSample(text);
          }
        });
      });
    }

    // -------------------------------------------------------------
    // Right Sidebar: Documents & Schema
    // -------------------------------------------------------------
    function switchExplorerTab(tab) {
      const btnDocs = document.getElementById('tabDocsBtn');
      const btnDb = document.getElementById('tabDbBtn');
      const contentDocs = document.getElementById('tabContentDocs');
      const contentDb = document.getElementById('tabContentDb');

      if (tab === 'docs') {
        btnDocs.classList.add('active');
        btnDb.classList.remove('active');
        contentDocs.style.display = 'block';
        contentDb.style.display = 'none';
      } else {
        btnDb.classList.add('active');
        btnDocs.classList.remove('active');
        contentDb.style.display = 'block';
        contentDocs.style.display = 'none';
      }
    }

    async function loadDocuments() {
      try {
        const res = await fetch('/api/documents');
        const data = await res.json();
        allDocuments = data.documents || [];
      } catch (e) {
        allDocuments = [];
      }
      renderDocuments(allDocuments);
      const badge = document.getElementById('docCountBadge');
      if (badge) badge.innerText = allDocuments.length;
    }

    function renderDocuments(docs) {
      const container = document.getElementById('docsContainer');
      if (!container) return;

      if (!docs || docs.length === 0) {
        container.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-muted); padding: 12px 0;">No matching documents found.</div>';
        return;
      }

      let html = '';
      docs.forEach(d => {
        const askQuery = 'What does ' + (d.company || 'the policy') + ' state regarding ' + (d.title || d.filename) + '?';
        html += `
          <div class="doc-card" onclick="executeSample('${escapeHtml(askQuery).replace(/'/g, "\\'")}')" title="Click to ask about this document">
            <div class="doc-title">${escapeHtml(d.title || d.filename)}</div>
            <div class="doc-filename">${escapeHtml(d.filename)}</div>
            <div class="doc-meta">
              <span class="doc-badge company">${escapeHtml(d.company || 'Enterprise')}</span>
              <span class="doc-badge pages">${d.pages || 1} pages</span>
              <span class="doc-badge">${escapeHtml(d.category || 'Policy')}</span>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
    }

    function filterDocuments() {
      const query = (document.getElementById('docSearchInput').value || '').toLowerCase().trim();
      if (!query) {
        renderDocuments(allDocuments);
        return;
      }
      const filtered = allDocuments.filter(d => {
        return (d.title && d.title.toLowerCase().includes(query)) ||
               (d.filename && d.filename.toLowerCase().includes(query)) ||
               (d.company && d.company.toLowerCase().includes(query)) ||
               (d.category && d.category.toLowerCase().includes(query));
      });
      renderDocuments(filtered);
    }

    async function loadDatabaseSchema() {
      try {
        const res = await fetch('/api/schema');
        const data = await res.json();
        databaseSchema = data.tables || [];
      } catch (e) {
        databaseSchema = [];
      }
      renderDatabaseSchema(databaseSchema);
    }

    function renderDatabaseSchema(tables) {
      const container = document.getElementById('schemaContainer');
      if (!container) return;

      let html = '';
      tables.forEach(t => {
        const sampleQ = 'Show top 5 records from ' + t.name + ' table';
        const cols = (t.columns || []).map(c => `<span class="col-pill">${escapeHtml(c)}</span>`).join('');
        html += `
          <div class="table-schema-card">
            <div class="table-head">
              <span class="table-name">📁 ${escapeHtml(t.name)}</span>
              <button class="btn-query-table" onclick="executeSample('${escapeHtml(sampleQ)}')">Query</button>
            </div>
            <div style="font-size: 0.74rem; color: var(--text-muted);">${escapeHtml(t.description || '')}</div>
            <div class="table-columns-pills">${cols}</div>
          </div>
        `;
      });
      container.innerHTML = html;
    }

    // -------------------------------------------------------------
    // Auth & Logout
    // -------------------------------------------------------------
    function initAuth() {
      const loggedIn = localStorage.getItem('uba_logged_in');
      if (loggedIn === 'false') {
        document.getElementById('loggedOutOverlay').style.display = 'flex';
      }
    }

    function openLogoutModal() {
      document.getElementById('logoutModal').style.display = 'flex';
    }

    function closeLogoutModal() {
      document.getElementById('logoutModal').style.display = 'none';
    }

    function confirmLogout() {
      closeLogoutModal();
      localStorage.setItem('uba_logged_in', 'false');
      document.getElementById('loggedOutOverlay').style.display = 'flex';
    }

    function signInAgain() {
      localStorage.setItem('uba_logged_in', 'true');
      document.getElementById('loggedOutOverlay').style.display = 'none';
    }

    // -------------------------------------------------------------
    // Markdown & Boxed Table Parser
    // -------------------------------------------------------------
    function escapeHtml(text) {
      if (!text) return '';
      return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function parseTables(text) {
      if (!text || text.indexOf('|') === -1) return text;
      const lines = text.split(/\r?\n/);
      const out = [];
      let i = 0;
      while (i < lines.length) {
        const line = lines[i];
        const trimmed = line.trim();
        if (trimmed.startsWith('|') && trimmed.endsWith('|') && i + 1 < lines.length) {
          const nextTrimmed = lines[i + 1].trim();
          if (/^\|(?:\s*:?-+:?\s*\|)+$/.test(nextTrimmed)) {
            const parseCells = function(l) {
              return l.trim().slice(1, -1).split('|').map(function(c) { return c.trim(); });
            };
            const headers = parseCells(trimmed);
            i += 2;
            const bodyRows = [];
            while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
              bodyRows.push(parseCells(lines[i]));
              i++;
            }
            let html = '<div class="table-container"><table class="custom-table"><thead><tr>';
            for (let h = 0; h < headers.length; h++) {
              html += '<th>' + escapeHtml(headers[h]) + '</th>';
            }
            html += '</tr></thead><tbody>';
            for (let r = 0; r < bodyRows.length; r++) {
              html += '<tr>';
              for (let c = 0; c < headers.length; c++) {
                const val = bodyRows[r][c] !== undefined ? bodyRows[r][c] : '';
                html += '<td>' + escapeHtml(val) + '</td>';
              }
              html += '</tr>';
            }
            html += '</tbody></table></div>';
            out.push(html);
            continue;
          }
        }
        out.push(line);
        i++;
      }
      return out.join('\n');
    }

    function formatMarkdown(text) {
      if (!text) return '';
      const codeBlocks = [];
      let processed = text.replace(/```([a-zA-Z0-9_-]*)\s*([\s\S]*?)```/g, function(match, lang, code) {
        const token = '__CODE_BLOCK_' + codeBlocks.length + '__';
        codeBlocks.push('<pre><code class="' + (lang ? 'language-' + lang : '') + '">' + escapeHtml(code.trim()) + '</code></pre>');
        return token;
      });

      processed = parseTables(processed);
      processed = processed.replace(/^>[ \t]+(.*)$/gm, '<blockquote>$1</blockquote>');
      processed = processed.replace(/<\/blockquote>\s*<blockquote>/g, '<br>');
      processed = processed.replace(/^###[ \t]+(.*)$/gm, '<h3>$1</h3>');
      processed = processed.replace(/^##[ \t]+(.*)$/gm, '<h2>$1</h2>');
      processed = processed.replace(/^#[ \t]+(.*)$/gm, '<h1>$1</h1>');
      processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      processed = processed.replace(/`([^`]+)`/g, function(m, c) { return '<code>' + escapeHtml(c) + '</code>'; });

      const blocks = processed.split(/\n\n+/);
      const formattedBlocks = blocks.map(function(block) {
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
        return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
      });
      processed = formattedBlocks.filter(Boolean).join('\n');

      codeBlocks.forEach(function(cb, idx) {
        processed = processed.replace('__CODE_BLOCK_' + idx + '__', cb);
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
