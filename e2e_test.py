"""
E2E Test for FixFlow MCP Server — standalone (no server.py import)
Tests: Edge Function → Save with embedding → Search → Read → Track → Cleanup
Uses only stdlib (urllib, json, ssl) + supabase-py for DB ops.
"""
import json, os, sys, time, ssl, urllib.request, urllib.error, traceback

SUPABASE_URL = "https://hbwrduqbmuupxhtndrta.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhid3JkdXFibXV1cHhodG5kcnRhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNzQxNDQsImV4cCI6MjA4Njg1MDE0NH0.t37Ag0pQHuYdyflfviST69ZX8R2FTNCdLzhpN2tt_s0"
RESULT_FILE = "e2e_result.txt"
try:
    CTX = ssl.create_default_context()
except Exception:
    CTX = ssl._create_unverified_context()

log_lines = []
passed = 0
failed = 0

def log(msg):
    log_lines.append(msg)
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

def api(method, path, body=None):
    """Call Supabase REST/RPC/Functions API."""
    url = f"{SUPABASE_URL}{path}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body_err[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        log(f"  ✅ PASS — {detail}")
        passed += 1
    else:
        log(f"  ❌ FAIL — {detail}")
        failed += 1

# ═══════════════════════════════════════════════
log("=" * 55)
log("🧪 FixFlow MCP Server — E2E Test (standalone)")
log(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
log("=" * 55)

# ── TEST 1: Supabase REST API ──
log("\n[TEST 1] Supabase REST API connectivity...")
res = api("GET", "/rest/v1/fixflow_kb?select=kb_id&limit=1")
check("supabase_api", not isinstance(res, dict) or "error" not in res,
      f"got response: {type(res).__name__}")

# ── TEST 2: Edge Function 'embed' ──
log("\n[TEST 2] Edge Function 'embed' (gte-small 384d)...")
embed_res = api("POST", "/functions/v1/embed", {"input": "Docker crash on Apple Silicon M1"})
embedding = None
if isinstance(embed_res, dict) and "embedding" in embed_res:
    embedding = embed_res["embedding"]
    check("embed", len(embedding) == 384, f"{len(embedding)} dimensions, first3={embedding[:3]}")
else:
    check("embed", False, f"response: {str(embed_res)[:200]}")

# ── TEST 3: Save test card (with embedding) ──
log("\n[TEST 3] Save test card to DB...")
test_card = {
    "kb_id": "E2E_TEST_001",
    "title": "E2E Test Card — Automated Validation",
    "category": "testing",
    "platform": "agnostic",
    "technologies": ["python", "pytest"],
    "complexity": 2,
    "criticality": "low",
    "tags": ["e2e", "automated", "test"],
    "related_kb": [],
    "quick_summary": "Automated test card for E2E validation",
    "fix_time": "0 min",
    "content": "# E2E Test Card\n\n> **TL;DR**: Automated test\n> **Fix Time**: 0 min\n\n## Solution\n```bash\necho test\n```",
    "status": "published",
}
if embedding:
    test_card["embedding"] = embedding

# Use PostgREST upsert
headers_upsert = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}
req = urllib.request.Request(
    f"{SUPABASE_URL}/rest/v1/fixflow_kb",
    data=json.dumps(test_card).encode(),
    headers=headers_upsert,
    method="POST"
)
try:
    with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
        check("save", resp.status in (200, 201), f"HTTP {resp.status}")
except urllib.error.HTTPError as e:
    body_err = e.read().decode("utf-8", errors="replace")
    check("save", False, f"HTTP {e.code}: {body_err[:200]}")

# ── TEST 4: Verify embedding stored ──
log("\n[TEST 4] Verify embedding stored in DB...")
row = api("GET", "/rest/v1/fixflow_kb?kb_id=eq.E2E_TEST_001&select=kb_id,title,embedding")
if isinstance(row, list) and len(row) > 0:
    has_emb = row[0].get("embedding") is not None
    check("embedding_stored", has_emb, f"embedding={'YES' if has_emb else 'NO'}")
else:
    check("embedding_stored", False, f"card not found: {row}")

# ── TEST 5: FTS Search via RPC ──
log("\n[TEST 5] Full-text search via RPC...")
search_res = api("POST", "/rest/v1/rpc/search_kb_cards", {
    "query_text": "E2E automated test",
    "match_limit": 5
})
if isinstance(search_res, list):
    found = any(r.get("kb_id") == "E2E_TEST_001" for r in search_res)
    check("fts_search", found, f"found={'YES' if found else 'NO'} in {len(search_res)} results")
else:
    check("fts_search", False, f"RPC error: {str(search_res)[:200]}")

# ── TEST 6: Vector Search via RPC ──
log("\n[TEST 6] Semantic (vector) search via RPC...")
if embedding:
    # Search with a DIFFERENT query but same meaning
    diff_query_emb = api("POST", "/functions/v1/embed", {"input": "end-to-end testing validation script"})
    if isinstance(diff_query_emb, dict) and "embedding" in diff_query_emb:
        vec_search = api("POST", "/rest/v1/rpc/search_kb_cards", {
            "query_text": "end-to-end testing validation script",
            "query_embedding": diff_query_emb["embedding"],
            "match_limit": 5
        })
        if isinstance(vec_search, list):
            vec_found = any(r.get("kb_id") == "E2E_TEST_001" for r in vec_search)
            if vec_found:
                sim = next((r.get("similarity", 0) for r in vec_search if r.get("kb_id") == "E2E_TEST_001"), 0)
                check("vector_search", True, f"found with similarity={sim:.4f}")
            else:
                check("vector_search", False, f"not found in {len(vec_search)} results: {[r.get('kb_id') for r in vec_search]}")
        else:
            check("vector_search", False, f"RPC error: {str(vec_search)[:200]}")
    else:
        check("vector_search", False, "could not embed search query")
else:
    log("  ⏭️ SKIP — no embedding available")

# ── TEST 7: Track event via RPC ──
log("\n[TEST 7] Track view event via RPC...")
track_res = api("POST", "/rest/v1/rpc/track_card_event", {
    "p_kb_id": "E2E_TEST_001",
    "p_event": "view"
})
check("track_event", track_res is not None and not (isinstance(track_res, dict) and "error" in track_res),
      f"result: {str(track_res)[:100]}")

# ── TEST 8: Verify view_count incremented ──
log("\n[TEST 8] Verify view_count incremented...")
row2 = api("GET", "/rest/v1/fixflow_kb?kb_id=eq.E2E_TEST_001&select=view_count")
if isinstance(row2, list) and len(row2) > 0:
    vc = row2[0].get("view_count", 0)
    check("view_count", vc and vc > 0, f"view_count={vc}")
else:
    check("view_count", False, f"not found: {row2}")

# ── CLEANUP ──
log("\n[CLEANUP] Removing test card...")
try:
    del_req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/fixflow_kb?kb_id=eq.E2E_TEST_001",
        headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"},
        method="DELETE"
    )
    urllib.request.urlopen(del_req, context=CTX, timeout=10)
    log("  ☁️ Cloud: deleted")
except Exception as e:
    log(f"  ⚠️ Cleanup error: {e}")

# ── SUMMARY ──
log(f"\n{'='*55}")
total = passed + failed
log(f"🏁 RESULT: {passed}/{total} passed, {failed} failed")
if failed == 0:
    log("🎉 ALL TESTS PASSED!")
else:
    log(f"⚠️  {failed} test(s) need attention")
log("=" * 55)
