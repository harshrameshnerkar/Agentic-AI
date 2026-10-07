"""
web_search_tool.py
==================
Tool 1 of 4: Web Search Tool (Day 4 - Session 2)

Design Best Practices Implemented:
1. Clear Naming: 'web_search' clearly informs the model of its capability.
2. Model-Facing Description: Tells the model *when* to search (external live data, facts, news)
   and *what* it returns (structured list of title, snippet, url).
3. Typed & Validated Arguments:
   - query: non-empty string.
   - max_results: integer bounded between 1 and 10.
4. Error as Observation: Returns structured feedback on empty queries or zero results
   instead of raising exceptions, allowing the model to adapt and retry.
"""

from typing import List, Dict, Any
import re

# Comprehensive knowledge base simulating web search results across tech, science, and enterprise
_WEB_INDEX = [
    {
        "title": "Python 3.12 Release Notes - Python Documentation",
        "url": "https://docs.python.org/3/whatsnew/3.12.html",
        "snippet": "Python 3.12 introduces isolated subinterpreters with separate GILs, improved error messages with suggestions, and faster comprehension execution.",
        "keywords": ["python", "python 3.12", "gil", "subinterpreters", "release notes"],
    },
    {
        "title": "Google Gemini 2.0 & 3.5 Flash Model Overview",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "snippet": "Gemini 3.5 Flash offers superior multimodal reasoning, high throughput, and native tool calling with low latency across developer workflows.",
        "keywords": ["gemini", "gemini 3.5", "flash", "google", "ai model", "tool calling"],
    },
    {
        "title": "PostgreSQL 16 High-Performance Logical Replication",
        "url": "https://www.postgresql.org/docs/16/logical-replication.html",
        "snippet": "PostgreSQL 16 allows logical decoding on standbys, concurrent parallel streaming of large in-progress transactions, and enhanced pgoutput performance.",
        "keywords": ["postgresql", "postgres 16", "logical replication", "pgoutput", "database"],
    },
    {
        "title": "Enterprise Cloud Migration Best Practices (AWS / GCP)",
        "url": "https://cloud.google.com/architecture/migration-to-gcp",
        "snippet": "Planning phased cutovers with CDC (Change Data Capture) using Debezium and Kafka minimizes downtime to under 5 minutes during production maintenance windows.",
        "keywords": ["cloud migration", "cdc", "debezium", "cutover", "database migration"],
    },
    {
        "title": "Weather Forecast: New York City (NYC)",
        "url": "https://weather.com/weather/today/l/New+York+NY",
        "snippet": "Current conditions in NYC: 64°F (18°C), Partly Cloudy. Winds NW at 8 mph. Humidity 52%. High of 68°F expected this afternoon.",
        "keywords": ["weather", "nyc", "new york", "temperature", "forecast"],
    },
    {
        "title": "Stock Market Summary: Tech Equities Today",
        "url": "https://finance.yahoo.com/tech-index",
        "snippet": "Tech shares rallied today with the NASDAQ gaining +1.4%. Semiconductor and AI infrastructure leaders saw increased trading volumes.",
        "keywords": ["stock", "market", "nasdaq", "shares", "finance", "equities"],
    },
]


def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Searches the web for recent articles, documentation, facts, and live information.

    Args:
        query: The search keywords or question string.
        max_results: Maximum number of search results to return (1 to 10).
    """
    # 1. Argument Validation
    if not isinstance(query, str) or not query.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'query' argument must be a non-empty string. Please provide search keywords.",
        }

    if not isinstance(max_results, int) or max_results < 1 or max_results > 10:
        max_results = min(max(1, int(max_results) if isinstance(max_results, (int, float)) else 3), 10)

    # 2. Search Execution with Keyword Scoring
    clean_query = query.lower().strip()
    query_terms = set(re.findall(r"\w+", clean_query))

    matches = []
    for item in _WEB_INDEX:
        score = 0
        item_text = (item["title"] + " " + item["snippet"]).lower()
        
        # Check phrase match
        if clean_query in item_text:
            score += 5

        # Check keyword matches
        for kw in item["keywords"]:
            if kw in clean_query or clean_query in kw:
                score += 3

        # Check individual term matches
        item_words = set(re.findall(r"\w+", item_text))
        common_words = query_terms & item_words
        score += len(common_words)

        if score > 0:
            matches.append((score, item))

    # Sort by relevance score descending
    matches.sort(key=lambda x: x[0], reverse=True)
    top_results = [item for _, item in matches[:max_results]]

    # 3. Return as Observation
    if not top_results:
        return {
            "status": "no_results",
            "query": query,
            "results_count": 0,
            "message": f"No web search results found matching '{query}'. Try refining keywords or searching for broader terms.",
        }

    return {
        "status": "success",
        "query": query,
        "results_count": len(top_results),
        "results": [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"],
            }
            for r in top_results
        ],
    }


if __name__ == "__main__":
    print("=== Testing web_search Tool ===")
    res1 = web_search("What is new in Python 3.12?")
    print("Search 'Python 3.12':", res1["status"], f"({res1['results_count']} results)")

    res_err = web_search("")
    print("Search empty query (Error Observation):", res_err)

    res_none = web_search("quantum levitation unicycle racing 1920")
    print("Search no results (No Results Observation):", res_none["status"], "-", res_none["message"])
