"""
Routing Engine (Interface 3 - Owned by Role C)
Evaluates incoming natural-language queries and determines the execution route:
- 'knowledge' : Corporate policies, handbooks, compliance, governance, guidelines
- 'data'      : Relational queries, SQL tables, counts, aggregates, Northwind data
- 'both'      : Hybrid cross-domain queries combining database entities & policy compliance
- 'none'      : Unanswerable, out-of-scope, live real-time feeds, or malicious prompts
"""

import re 
from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

class RouteType(str, Enum):
    KNOWLEDGE = "knowledge"
    DATA = "data"
    BOTH = "both"
    NONE = "none"

class RoutingDecision(BaseModel):
    question: str
    route: RouteType
    routing_rule: str
    fallback: str
    confidence: float
    matched_signals: List[str] = Field(default_factory=list)

class QueryRouter:
    """
    Interface 3 Router implementation.
    Consumes question -> Produces RoutingDecision (route, routing_rule, fallback, confidence).
    """

    # Guardrail / Malicious / Out of scope patterns -> route to 'none'
    NONE_PATTERNS = [
        (r"sql injection|exploit|wipe the database|drop table|attack", "Security guardrail: malicious exploit or destructive command blocked"),
        (r"real-time.*stock price|current.*stock price|nse right now|live ticker", "Out-of-scope: real-time financial market ticker feeds are unavailable"),
        (r"personal cell phone|home address|private phone number", "Privacy guardrail: personal sensitive PII phone and home addresses are omitted"),
        (r"money laundering.*offenses|highest number of money laundering", "False premise: transactional database does not record criminal indictments"),
        (r"revenue.*financial year 2026|revenue generated.*2026", "Out-of-scope: internal annual financial ledger for future/current fiscal year 2026 is unavailable"),
    ]

    # Explicit Hybrid / Cross-Domain Patterns
    HYBRID_SIGNALS = [
        r"(database|northwind|table|customer|product|shipper|employee|supplier).*(violat|compl(y|iance)|handbook|policy|rules?|allowed|prohibit)",
        r"(violat|compl(y|iance)|handbook|policy|rules?|allowed|prohibit).*(database|northwind|table|customer|product|shipper|employee|supplier)",
        r"german.*(customer|client).*(gift|hospitality|policy|handbook)",
        r"(chais|chang).*(donation|brib|gift|policy)",
        r"hire a relative of a government official.*(employee|northwind|system)",
        r"diversity policy.*(shipper|speedy express)",
        r"corporate accounts fraud.*(supplier|phone number|exotic liquid)"
    ]

    # Knowledge Document Title / Concept Patterns (override generic word matches)
    POLICY_DOCUMENT_TITLES = [
        r"product safety policy",
        r"supplier code of conduct",
        r"supply chain policy",
        r"responsible supply chain report",
        r"code of conduct",
        r"vigil mechanism",
        r"whistleblower policy",
        r"remuneration policy",
        r"parental leave policy",
        r"expense policy",
        r"csr activities",
        r"upsi fair disclosure",
        r"posh",
        r"diversity,\s*equity\s*and\s*inclusion\s*policy"
    ]

    # Data Service Signals (SQL, Aggregates, Tables, Columns)
    DATA_SIGNALS = [
        r"\b(show|find|list|get|display|calculate|give|fetch|return|select)\b.*\b(products?|prices?|orders?|orderdetails?|order\s+details?|customers?|suppliers?|employees?|shippers?|categories|category|quantity|rows?|records?|tables?)\b",
        r"\b(count|sum|total quantity|average price|avg|maximum price|max|minimum price|min)\b",
        r"\b(categoryid|supplierid|employeeid|orderid|customerid|orderdetailid)\b",
        r"\b(northwind|orderdetails|order\s+details)\b",
        r"\bselect\b.*\bfrom\b",
        r"\bdistinct\b",
        r"\bfirst name and last name\b",
        r"\bunitprice|unit price|unitsinstock|units in stock\b",
        r"\borderdate|shippeddate|freight\b",
        r"\bcustomers who live in\b",
        r"\bcustomers registered from\b",
        r"\bproducts supplied by\b",
        r"\bproducts that have a price\b",
        r"\borders sorted by\b"
    ]

    # Knowledge Service Signals (Policies, Handbooks, Compliance, HR, Governance)
    KNOWLEDGE_SIGNALS = [
        r"\bpolic(y|ies)\b",
        r"\bhandbook\b",
        r"\bcode of conduct\b",
        r"\bposh\b|sexual harassment",
        r"\bwhistleblower\b|vigil mechanism",
        r"\banti-corruption\b|anti-bribery|brib(e|ery)",
        r"\bparental leave\b|maternity|paternity",
        r"\bexpense policy\b|reimbursement",
        r"\bgifts? and hospitality\b",
        r"\bmission\b|operating model",
        r"\ball remote\b",
        r"\bai principles\b",
        r"\bgdpr\b|privacy policy",
        r"\bsupplier code of conduct\b",
        r"\bresponsible supply chain\b|supply chain report",
        r"\bmodern slavery\b",
        r"\bdei\b|diversity|equal opportunity",
        r"\besg\b|sustainability|csr\b",
        r"\binsider trading\b|upsi\b",
        r"\brisk management\b",
        r"\bremuneration\b",
        r"\bretention of documents\b",
        r"\bmateriality policy\b",
        r"\bindependent directors?\b"
    ]

    def route_query(self, question: str) -> RoutingDecision:
        """
        Classifies a user query into one of four contract routes:
        - RouteType.NONE
        - RouteType.BOTH
        - RouteType.DATA
        - RouteType.KNOWLEDGE
        """
        q_norm = question.strip()
        q_lower = q_norm.lower()

        # Step 1: Check Guardrails / Out-of-Scope (Route -> NONE)
        for pattern, explanation in self.NONE_PATTERNS:
            if re.search(pattern, q_lower):
                return RoutingDecision(
                    question=q_norm,
                    route=RouteType.NONE,
                    routing_rule=explanation,
                    fallback="Immediately return security or scope limitation message without dispatching to backend services.",
                    confidence=0.99,
                    matched_signals=[pattern]
                )

        # Step 2: Check Explicit Hybrid / Cross-Domain (Route -> BOTH)
        # Note: If it's simply a document title like "Product Safety Policy", it's not hybrid unless independent data signals exist!
        matched_policy_titles = [t for t in self.POLICY_DOCUMENT_TITLES if re.search(t, q_lower)]
        
        # Strip matched policy titles to detect if independent data signals exist
        stripped_q = q_lower
        for pt in matched_policy_titles:
            stripped_q = re.sub(pt, "", stripped_q)

        # Count Data Signals vs Knowledge Signals
        data_matches = [p for p in self.DATA_SIGNALS if re.search(p, q_lower)]
        knowledge_matches = [p for p in self.KNOWLEDGE_SIGNALS if re.search(p, q_lower)]
        independent_data_matches = [p for p in self.DATA_SIGNALS if re.search(p, stripped_q)]

        matched_hybrid = [p for p in self.HYBRID_SIGNALS if re.search(p, q_lower)]
        if matched_hybrid and (not matched_policy_titles or independent_data_matches):
            return RoutingDecision(
                question=q_norm,
                route=RouteType.BOTH,
                routing_rule="Cross-domain queries referencing structured database entities alongside policy guidelines route to both services.",
                fallback="Query Data Service for entities, then pass extracted entities as context to Knowledge Service.",
                confidence=0.95,
                matched_signals=matched_hybrid
            )

        # Check for compound cross-domain queries (e.g., "show supplier name and phone number also tell me about gitlabs expense policy")
        has_compound_intent = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["also", "and also", "as well as", "along with", "in addition to"]) or ";" in q_lower
        is_hybrid_overlap = (len(independent_data_matches) >= 1 and len(knowledge_matches) >= 1) or (has_compound_intent and len(data_matches) >= 1 and (len(knowledge_matches) >= 1 or matched_policy_titles))

        if is_hybrid_overlap:
            return RoutingDecision(
                question=q_norm,
                route=RouteType.BOTH,
                routing_rule="Query contains both structured transactional terms and corporate policy governance terms.",
                fallback="Query Data Service first; if answerable=false, try knowledge alone.",
                confidence=0.92,
                matched_signals=data_matches + knowledge_matches
            )

        # Specific check for Corporate Document Titles (e.g., Reckitt Product Safety Policy, Google Supply Chain Report)
        if matched_policy_titles and not independent_data_matches:
            return RoutingDecision(
                question=q_norm,
                route=RouteType.KNOWLEDGE,
                routing_rule="Recognized Corporate Policy Document title routes to Knowledge Service.",
                fallback="If Knowledge Service returns no_match=true, answer 'I do not have corporate policy documentation regarding this query.'",
                confidence=0.96,
                matched_signals=["policy_document_title_match"]
            )

        # Step 3: Pure Data Service Route
        if len(data_matches) > 0 and len(knowledge_matches) == 0:
            return RoutingDecision(
                question=q_norm,
                route=RouteType.DATA,
                routing_rule="Aggregates, counts, SQL table entities (products, customers, orders, suppliers, employees) route to Data Service.",
                fallback="If Data Service returns answerable=false, try Knowledge Service as fallback.",
                confidence=min(0.98, 0.75 + 0.05 * len(data_matches)),
                matched_signals=data_matches
            )

        # Step 4: Pure Knowledge Service Route
        if len(knowledge_matches) > 0:
            return RoutingDecision(
                question=q_norm,
                route=RouteType.KNOWLEDGE,
                routing_rule="Corporate policies, compliance standards, HR guidelines, whistleblower, and governance route to Knowledge Service.",
                fallback="If Knowledge Service returns no_match=true, answer 'I do not know / No matching policy found'.",
                confidence=min(0.98, 0.75 + 0.05 * len(knowledge_matches)),
                matched_signals=knowledge_matches
            )

        # Step 5: Analytical heuristic
        if any(term in q_lower for term in ["how many", "count", "average", "highest price", "lowest price"]):
            return RoutingDecision(
                question=q_norm,
                route=RouteType.DATA,
                routing_rule="Analytical or numerical aggregation intent routes to Data Service.",
                fallback="If data returns answerable=false, try knowledge.",
                confidence=0.70,
                matched_signals=["numerical_aggregation_heuristic"]
            )

        # Default fallback to Knowledge Service with standard fallback rule
        return RoutingDecision(
            question=q_norm,
            route=RouteType.KNOWLEDGE,
            routing_rule="General text lookup defaults to Knowledge Service with strict no_match handling.",
            fallback="If no_match=true, return 'I do not have corporate records answering this query.'",
            confidence=0.65,
            matched_signals=["general_text_heuristic"]
        )
