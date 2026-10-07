"""
Production-Realistic Enterprise Workload Dataset.
Contains 30 operational queries structured across:
- 18 Unique baseline queries (Database, Docs, Math, Logs).
- 6 Exact repeat queries (evaluates Exact Caching: 100% hits, 0 tokens, <1ms).
- 6 Semantically paraphrased queries (evaluates Semantic Intent Caching: 0 tokens, <2ms).
"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class WorkloadQuery:
    query_id: str
    query_text: str
    query_type: str  # "unique", "exact_repeat", "semantic_repeat"
    expected_keywords: List[str] = field(default_factory=list)
    description: str = ""


ENTERPRISE_WORKLOAD: List[WorkloadQuery] = [
    # -----------------------------------------------------------------------
    # 1. Unique Invocations (Initial Baseline Traffic)
    # -----------------------------------------------------------------------
    WorkloadQuery(
        query_id="Q-01",
        query_text="List all Enterprise tier customers from our database.",
        query_type="unique",
        expected_keywords=["Acme Corp", "Umbrella Corp"],
        description="Customer tier filtering",
    ),
    WorkloadQuery(
        query_id="Q-02",
        query_text="What is our official company policy on JWT token key rotation?",
        query_type="unique",
        expected_keywords=["90 days", "RS256"],
        description="JWT policy lookup",
    ),
    WorkloadQuery(
        query_id="Q-03",
        query_text="Calculate annual recurring revenue if monthly MRR is $25,000.",
        query_type="unique",
        expected_keywords=["300000", "300,000"],
        description="ARR multiplication",
    ),
    WorkloadQuery(
        query_id="Q-04",
        query_text="How many units of SKU-SWITCH-24 do we have in inventory?",
        query_type="unique",
        expected_keywords=["42", "US-West"],
        description="Inventory stock lookup",
    ),
    WorkloadQuery(
        query_id="Q-05",
        query_text="Inspect /var/log/syslog for database connection errors.",
        query_type="unique",
        expected_keywords=["exhausted", "timeout"],
        description="Syslog error diagnosis",
    ),
    WorkloadQuery(
        query_id="Q-06",
        query_text="What is the response SLA for primary on-call answering Sev-1 alerts?",
        query_type="unique",
        expected_keywords=["15 minutes"],
        description="Incident on-call SLA",
    ),
    WorkloadQuery(
        query_id="Q-07",
        query_text="What is the status and amount for order ORD-501?",
        query_type="unique",
        expected_keywords=["Shipped", "1450"],
        description="Order status check",
    ),
    WorkloadQuery(
        query_id="Q-08",
        query_text="Calculate gross profit margin percentage if revenue is $400,000 and COGS is $280,000.",
        query_type="unique",
        expected_keywords=["30%", "30"],
        description="Margin calculation",
    ),
    WorkloadQuery(
        query_id="Q-09",
        query_text="What are our documented API rate limits for Standard tier?",
        query_type="unique",
        expected_keywords=["60"],
        description="Rate limit check",
    ),
    WorkloadQuery(
        query_id="Q-10",
        query_text="What is the unit cost of SKU-UPS-3000 in inventory?",
        query_type="unique",
        expected_keywords=["1200", "1,200"],
        description="UPS battery cost check",
    ),
    WorkloadQuery(
        query_id="Q-11",
        query_text="Identify all customers in our database who have Churned status.",
        query_type="unique",
        expected_keywords=["Soylent Corp"],
        description="Churn filter",
    ),
    WorkloadQuery(
        query_id="Q-12",
        query_text="What is the sum of order amounts 1450.00 and 890.50?",
        query_type="unique",
        expected_keywords=["2340.5"],
        description="Order sum computation",
    ),
    WorkloadQuery(
        query_id="Q-13",
        query_text="What uptime availability percentage is guaranteed under Tier 2 SLA?",
        query_type="unique",
        expected_keywords=["99.95%"],
        description="SLA uptime percentage",
    ),
    WorkloadQuery(
        query_id="Q-14",
        query_text="What is the total order amount for order ORD-504?",
        query_type="unique",
        expected_keywords=["12500", "12,500"],
        description="High-value order query",
    ),
    WorkloadQuery(
        query_id="Q-15",
        query_text="Calculate 180 optical transceivers at $45.00 each.",
        query_type="unique",
        expected_keywords=["8100", "8,100"],
        description="Batch valuation",
    ),
    WorkloadQuery(
        query_id="Q-16",
        query_text="How many transceivers SKU-SFP-10G are in EU-Central warehouse?",
        query_type="unique",
        expected_keywords=["180", "EU-Central"],
        description="Warehouse stock check",
    ),
    WorkloadQuery(
        query_id="Q-17",
        query_text="What is the documented rate limit for Enterprise tier accounts?",
        query_type="unique",
        expected_keywords=["1000"],
        description="Enterprise rate limit",
    ),
    WorkloadQuery(
        query_id="Q-18",
        query_text="Calculate monthly server uptime percentage with 12 minutes downtime in 43,200 minutes.",
        query_type="unique",
        expected_keywords=["99.97"],
        description="Uptime calculation",
    ),

    # -----------------------------------------------------------------------
    # 2. Exact Repeat Queries (Simulating Cache Hot-Spots)
    # -----------------------------------------------------------------------
    WorkloadQuery(
        query_id="Q-19",
        query_text="List all Enterprise tier customers from our database.",
        query_type="exact_repeat",
        expected_keywords=["Acme Corp", "Umbrella Corp"],
        description="Exact repeat of Q-01",
    ),
    WorkloadQuery(
        query_id="Q-20",
        query_text="What is our official company policy on JWT token key rotation?",
        query_type="exact_repeat",
        expected_keywords=["90 days", "RS256"],
        description="Exact repeat of Q-02",
    ),
    WorkloadQuery(
        query_id="Q-21",
        query_text="Calculate annual recurring revenue if monthly MRR is $25,000.",
        query_type="exact_repeat",
        expected_keywords=["300000", "300,000"],
        description="Exact repeat of Q-03",
    ),
    WorkloadQuery(
        query_id="Q-22",
        query_text="How many units of SKU-SWITCH-24 do we have in inventory?",
        query_type="exact_repeat",
        expected_keywords=["42", "US-West"],
        description="Exact repeat of Q-04",
    ),
    WorkloadQuery(
        query_id="Q-23",
        query_text="Inspect /var/log/syslog for database connection errors.",
        query_type="exact_repeat",
        expected_keywords=["exhausted", "timeout"],
        description="Exact repeat of Q-05",
    ),
    WorkloadQuery(
        query_id="Q-24",
        query_text="What is the response SLA for primary on-call answering Sev-1 alerts?",
        query_type="exact_repeat",
        expected_keywords=["15 minutes"],
        description="Exact repeat of Q-06",
    ),

    # -----------------------------------------------------------------------
    # 3. Semantically Paraphrased Queries (Simulating Semantic Cache Hits)
    # -----------------------------------------------------------------------
    WorkloadQuery(
        query_id="Q-25",
        query_text="Show me all the customers who are in the Enterprise tier.",
        query_type="semantic_repeat",
        expected_keywords=["Acme Corp", "Umbrella Corp"],
        description="Semantic paraphrase of Q-01",
    ),
    WorkloadQuery(
        query_id="Q-26",
        query_text="Tell me the JWT signing algorithm and key rotation frequency policy.",
        query_type="semantic_repeat",
        expected_keywords=["90 days", "RS256"],
        description="Semantic paraphrase of Q-02",
    ),
    WorkloadQuery(
        query_id="Q-27",
        query_text="Compute annual recurring revenue assuming current MRR is $25,000.",
        query_type="semantic_repeat",
        expected_keywords=["300000", "300,000"],
        description="Semantic paraphrase of Q-03",
    ),
    WorkloadQuery(
        query_id="Q-28",
        query_text="Check stock level and warehouse for item SKU-SWITCH-24.",
        query_type="semantic_repeat",
        expected_keywords=["42", "US-West"],
        description="Semantic paraphrase of Q-04",
    ),
    WorkloadQuery(
        query_id="Q-29",
        query_text="Look at /var/log/syslog to find database connection pool errors.",
        query_type="semantic_repeat",
        expected_keywords=["exhausted", "timeout"],
        description="Semantic paraphrase of Q-05",
    ),
    WorkloadQuery(
        query_id="Q-30",
        query_text="What is the target response time for primary on-call Sev-1 incident alerts?",
        query_type="semantic_repeat",
        expected_keywords=["15 minutes"],
        description="Semantic paraphrase of Q-06",
    ),
]
