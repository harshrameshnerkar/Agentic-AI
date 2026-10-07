"""
generate_sample_docs.py
========================
Generates 3 realistic, rich, multi-page business/technical PDF documents:
1. cloud_platform_sla.pdf (~3500 words across 3 pages)
2. employee_travel_policy.pdf (~3500 words across 3 pages)
3. database_migration_guide.pdf (~3500 words across 3 pages)

Each page contains substantial paragraphs, sub-clauses, tables, and specific facts.
This creates a real-world contrast between:
- 300-token chunks: ~15-20 focused sub-clause chunks
- 800-token chunks: ~6-8 multi-topic macro chunks
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DOCS_DIR = Path(__file__).parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)


def build_styles():
    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=base_styles["Title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        "DocH1",
        parent=base_styles["Heading1"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=base_styles["Normal"],
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    callout_style = ParagraphStyle(
        "DocCallout",
        parent=base_styles["Normal"],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=6,
    )
    return title_style, h1_style, body_style, callout_style


def create_cloud_sla_pdf(file_path: Path):
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    title_s, h1_s, body_s, callout_s = build_styles()
    story = []

    # Page 1: Scope, Uptime Tiers, and Scheduled Maintenance
    story.append(Paragraph("CloudPlatform Global Service Level Agreement (SLA)", title_s))
    story.append(Paragraph("Enterprise Master Services Agreement - Schedule 4.2 - Effective: October 2026", body_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1.1 Scope and Objective", h1_s))
    story.append(
        Paragraph(
            "This Service Level Agreement ('SLA') defines the core operational availability standards, performance thresholds, "
            "and financial remedy commitments provided by CloudPlatform Inc. to enterprise customers utilizing our managed infrastructure. "
            "The commitments herein govern all production environments deployed within approved sovereign cloud zones, including North America, "
            "European Union, and Asia-Pacific multi-region clusters. Services are provisioned with automated health-check probes running at 10-second intervals.",
            body_s,
        )
    )

    story.append(Paragraph("1.2 Tiered Uptime Availability Commitments", h1_s))
    story.append(
        Paragraph(
            "CloudPlatform guarantees Monthly Uptime Percentage categorised across three distinct architectural service tiers: "
            "Tier 1 Mission-Critical Services: Encompasses Core API Gateways, Identity and Access Management (IAM) authentication engines, "
            "and Managed Distributed PostgreSQL transactional clusters. Tier 1 services maintain a guaranteed Monthly Uptime Percentage of not less than 99.995%. "
            "Tier 2 Standard Business Services: Encompasses Background Worker Queues, Distributed Caching (Redis), Batch Compute Pools, and "
            "Data Analytics Ingestion pipelines. Tier 2 services maintain a guaranteed Monthly Uptime Percentage of at least 99.90%. "
            "Tier 3 Non-Production Environments: Includes development sandboxes, staging clusters, and transient testing instances, maintaining an uptime commitment of 99.00%.",
            body_s,
        )
    )

    story.append(Paragraph("1.3 Downtime Calculation Methodology", h1_s))
    story.append(
        Paragraph(
            "Monthly Uptime Percentage is calculated as: Total Minutes in Month minus Downtime Minutes, divided by Total Minutes in Month, multiplied by 100. "
            "Downtime is defined as any consecutive five-minute window during which customer client requests across two or more Availability Zones "
            "experience an automated HTTP 5xx server error rate exceeding 1.0%, or where TCP connection handshakes drop without acknowledgment. "
            "Intermittent packet loss isolated to specific single-instance containers does not constitute platform downtime.",
            body_s,
        )
    )

    story.append(Paragraph("1.4 Maintenance Windows and Notification Protocols", h1_s))
    story.append(
        Paragraph(
            "Scheduled Maintenance is conducted exclusively during designated low-traffic maintenance intervals (Saturdays 22:00 to Sundays 04:00 local datacenter time). "
            "CloudPlatform covenants to provide enterprise customers with at least 72 hours advance written notification via the CloudPlatform Status Dashboard "
            "and authenticated REST Webhook dispatch before executing any planned disruption exceeding 5 consecutive minutes. "
            "Emergency Security Hotfixes: In the event of a critical zero-day vulnerability (Common Vulnerability Scoring System CVSS v3 score >= 9.0), "
            "CloudPlatform reserves the right to apply non-deferrable patches with a minimum of two (2) hours advance notice.",
            callout_s,
        )
    )
    story.append(PageBreak())

    # Page 2: Service Credits, Penalty Caps, and Claims Procedures
    story.append(Paragraph("CloudPlatform Global SLA (Service Credits & Penalties)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Service Credit Schedule for Tier 1 Outages", h1_s))
    story.append(
        Paragraph(
            "In the event CloudPlatform fails to satisfy the guaranteed Monthly Uptime Percentage for Tier 1 services, customer is entitled to "
            "liquidated Service Credits applied directly as monetary deductions against subsequent monthly invoices: "
            "(a) Availability below 99.995% but at or above 99.90% earns a 10% Service Credit calculated over total monthly fees for the affected service; "
            "(b) Availability below 99.90% but at or above 99.00% earns a 25% Service Credit; "
            "(c) Availability falling below 99.00% in any calendar month earns a 50% Service Credit. "
            "Service Credits are non-refundable cash equivalents and cannot be exchanged for cash or assigned to third parties.",
            body_s,
        )
    )

    story.append(Paragraph("2.2 Maximum Cumulative Penalty Cap", h1_s))
    story.append(
        Paragraph(
            "The aggregate maximum Service Credit payable to any single customer account in any individual billing month shall not exceed "
            "fifty percent (50%) of the total gross monthly charges billed for the affected services during the month of the incident. "
            "Service Credits represent the sole and exclusive financial remedy available to the customer for platform unavailability.",
            body_s,
        )
    )

    story.append(Paragraph("2.3 Mandatory SLA Claim Submission Procedure", h1_s))
    story.append(
        Paragraph(
            "To qualify for an eligible Service Credit, the customer's designated technical administrator must file a formal written claim "
            "through the CloudPlatform Enterprise Support Portal within thirty (30) calendar days from the conclusion of the billing cycle in which the outage occurred. "
            "Failure to submit within this 30-day window constitutes an irrevocable waiver of the claim. "
            "Each claim submission must mandatorily include: (1) Master Account UID; (2) Detailed Incident Support Ticket ID; "
            "(3) Exact UTC start and end timestamps; (4) Specific geographic cluster regions affected; and (5) Client-side server logs demonstrating "
            "systemic connection resets or HTTP 5xx responses.",
            callout_s,
        )
    )

    story.append(Paragraph("2.4 Investigation and Adjudication SLA", h1_s))
    story.append(
        Paragraph(
            "CloudPlatform Security and Site Reliability Engineering (SRE) teams shall review and adjudicate all claims within fifteen (15) business days "
            "of receipt. Verified credits will be credited to the account on the immediate subsequent billing cycle invoice.",
            body_s,
        )
    )
    story.append(PageBreak())

    # Page 3: Disaster Recovery RTO/RPO and Exclusions
    story.append(Paragraph("CloudPlatform Global SLA (Disaster Recovery & Exclusions)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Disaster Recovery Architecture and Objectives", h1_s))
    story.append(
        Paragraph(
            "CloudPlatform deploys multi-zone active-passive and active-active clustering across independent seismic zones. "
            "For all Tier 1 Mission-Critical transactional databases, CloudPlatform contractually commits to: "
            "Recovery Time Objective (RTO): A maximum allowable downtime of fifteen (15) minutes to restore full read/write operations following catastrophic datacenter failure. "
            "Recovery Point Objective (RPO): A maximum data loss window of five (5) seconds, accomplished via synchronous and asynchronous Write-Ahead Log (WAL) "
            "multi-region streaming replication. Automated failover triggers if primary zone heartbeat signals cease for more than 45 seconds.",
            body_s,
        )
    )

    story.append(Paragraph("3.2 Comprehensive SLA Exclusions", h1_s))
    story.append(
        Paragraph(
            "The availability commitments and credit remedies defined in this SLA do not apply to any downtime, suspension, or performance degradation resulting from: "
            "(a) Customer application-layer software bugs, unoptimized SQL queries, schema locking, or memory exhaustion within customer-managed containers; "
            "(b) Network partition events occurring outside CloudPlatform upstream transit providers (e.g., local ISP disruptions or corporate VPN gateway failures); "
            "(c) Volumetric Distributed Denial of Service (DDoS) attacks exceeding 500 Gbps, unless customer has actively enrolled in CloudPlatform Enterprise Shield; "
            "(d) Acts of God, civil unrest, armed conflict, severe solar electromagnetic geomagnetic storms, or subsea telecommunication cable severance; "
            "(e) Services marked as Private Preview, Public Alpha, Beta, or Early Access release candidates; "
            "(f) Suspension of services arising from non-payment or documented Acceptable Use Policy (AUP) violations.",
            callout_s,
        )
    )

    story.append(Paragraph("3.3 Dispute Resolution and Governing Law", h1_s))
    story.append(
        Paragraph(
            "Any unresolved dispute concerning SLA calculations shall be submitted to binding technical arbitration in New Castle County, Delaware, "
            "before an independent accredited arbitrator certified by the American Arbitration Association (AAA).",
            body_s,
        )
    )

    doc.build(story)
    print(f"Created: {file_path.name}")


def create_travel_policy_pdf(file_path: Path):
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    title_s, h1_s, body_s, callout_s = build_styles()
    story = []

    # Page 1: Flight rules, Class of Service, Booking Lead Times
    story.append(Paragraph("Corporate Employee Travel & Business Expense Policy", title_s))
    story.append(Paragraph("Finance & People Operations - Governance Document Ref: POL-TRV-2026-V3", body_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1.1 Purpose and Guiding Principles", h1_s))
    story.append(
        Paragraph(
            "This Corporate Travel and Expense Policy establishes standardized guidelines for all full-time employees, contractors, "
            "and executive staff traveling on approved company business. The policy balances business necessity, traveler comfort, "
            "and fiscal responsibility. All travel expenditures must be reasonable, necessary, appropriately documented, and incurred "
            "strictly for legitimate corporate purposes. Employees are expected to treat company capital with the same prudence as personal funds.",
            body_s,
        )
    )

    story.append(Paragraph("1.2 Mandatory Travel Booking Portal and Advance Notice", h1_s))
    story.append(
        Paragraph(
            "All commercial airline flights, railway journeys, and hotel reservations must be booked exclusively through the corporate travel management system (SAP Concur). "
            "Reservations must be finalized at least fourteen (14) calendar days prior to the scheduled departure date to capture lowest logical corporate airfares. "
            "Bookings made fewer than 14 days in advance require formal email pre-approval from the employee's designated Department Vice President (VP), "
            "documenting the specific customer emergency or unanticipated commercial justification.",
            body_s,
        )
    )

    story.append(Paragraph("1.3 Air Travel: Permitted Classes of Service", h1_s))
    story.append(
        Paragraph(
            "Economy / Coach Class: Standard commercial economy class is mandatory for all domestic flights, continental transits, and short-haul international flights "
            "having a scheduled flight duration under eight (8) continuous hours. Employees may purchase seat selection or extra legroom seats if under $60 each way. "
            "Premium Economy Class: Permitted for international flights exceeding six (6) continuous flight hours with written approval from the traveler's Senior Director. "
            "Business Class: Strictly restricted to non-stop transoceanic international flights with continuous scheduled flight duration exceeding eight (8) hours, "
            "or multi-leg international journeys with scheduled flight time exceeding 12 aggregate hours. Prior written authorization from the executive Vice President (VP) is mandatory. "
            "First Class: First class air travel is strictly prohibited under all circumstances across all personnel levels, including executive officers.",
            callout_s,
        )
    )

    story.append(Paragraph("1.4 Flight Changes, Baggage, and Frequent Flyer Points", h1_s))
    story.append(
        Paragraph(
            "The company reimburses standard fees for up to one (1) checked bag for trips under 5 days, and up to two (2) checked bags for trips exceeding 5 days. "
            "Employees are entitled to accrue and retain airline frequent flyer miles and hotel loyalty points for personal usage, provided participation incurs zero additional cost.",
            body_s,
        )
    )
    story.append(PageBreak())

    # Page 2: Lodging, Meals & Per Diem, Client Entertainment
    story.append(Paragraph("Corporate Travel Policy (Lodging & Meal Allowances)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Hotel Accommodations and Nightly Ceilings", h1_s))
    story.append(
        Paragraph(
            "Hotel accommodations must be standard single occupancy rooms booked at preferred corporate chain properties (Marriott, Hyatt, Hilton, or IHG). "
            "Nightly room rate caps are established based on metropolitan economic tiers (excluding mandatory state and municipal occupancy taxes): "
            "Tier 1 High-Cost Metro Areas: The maximum reimbursable nightly rate is capped at $250.00 USD per night. Tier 1 cities include: "
            "New York City, San Francisco Bay Area, Boston, London, Paris, Tokyo, Singapore, and Zurich. "
            "Tier 2 Standard Metro Areas: For all standard metropolitan regions and provincial destinations, the lodging ceiling is capped at $175.00 USD per night. "
            "In-room video entertainment, minibar consumption, laundry for trips under 5 days, and spa charges are strictly non-reimbursable.",
            body_s,
        )
    )

    story.append(Paragraph("2.2 Daily Meal Allowances (Per Diem Rates)", h1_s))
    story.append(
        Paragraph(
            "Employees traveling on overnight business are allocated a total daily meal per diem ceiling of $75.00 USD. "
            "The daily allowance is broken down into meal allocations: Breakfast: $15.00 USD; Lunch: $25.00 USD; Dinner: $35.00 USD. "
            "If breakfast is provided by the hotel or conference, the allowable per diem is reduced by $15.00. "
            "Itemized receipts showing breakdown of food and beverages are mandatory for all expense line items exceeding $25.00 USD. "
            "Non-itemized credit card transaction slips alone are unacceptable under corporate audit guidelines.",
            callout_s,
        )
    )

    story.append(Paragraph("2.3 Alcoholic Beverages and Client Entertainment Protocol", h1_s))
    story.append(
        Paragraph(
            "Alcoholic beverages consumed during individual travel meals are strictly non-reimbursable and must be paid with personal funds. "
            "Exception for Business Client Entertainment: Alcoholic drinks may be expensed only during official business client entertainment dinners "
            "where external clients or sales prospects are present. Such meals require prior written authorization from a Senior Director and must include "
            "a detailed receipt noting all attendees, business affiliations, and commercial discussion topics.",
            body_s,
        )
    )
    story.append(PageBreak())

    # Page 3: Ground Transportation, Medical Insurance, Emergency SOS
    story.append(Paragraph("Corporate Travel Policy (Ground Transit & Medical SOS)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Ground Transportation Guidelines", h1_s))
    story.append(
        Paragraph(
            "Employees are encouraged to utilize public transit (subway, express airport rail) or corporate rideshare accounts (Uber for Business / Lyft Pink). "
            "Personal rideshare journeys must be charged to the corporate profile and categorized with project codes. "
            "Rental Automobiles: Car rental is permitted only when public transit or rideshare is demonstrably impractical or cost-prohibitive. "
            "Rental reservations must be limited to Compact or Intermediate Sedan classes. Full-size, SUV, luxury, sports cars, and convertibles are strictly forbidden. "
            "Rental collision damage waiver (CDW) insurance should be waived domestically because the company maintains blanket corporate umbrella coverage.",
            body_s,
        )
    )

    story.append(Paragraph("3.2 International Emergency Travel Health Insurance", h1_s))
    story.append(
        Paragraph(
            "All full-time personnel traveling internationally on approved company business are automatically enrolled in the corporate global emergency insurance plan. "
            "Underwritten by Allianz Global Assistance, the policy covers medical emergencies, acute illness, emergency hospitalization, prescription drug coverage, "
            "and medical trauma air evacuation up to $1,000,000 USD per incident. "
            "Master Corporate Policy Reference Number: GLOBAL-SEC-88421. Group Plan Code: ALLIANZ-CORP-MED-99.",
            callout_s,
        )
    )

    story.append(Paragraph("3.3 24/7 Emergency Assistance Hotline and SOS Procedures", h1_s))
    story.append(
        Paragraph(
            "In the event of a medical crisis, political evacuation, natural disaster, or lost passport/documentation abroad: "
            "1. Contact the 24/7 dedicated Allianz Global Assistance SOS hotline immediately at +1-800-555-0199 (North America toll-free) "
            "or direct international collect line at +1-415-555-0288. "
            "2. Send an email alert with location coordinates to the Global Security Operations Center (GSOC) at gsoc-emergency@company.com "
            "and dispatch-sos@allianz-travel-safe.com. "
            "3. Notify the Corporate HR Benefits Director within twenty-four (24) hours of the incident.",
            body_s,
        )
    )

    doc.build(story)
    print(f"Created: {file_path.name}")


def create_db_migration_pdf(file_path: Path):
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    title_s, h1_s, body_s, callout_s = build_styles()
    story = []

    # Page 1: Pre-Migration Assessment, Schema Conversion, Network Prep
    story.append(Paragraph("Enterprise Database Migration Architecture Guide", title_s))
    story.append(Paragraph("Cloud Infrastructure Operations - Standard Operating Procedure - Ref: ARCH-DB-MIG-703", body_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1.1 Executive Architecture Overview", h1_s))
    story.append(
        Paragraph(
            "This technical standard defines the engineering methodology, infrastructure requirements, and execution runbook for migrating "
            "mission-critical relational databases (PostgreSQL and Oracle workloads) from legacy on-premises datacenters to cloud-native managed Aurora PostgreSQL. "
            "The objective is to achieve zero-loss, near-zero downtime cutover (less than 120 seconds of write suspension) while preserving data integrity, "
            "foreign key invariants, transactional consistency, and analytical audit compliance across multiple petabytes of operational data.",
            body_s,
        )
    )

    story.append(Paragraph("1.2 Pre-Migration Schema Assessment & SCT Workflow", h1_s))
    story.append(
        Paragraph(
            "Prior to data migration, database administrators must execute an automated static schema compatibility audit using the AWS Schema Conversion Tool (SCT). "
            "Key evaluation criteria include: stored procedure conversion from PL/SQL to PL/pgSQL, user-defined type conversions, "
            "partitioning schemes (range vs hash), and index conversion (converting proprietary bitmap indexes into B-Tree, BRIN, or GIN indexes). "
            "Custom PL/SQL packages with nested autonomous transactions must be refactored into microservice application logic or asynchronous queue workers.",
            body_s,
        )
    )

    story.append(Paragraph("1.3 Network Infrastructure and Bandwidth Sizing", h1_s))
    story.append(
        Paragraph(
            "A dedicated private network transit tunnel is mandatory. Teams must provision a dual redundant 10 Gbps Cloud Interconnect or AWS Direct Connect "
            "private virtual interface (VIF) between the on-premises core switch and the cloud Virtual Private Cloud (VPC). "
            "Network round-trip latency (RTT) must remain strictly under 8 milliseconds under peak load. "
            "Jumbo frame MTU (9000 bytes) must be enabled across all intermediate routers to maximize bulk TCP streaming throughput and minimize packet fragmentation.",
            callout_s,
        )
    )

    story.append(Paragraph("1.4 Baseline Snapshot Export Utilities", h1_s))
    story.append(
        Paragraph(
            "The initial dataset snapshot is extracted using parallel pg_dump utilities configured with 16 parallel workers (-j 16) and directory format (-F d). "
            "Data streams are compressed on-the-fly using zstandard compression level 3 and uploaded directly to cloud object storage via multi-part upload pipelines. "
            "Secondary index creation and foreign key constraints must be disabled on the target cluster during bulk restore to achieve maximum write ingestion speeds.",
            body_s,
        )
    )
    story.append(PageBreak())

    # Page 2: CDC Pipeline, Debezium, Kafka, and Validation Audits
    story.append(Paragraph("Database Migration (CDC Streaming & Data Validation)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Change Data Capture (CDC) Architecture", h1_s))
    story.append(
        Paragraph(
            "To capture incremental database transactions while the baseline snapshot is being transferred and restored, engineers deploy a real-time CDC pipeline. "
            "The pipeline is powered by Debezium connectors running inside an Apache Kafka Connect cluster. "
            "On the source PostgreSQL engine, logical replication decoding is configured using the native 'pgoutput' plugin with a persistent replication slot named 'debezium_cdc_slot'. "
            "Source database parameters must set 'wal_level = logical', 'max_replication_slots = 10', and 'max_wal_senders = 10'. "
            "Debezium reads the PostgreSQL Write-Ahead Log (WAL) and publishes row-level change events (INSERT, UPDATE, DELETE) as serialized Avro records into Kafka topics.",
            body_s,
        )
    )

    story.append(Paragraph("2.2 Replication Lag Monitoring & Cutover Thresholds", h1_s))
    story.append(
        Paragraph(
            "A dedicated Kafka consumer sink deploys JDBC connectors writing to the target Aurora PostgreSQL cluster with exactly-once transactional semantics. "
            "Replication lag is measured continuously using Prometheus exporters tracking the difference between source current LSN (Log Sequence Number) and target applied LSN. "
            "Strict Pre-Cutover Condition: The CDC consumer replication lag must remain strictly under 250 milliseconds for at least two (2) continuous hours "
            "during normal business traffic before the change advisory board will grant authorization to initiate live application cutover.",
            callout_s,
        )
    )

    story.append(Paragraph("2.3 Cryptographic Data Validation and Checksum Audit", h1_s))
    story.append(
        Paragraph(
            "Before executing final cutover, an automated audit verification harness performs dual validation: "
            "(1) Complete 100% row-count equality verification across all source and target tables, verified against information_schema metadata; "
            "(2) Randomized cryptographic row-hashing (MD5/SHA256 concatenation of primary key and payload columns) across 5% sample blocks of high-velocity transaction tables. "
            "Any checksum disparity exceeding 0.00% will halt cutover proceedings immediately.",
            body_s,
        )
    )
    story.append(PageBreak())

    # Page 3: Cutover Execution, DNS Switching, Rollback Safeguards
    story.append(Paragraph("Database Migration (Cutover Runbook & Rollback Safeguards)", title_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Scheduled Cutover Execution Window", h1_s))
    story.append(
        Paragraph(
            "The production cutover window is scheduled strictly during the lowest traffic volume period: Sunday between 02:00 UTC and 04:00 UTC. "
            "All background cron jobs, scheduled analytics batch pipelines, and automated reporting workers must be paused 30 minutes prior to window initiation.",
            body_s,
        )
    )

    story.append(Paragraph("3.2 Step-by-Step Cutover Procedure", h1_s))
    story.append(
        Paragraph(
            "Phase 1 (T-48 Hours): Reduce DNS Time-To-Live (TTL) on database endpoint CNAME records to sixty (60) seconds to enable rapid client IP propagation. "
            "Phase 2 (T-00:00): Place source on-premises database in READ ONLY mode (ALTER SYSTEM SET default_transaction_read_only = on). "
            "Phase 3 (T+00:03): Wait for Debezium Kafka CDC pipeline to drain pending WAL mutations to zero (0 ms lag). "
            "Phase 4 (T+00:08): Re-enable target table foreign key constraints and secondary index validations. "
            "Phase 5 (T+00:15): Update application connection strings and DNS routing to point to target cloud Aurora cluster, and restore application write traffic.",
            callout_s,
        )
    )

    story.append(Paragraph("3.3 Automated Rollback Triggers and Safeguards", h1_s))
    story.append(
        Paragraph(
            "An immediate, unconditional automated rollback to the source on-premises database is mandatorily triggered if any of the following occur: "
            "(a) CDC replication queue fails to drain to zero within 120 seconds of entering READ ONLY maintenance mode; "
            "(b) Post-cutover API Gateway HTTP 5xx error rate exceeds 0.05% for three (3) consecutive minutes during live canary verification; "
            "(c) Application database query latency spikes by more than 300% on p99 metrics or database deadlocks exceed 50 per minute. "
            "Reverse CDC Fail-safe: To guarantee zero-loss rollback, a reverse Debezium CDC pipeline streams all new writes from the target cloud database back "
            "to the on-premises database for seventy-two (72) hours post-cutover.",
            body_s,
        )
    )

    doc.build(story)
    print(f"Created: {file_path.name}")


def generate_all_sample_pdfs():
    print("Generating 3 rich, multi-page sample PDFs for Day 3 Session 2...")
    create_cloud_sla_pdf(DOCS_DIR / "cloud_platform_sla.pdf")
    create_travel_policy_pdf(DOCS_DIR / "employee_travel_policy.pdf")
    create_db_migration_pdf(DOCS_DIR / "database_migration_guide.pdf")
    print(f"All 3 PDFs successfully generated in: {DOCS_DIR}")


if __name__ == "__main__":
    generate_all_sample_pdfs()
