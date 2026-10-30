import json
import sys
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def test_services():
    print("1. Knowledge Service (Port 8000)")
    k_health = requests.get("http://127.0.0.1:8000/health", timeout=5).json()
    print("Health:", json.dumps(k_health))

    k_q = "What is the procedure for reporting workplace harassment?"
    print(f"\nPOST /search: '{k_q}'")
    search_res = requests.post(
        "http://127.0.0.1:8000/search",
        json={"question": k_q, "top_k": 3, "score_threshold": 0.3},
        timeout=10,
    )
    search_data = search_res.json()
    print(f"Status: {search_res.status_code} | no_match: {search_data.get('no_match')} | Results: {len(search_data.get('results', []))}")
    for i, p in enumerate(search_data.get("results", []), 1):
        print(f"  [{i}] {p.get('source_file')} (p. {p.get('page')}) | {p.get('chunk_id')} | score={p.get('score'):.4f}")

    print(f"\nPOST /chat: '{k_q}'")
    chat_res = requests.post("http://127.0.0.1:8000/chat", json={"message": k_q, "top_k": 3}, timeout=10)
    chat_data = chat_res.json()
    print(f"Status: {chat_res.status_code}")
    print("Answer:", chat_data.get("answer", ""))

    print("\n2. Data Service (Port 8002)")
    d_health = requests.get("http://127.0.0.1:8002/health", timeout=15).json()
    print("Health:", json.dumps(d_health))

    queries = [
        "What are the names and prices of all products in the 'Beverages' category that cost more than $20?",
        "List the top 5 customers who have spent the most total money, along with the total amount they have spent.",
        "What is the company maternity leave duration in weeks?",
    ]
    for q in queries:
        print(f"\nPOST /query: '{q}'")
        res = requests.post("http://127.0.0.1:8002/query", json={"question": q, "limit": 5}, timeout=10).json()
        print(f"Answerable: {res.get('answerable')} | SQL: {res.get('sql')} | Error: {res.get('error')}")
        for row in res.get("rows", [])[:5]:
            print(" ", row)


if __name__ == "__main__":
    test_services()
