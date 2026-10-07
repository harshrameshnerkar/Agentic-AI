"""
30-Case Agent Evaluation Test Suite.
Covers 6 Enterprise Operational Categories:
1. Database & SQL Analytics (TC-01 to TC-05)
2. Knowledge Base & RAG Search (TC-06 to TC-10)
3. Math & Metric Computations (TC-11 to TC-15)
4. Virtual Filesystem & Log Diagnostics (TC-16 to TC-20)
5. Multi-Step Chained Workflows (TC-21 to TC-25)
6. Edge Cases & Boundary Handling (TC-26 to TC-30)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TestCase:
    case_id: str
    category: str
    prompt: str
    expected_tools: List[str]
    expected_arg_matches: Dict[str, str] = field(default_factory=dict)
    forbidden_tools: List[str] = field(default_factory=list)
    max_allowed_steps: int = 3
    expected_final_keywords: List[str] = field(default_factory=list)
    description: str = ""


TEST_CASES_SUITE: List[TestCase] = [
    # -----------------------------------------------------------------------
    # 1. Database & SQL Analytics (TC-01 to TC-05)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-01",
        category="Database_Analytics",
        prompt="List all Enterprise tier customers from our customers database.",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "customers"},
        forbidden_tools=["send_alert", "read_file"],
        max_allowed_steps=3,
        expected_final_keywords=["Acme Corp", "Umbrella Corp"],
        description="Single-table query with filter criteria",
    ),
    TestCase(
        case_id="TC-02",
        category="Database_Analytics",
        prompt="What is the shipping status and order amount for customer order ORD-501?",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "orders"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["Shipped", "1450"],
        description="Point lookup by unique order ID",
    ),
    TestCase(
        case_id="TC-03",
        category="Database_Analytics",
        prompt="How many units of item SKU-SWITCH-24 do we currently hold in inventory and in which warehouse?",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "inventory"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["42", "US-West"],
        description="Inventory stock level and location query",
    ),
    TestCase(
        case_id="TC-04",
        category="Database_Analytics",
        prompt="Identify any customers in our database who have Churned status.",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "customers"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["Soylent Corp"],
        description="Customer churn status filtering",
    ),
    TestCase(
        case_id="TC-05",
        category="Database_Analytics",
        prompt="Look up order ORD-504 in the orders database and report its total amount.",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "orders"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["12500", "12,500"],
        description="Order record monetary verification",
    ),

    # -----------------------------------------------------------------------
    # 2. Knowledge Base & RAG Search (TC-06 to TC-10)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-06",
        category="Knowledge_RAG",
        prompt="What is our official company policy regarding JWT token signing and key rotation frequency?",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert", "query_database"],
        max_allowed_steps=3,
        expected_final_keywords=["90 days", "RS256"],
        description="SOP lookup for JWT security",
    ),
    TestCase(
        case_id="TC-07",
        category="Knowledge_RAG",
        prompt="What is the required response SLA for primary on-call engineers answering Sev-1 alerts?",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["15 minutes"],
        description="On-call incident SLA retrieval",
    ),
    TestCase(
        case_id="TC-08",
        category="Knowledge_RAG",
        prompt="What are our documented API rate limits for Standard vs Enterprise tier accounts?",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["60", "1000"],
        description="API throttling policy lookup",
    ),
    TestCase(
        case_id="TC-09",
        category="Knowledge_RAG",
        prompt="What uptime availability percentage and response time are guaranteed under our Tier 2 SLA?",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["99.95%"],
        description="Tier 2 SLA uptime criteria",
    ),
    TestCase(
        case_id="TC-10",
        category="Knowledge_RAG",
        prompt="According to financial compliance guidelines, for how many years must customer transaction records be retained?",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["7 years"],
        description="Data retention compliance lookup",
    ),

    # -----------------------------------------------------------------------
    # 3. Math & Metric Computations (TC-11 to TC-15)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-11",
        category="Math_Computations",
        prompt="Calculate our annual recurring revenue (ARR) if our current monthly recurring revenue (MRR) is $25,000.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["300000", "300,000"],
        description="Multiplication for annual ARR",
    ),
    TestCase(
        case_id="TC-12",
        category="Math_Computations",
        prompt="Calculate the gross profit margin percentage if total revenue is $400,000 and cost of goods sold is $280,000.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["30%", "30"],
        description="Profit margin percentage calculation",
    ),
    TestCase(
        case_id="TC-13",
        category="Math_Computations",
        prompt="Compute the exact combined sum of order amounts 1450.00 and 890.50.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["2340.5"],
        description="Addition of floating point currency",
    ),
    TestCase(
        case_id="TC-14",
        category="Math_Computations",
        prompt="What is the total valuation of 180 optical transceivers if each unit costs $45.00?",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["8100", "8,100"],
        description="Inventory batch valuation multiplication",
    ),
    TestCase(
        case_id="TC-15",
        category="Math_Computations",
        prompt="Calculate the monthly server uptime percentage if it experienced 12 minutes of downtime out of 43,200 total monthly minutes.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["99.97"],
        description="Uptime SLA percentage calculation",
    ),

    # -----------------------------------------------------------------------
    # 4. Virtual Filesystem & Diagnostics (TC-16 to TC-20)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-16",
        category="Filesystem_Diagnostics",
        prompt="Read the application configuration from /etc/config.json and tell me which port GatewayService listens on.",
        expected_tools=["read_file"],
        expected_arg_matches={"path": "/etc/config.json"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["8080"],
        description="JSON configuration inspection",
    ),
    TestCase(
        case_id="TC-17",
        category="Filesystem_Diagnostics",
        prompt="Inspect the system log at /var/log/syslog and identify the reason for recent database connection timeouts.",
        expected_tools=["read_file"],
        expected_arg_matches={"path": "/var/log/syslog"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["exhausted", "connection pool", "pool exhausted"],
        description="System log error diagnostics",
    ),
    TestCase(
        case_id="TC-18",
        category="Filesystem_Diagnostics",
        prompt="Check /app/manifest.yaml and report how many deployment replicas are configured for checkout-api.",
        expected_tools=["read_file"],
        expected_arg_matches={"path": "/app/manifest.yaml"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["4"],
        description="Kubernetes manifest inspection",
    ),
    TestCase(
        case_id="TC-19",
        category="Filesystem_Diagnostics",
        prompt="Review /var/log/auth.log to determine if there were any failed login attempts and what IP they originated from.",
        expected_tools=["read_file"],
        expected_arg_matches={"path": "/var/log/auth.log"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["192.168.1.5", "guest"],
        description="Security auth log inspection",
    ),
    TestCase(
        case_id="TC-20",
        category="Filesystem_Diagnostics",
        prompt="List the available log files present inside the /var/log directory.",
        expected_tools=["list_dir"],
        expected_arg_matches={"path": "/var/log"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["syslog", "auth.log"],
        description="Directory content listing",
    ),

    # -----------------------------------------------------------------------
    # 5. Multi-Step Chained Workflows (TC-21 to TC-25)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-21",
        category="Multi_Step",
        prompt="Find the unit cost of SKU-UPS-3000 in inventory, then calculate the total budget needed to purchase 5 units.",
        expected_tools=["query_database", "calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=4,
        expected_final_keywords=["6000", "6,000"],
        description="Chained lookup -> calculation",
    ),
    TestCase(
        case_id="TC-22",
        category="Multi_Step",
        prompt="Look up Acme Corp in customers table. If they are Enterprise tier, send an INFO alert to '#ops-alerts' with their MRR.",
        expected_tools=["query_database", "send_alert"],
        expected_arg_matches={"channel": "#ops-alerts"},
        forbidden_tools=[],
        max_allowed_steps=4,
        expected_final_keywords=["alert", "12500"],
        description="Chained database lookup -> conditional escalation",
    ),
    TestCase(
        case_id="TC-23",
        category="Multi_Step",
        prompt="Inspect /var/log/syslog for errors. If an error is detected, dispatch a CRITICAL alert to '#incident-room'.",
        expected_tools=["read_file", "send_alert"],
        expected_arg_matches={"channel": "#incident-room"},
        forbidden_tools=[],
        max_allowed_steps=4,
        expected_final_keywords=["alert", "exhausted"],
        description="Chained log inspection -> incident escalation",
    ),
    TestCase(
        case_id="TC-24",
        category="Multi_Step",
        prompt="Query order ORD-502's amount from database, then calculate the 8.5% sales tax on that order.",
        expected_tools=["query_database", "calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=4,
        expected_final_keywords=["75.69", "890.5"],
        description="Chained order lookup -> percentage tax computation",
    ),
    TestCase(
        case_id="TC-25",
        category="Multi_Step",
        prompt="Read the API rate limit for Enterprise tier from docs, and calculate how many requests that permits in a 60-minute hour.",
        expected_tools=["search_docs", "calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=4,
        expected_final_keywords=["60000", "60,000"],
        description="Chained policy search -> rate limit multiplication",
    ),

    # -----------------------------------------------------------------------
    # 6. Edge Cases & Boundary Handling (TC-26 to TC-30)
    # -----------------------------------------------------------------------
    TestCase(
        case_id="TC-26",
        category="Edge_Cases",
        prompt="Query the database for customer record with ID 'C-999'.",
        expected_tools=["query_database"],
        expected_arg_matches={"table": "customers"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["not found", "no customer", "0", "empty"],
        description="Querying non-existent database entity",
    ),
    TestCase(
        case_id="TC-27",
        category="Edge_Cases",
        prompt="Read the file contents of '/etc/secrets.env'.",
        expected_tools=["read_file"],
        expected_arg_matches={"path": "/etc/secrets.env"},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["does not exist", "not found", "filenotfound"],
        description="Attempting to read non-existent virtual file",
    ),
    TestCase(
        case_id="TC-28",
        category="Edge_Cases",
        prompt="Calculate the result of dividing 100 by 0.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["division by zero", "cannot divide", "error", "undefined"],
        description="Mathematical zero division boundary",
    ),
    TestCase(
        case_id="TC-29",
        category="Edge_Cases",
        prompt="Search company documentation for 'quantum hyperdrive warp engine specifications'.",
        expected_tools=["search_docs"],
        expected_arg_matches={},
        forbidden_tools=["send_alert"],
        max_allowed_steps=3,
        expected_final_keywords=["no documents", "not found"],
        description="Documentation search with zero matches",
    ),
    TestCase(
        case_id="TC-30",
        category="Edge_Cases",
        prompt="What is 15 + 27? Do not send any alerts or query any database.",
        expected_tools=["calculate"],
        expected_arg_matches={},
        forbidden_tools=["send_alert", "query_database"],
        max_allowed_steps=3,
        expected_final_keywords=["42"],
        description="Simple arithmetic respecting tool boundary constraints",
    ),
]
