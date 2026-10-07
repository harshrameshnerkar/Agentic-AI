# Day 11 Session 1: Agentic & Adaptive RAG Benchmark Summary

- **Generated**: 2026-10-06 11:11:22 UTC
- **Benchmark Objective**: Compare Multi-Way Query Router (Vector vs SQL vs No-Retrieval) against Naive Always-Retrieve Baseline.
- **Evaluation Set**: 20 Multi-Category Operational Enterprise Queries.

## Executive Head-to-Head Comparison

| Metric | Naive Always-Retrieve | Adaptive Agentic RAG | Performance Gain |
|---|---|---|---|
| **Answer Pass Rate** | **30.0%** (6/20) | **100.0%** (20/20) | **+70.0% Accuracy** |
| **Routing Accuracy** | 0.0% (Unrouted) | **100.0%** (20/20) | **100% Precision** |
| **p50 Latency (Median)** | 0.12 ms | **0.10 ms** | **Faster** |
| **Mean Tokens / Query** | 273.8 tokens | **182.8 tokens** | **33.2% Token Reduction** |
| **Cost / 1,000 Queries** | $0.0390 | **$0.0260** | **33.2% Cost Savings** |
| **Context Pollution** | 35.0% | **0.0%** | **Completely Eliminated** |

## Pillar Category Breakdown

| Category | Query Count | Naive Pass Rate | Adaptive Pass Rate | Naive Latency | Adaptive Latency |
|---|---|---|---|---|---|
| `Vector_Search` | 6 | 100% | **100%** | 0.14 ms | **0.16 ms** |
| `SQL_Database` | 6 | 0% | **100%** | 0.11 ms | **0.53 ms** |
| `No_Retrieval` | 5 | 0% | **100%** | 0.09 ms | **0.07 ms** |
| `Multi_Hop` | 3 | 0% | **100%** | 0.17 ms | **0.29 ms** |

## Key Architectural Findings
1. **The SQL Blindspot in Naive RAG**: Naive RAG achieved **0% accuracy on SQL queries** because unstructured documentation chunks cannot answer live aggregations (counts, sums, inventory levels). Routing to SQL produced **100% accuracy**.
2. **Context Pollution Elimination**: On greetings, general programming, and math queries, Naive RAG polluted the prompt with unrelated policy documents. Adaptive RAG recognized **No-Retrieval** intent, eliminating latency and token waste.
3. **Corrective RAG (CRAG) Precision**: Low-confidence semantic queries triggered the Retrieve-Grade-Rewrite loop, expanding acronyms and focusing keywords before synthesis.
4. **Multi-Hop Fusion**: Hybrid questions successfully merged live database metrics with governing corporate policies.
