"""
Day 12 - Session 3: General Benchmark Dataset for Catastrophic Forgetting Checks
================================================================================
Contains 20 curated general-domain reasoning, math, Python logic, and linguistic
tasks used to evaluate whether LoRA fine-tuning on the narrow SRE task degrades
general foundational model capabilities.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class GeneralBenchmarkCase:
    test_id: str
    domain: str
    prompt: str
    expected_answer: str
    validation_keywords: List[str] = field(default_factory=list)
    description: str = ""


GENERAL_BENCHMARK_CASES: List[GeneralBenchmarkCase] = [
    # -------------------------------------------------------------------------
    # DOMAIN 1: MATHEMATICAL REASONING & ARITHMETIC (GSM8K Style)
    # -------------------------------------------------------------------------
    GeneralBenchmarkCase(
        test_id="GEN-01",
        domain="MATH",
        prompt="A cluster of 12 worker nodes processes 450 requests per minute each. If 3 nodes go offline for maintenance, how many total requests per minute can the remaining cluster process?",
        expected_answer="4050 requests per minute",
        validation_keywords=["4050", "4,050", "remaining 9"],
        description="Multi-step rate calculation with node subset reduction",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-02",
        domain="MATH",
        prompt="If a data store consumes 256 GB with a 15% monthly compound growth rate, calculate the approximate storage needed after 2 months. Round to one decimal place.",
        expected_answer="338.6 GB (or approximately 338 to 339 GB)",
        validation_keywords=["338", "339"],
        description="Compound growth percentage calculation",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-03",
        domain="MATH",
        prompt="Calculate the average response time if 80% of requests complete in 20ms and the remaining 20% complete in 120ms.",
        expected_answer="40ms",
        validation_keywords=["40", "40ms"],
        description="Weighted average latency computation",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-04",
        domain="MATH",
        prompt="A server has 64 GB of RAM. The OS reserves 4 GB, each application worker thread requires 750 MB, and 12 GB is dedicated to buffer cache. What is the maximum number of worker threads that can be spawned?",
        expected_answer="64 threads (48 GB available / 0.75 GB = 64)",
        validation_keywords=["64", "64 threads"],
        description="Memory allocation and integer thread bound",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-05",
        domain="MATH",
        prompt="If an SLA requires 99.95% uptime across a 30-day month (43,200 total minutes), what is the maximum permissible downtime in minutes?",
        expected_answer="21.6 minutes",
        validation_keywords=["21.6", "21.6 minutes", "22"],
        description="High-availability SLA error budget calculation",
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 2: PYTHON PROGRAMMING & ALGORITHM LOGIC
    # -------------------------------------------------------------------------
    GeneralBenchmarkCase(
        test_id="GEN-06",
        domain="PYTHON_LOGIC",
        prompt="Write a Python function `is_palindrome(s: str) -> bool` that ignores case and non-alphanumeric characters.",
        expected_answer="def is_palindrome(s):\n    clean = [c.lower() for c in s if c.isalnum()]\n    return clean == clean[::-1]",
        validation_keywords=["isalnum", "lower", "[::-1]"],
        description="String normalization and palindrome reversal check",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-07",
        domain="PYTHON_LOGIC",
        prompt="Explain what the time complexity of searching in a balanced Binary Search Tree (BST) versus an unsorted list is, using Big-O notation.",
        expected_answer="O(log n) for balanced BST, O(n) for unsorted list",
        validation_keywords=["o(log n)", "o(n)", "binary search"],
        description="Algorithmic complexity comparison",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-08",
        domain="PYTHON_LOGIC",
        prompt="What is the difference between shallow copy and deep copy in Python? Provide an example using a nested list.",
        expected_answer="Shallow copy constructs a new compound object and inserts references to the original objects; deep copy recursively copies nested objects.",
        validation_keywords=["reference", "recursive", "copy.deepcopy", "nested"],
        description="Memory reference semantics in object copying",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-09",
        domain="PYTHON_LOGIC",
        prompt="Explain how a Python generator function differs from a standard function and what the `yield` keyword does.",
        expected_answer="Generators yield values lazily one at a time and preserve local state between iterations without storing the full sequence in memory.",
        validation_keywords=["yield", "lazy", "iterator", "memory"],
        description="Generator state suspension and memory efficiency",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-10",
        domain="PYTHON_LOGIC",
        prompt="What does the GIL (Global Interpreter Lock) in CPython do and how does it affect CPU-bound multithreaded execution?",
        expected_answer="The GIL ensures only one thread executes Python bytecode at a time, preventing multi-core speedup for pure CPU-bound multithreading.",
        validation_keywords=["one thread", "bytecode", "cpu-bound", "concurrency"],
        description="CPython memory safety and concurrency concurrency semantics",
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 3: LOGICAL REASONING & GENERAL COMPUTER SCIENCE
    # -------------------------------------------------------------------------
    GeneralBenchmarkCase(
        test_id="GEN-11",
        domain="REASONING",
        prompt="All SSDs are persistent storage devices. Some persistent storage devices use NVMe protocol. Does it logically follow that all SSDs use NVMe protocol?",
        expected_answer="No, it does not follow logically. Some SSDs use SATA or SAS protocols.",
        validation_keywords=["no", "does not follow", "invalid", "sata"],
        description="Categorical syllogism and logical validity",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-12",
        domain="REASONING",
        prompt="Explain the core difference between TCP and UDP in terms of connection state, ordering, and delivery guarantees.",
        expected_answer="TCP is connection-oriented, guarantees in-order delivery and packet acknowledgement. UDP is connectionless, unordered, and best-effort.",
        validation_keywords=["connection-oriented", "connectionless", "order", "guarantee"],
        description="Transport layer networking fundamentals",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-13",
        domain="REASONING",
        prompt="In relational databases, what does the ACID acronym stand for, and what does the 'I' represent?",
        expected_answer="Atomicity, Consistency, Isolation, Durability. The 'I' stands for Isolation.",
        validation_keywords=["atomicity", "consistency", "isolation", "durability"],
        description="Database transaction integrity guarantees",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-14",
        domain="REASONING",
        prompt="Explain the difference between symmetric and asymmetric encryption, mentioning public/private key pairs and shared secrets.",
        expected_answer="Symmetric uses a single shared secret key for both encryption and decryption. Asymmetric uses a public key for encryption and a distinct private key for decryption.",
        validation_keywords=["shared key", "public key", "private key", "asymmetric"],
        description="Cryptographic primitives and key exchange principles",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-15",
        domain="REASONING",
        prompt="What is the CAP theorem in distributed systems, and why can a distributed system only guarantee two of Consistency, Availability, and Partition Tolerance simultaneously?",
        expected_answer="In the presence of a network partition (P), a distributed system must choose between returning consistent but potentially delayed/failed data (CP) or returning stale available data (AP).",
        validation_keywords=["consistency", "availability", "partition", "network partition"],
        description="Distributed systems trade-off theorem",
    ),

    # -------------------------------------------------------------------------
    # DOMAIN 4: LINGUISTIC REASONING & SUMMARIZATION
    # -------------------------------------------------------------------------
    GeneralBenchmarkCase(
        test_id="GEN-16",
        domain="LINGUISTICS",
        prompt="Summarize the following paragraph in exactly one sentence: 'Machine learning algorithms construct a mathematical model based on sample training data in order to make predictions or decisions without being explicitly programmed to perform the task. These models are widely utilized in speech recognition, computer vision, and autonomous vehicle navigation.'",
        expected_answer="Machine learning builds mathematical models from training data to autonomously perform complex tasks such as speech, vision, and navigation without hardcoded rules.",
        validation_keywords=["machine learning", "models", "data", "predictions"],
        description="Concise single-sentence condensation",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-17",
        domain="LINGUISTICS",
        prompt="Identify the passive voice in the sentence: 'The database migration was completed by the engineering team before sunrise.' Rewrite it in active voice.",
        expected_answer="Passive: 'was completed by'. Active: 'The engineering team completed the database migration before sunrise.'",
        validation_keywords=["engineering team completed", "active", "passive"],
        description="Grammar voice identification and transformation",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-18",
        domain="LINGUISTICS",
        prompt="Explain what an oxymoron is and provide two common real-world examples in English.",
        expected_answer="An oxymoron is a figure of speech combining contradictory terms. Examples include 'deafening silence' and 'bittersweet'.",
        validation_keywords=["contradictory", "figure of speech", "silence", "bittersweet"],
        description="Literary device definition and exemplar identification",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-19",
        domain="LINGUISTICS",
        prompt="Analyze the tone and intent of this message: 'I have reviewed your pull request. The architectural layout is thoroughly well-considered, but please address the memory leak on line 42 prior to merging.'",
        expected_answer="Constructive, professional, appreciative yet firm regarding quality gate requirements.",
        validation_keywords=["constructive", "professional", "feedback", "code review"],
        description="Pragmatic tone and intent classification",
    ),
    GeneralBenchmarkCase(
        test_id="GEN-20",
        domain="LINGUISTICS",
        prompt="Extract the key entities (Organization, Role, Location, Date) from: 'On October 14, 2026, CloudScale Inc. appointed Elena Rostova as Chief Information Security Officer at their Zurich headquarters.'",
        expected_answer="Organization: CloudScale Inc., Role: Chief Information Security Officer, Person: Elena Rostova, Location: Zurich, Date: October 14, 2026.",
        validation_keywords=["cloudscale", "elena", "ciso", "zurich", "october"],
        description="Named Entity Recognition (NER) structured extraction",
    ),
]
