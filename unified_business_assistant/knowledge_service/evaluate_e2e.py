import sys
import json
import time
import urllib.request
from neon_client import NeonDBClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"


def http_get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ensure_server_running():
    try:
        http_get("/health")
        return
    except Exception:
        pass

    import threading
    import uvicorn
    from app import app

    thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": 8000, "log_level": "error"},
        daemon=True,
    )
    thread.start()
    for _ in range(30):
        time.sleep(0.5)
        try:
            http_get("/health")
            return
        except Exception:
            pass


def run_evaluation():
    ensure_server_running()
    results = {}
    print("Running Knowledge Service E2E tests...")

    print("\n1. Health check (/health)")
    time.sleep(0.5)
    try:
        health = http_get("/health")
        assert health.get("status") == "healthy", f"Unexpected status: {health}"
        assert health.get("neon_connected") is True, "Neon not connected"
        print("   PASS")
        results["health_check"] = {"passed": True, "data": health}
    except Exception as e:
        print(f"   FAIL: {e}")
        results["health_check"] = {"passed": False, "error": str(e)}

    print("\n2. Stats & catalog (/stats, /documents)")
    try:
        stats = http_get("/stats")
        catalog = http_get("/documents")
        chunk_count = stats.get("chroma_indexed_chunks")
        doc_count = stats.get("documents_in_catalog")
        neon_chunks = int(stats.get("neon_table_chunks", 0))
        assert chunk_count >= 1500, f"Low Chroma chunk count: {chunk_count}"
        assert doc_count == 50, f"Expected 50 docs, got {doc_count}"
        assert neon_chunks >= 1500, f"Low Neon chunk count: {neon_chunks}"
        assert len(catalog.get("documents", [])) == 50, "Catalog length mismatch"
        print(f"   PASS (Chroma: {chunk_count}, Neon: {neon_chunks}, Docs: {doc_count})")
        results["telemetry_consistency"] = {"passed": True, "stats": stats}
    except Exception as e:
        print(f"   FAIL: {e}")
        results["telemetry_consistency"] = {"passed": False, "error": str(e)}

    print("\n3. Search contract & provenance (/search)")
    test_queries = [
        "maternity leave duration and policy",
        "whistleblower complaint reporting procedure",
        "prevention of sexual harassment redressal committee",
    ]
    search_passed = 0
    for q in test_queries:
        res = http_post("/search", {"question": q, "top_k": 3, "score_threshold": 0.35})
        items = res.get("results", [])
        provenance_valid = all(
            "source_file" in r and "page" in r and "score" in r and "chunk_id" in r
            for r in items
        )
        scores = [r["score"] for r in items]
        scores_sorted = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)) if len(scores) > 1 else True

        if items and provenance_valid and scores_sorted:
            search_passed += 1
            print(f"   PASS: '{q}' ({len(items)} results)")
        else:
            print(f"   FAIL: '{q}' -> {res}")
    results["semantic_search"] = {"passed": search_passed == len(test_queries), "passed_count": search_passed}

    print("\n4. Multi-turn chat reformulation (/chat)")
    test_session = f"eval_session_{int(time.time())}"
    chat_passed = 0
    t1 = http_post("/chat", {"message": "What is the policy for supplier code of conduct at Jayaswal Neco?", "session_id": test_session})
    if len(t1.get("citations", [])) > 0 and len(t1.get("answer", "")) > 50:
        print(f"   PASS Turn 1 ({len(t1['citations'])} citations)")
        chat_passed += 1
    else:
        print(f"   FAIL Turn 1: {t1}")

    t2 = http_post("/chat", {"message": "What are their core responsibilities under ESG?", "session_id": test_session})
    reformulated = t2.get("standalone_question", "")
    if ("jayaswal" in reformulated.lower() or "supplier" in reformulated.lower()) and len(t2.get("citations", [])) > 0:
        print(f"   PASS Turn 2 (Reformulated: '{reformulated}')")
        chat_passed += 1
    else:
        print(f"   FAIL Turn 2: '{reformulated}'")
    results["conversational_memory"] = {"passed": chat_passed == 2, "turn2_standalone": reformulated}

    print("\n5. Out-of-scope handling (/chat)")
    oos_res = http_post("/chat", {"message": "What is the capital of France?", "session_id": test_session})
    if oos_res.get("no_match") is True and len(oos_res.get("citations", [])) == 0:
        print("   PASS (no_match=True)")
        results["guardrail_rejection"] = {"passed": True}
    else:
        print(f"   FAIL: {oos_res}")
        results["guardrail_rejection"] = {"passed": False}

    print("\n6. Neon chat log persistence")
    db = NeonDBClient()
    history = db.get_chat_history(test_session)
    if len(history) >= 2:
        print(f"   PASS ({len(history)} rows logged)")
        results["neon_audit_log"] = {"passed": True, "rows": len(history)}
    else:
        print(f"   FAIL ({len(history)} rows found)")
        results["neon_audit_log"] = {"passed": False}

    all_passed = all(r.get("passed", False) for r in results.values())
    print(f"\nOverall status: {'ALL PASSED' if all_passed else 'FAILED'}")
    return results


if __name__ == "__main__":
    run_evaluation()
