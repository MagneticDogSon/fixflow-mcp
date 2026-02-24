
import os
import json
import uuid
import sys
import time
from supabase import create_client

# Config (matches server.py)
SUPABASE_URL = os.environ.get("FIXFLOW_SUPABASE_URL", "https://hbwrduqbmuupxhtndrta.supabase.co")
SUPABASE_KEY = os.environ.get("FIXFLOW_SUPABASE_KEY", "")

def log(msg):
    with open("test_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def test_semantic_search():
    if os.path.exists("test_log.txt"): os.remove("test_log.txt")
    
    log("🔌 Connecting to Supabase...")
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        log(f"❌ Connect error: {e}")
        return

    # 1. Test Edge Function
    text = "Docker container fails to start on Apple Silicon M1 due to architecture mismatch"
    log(f"🧠 Generating embedding for: '{text[:40]}...'")
    
    try:
        # Call Edge Function
        res = sb.functions.invoke("embed", invoke_options={'body': {'input': text}})
        
        # Parse result
        embedding = None
        if hasattr(res, 'data'): # Using updated client usually returns object
             log(f"Response data type: {type(res.data)}")
             if isinstance(res.data, bytes):
                 data = json.loads(res.data.decode('utf-8'))
             elif isinstance(res.data, str):
                 data = json.loads(res.data)
             else:
                 data = res.data
             embedding = data.get("embedding")
        elif isinstance(res, dict):
            embedding = res.get("embedding")

        if not embedding:
            log("❌ Failed to get embedding")
            if hasattr(res, 'text'): log(f"Raw response: {res.text}")
            return
            
        log(f"✅ Embedding generated! Length: {len(embedding)} (Dimensions)")
        log(f"   Preview: {embedding[:3]}...")

    except Exception as e:
        log(f"❌ Error invoking function: {e}")
        import traceback
        log(traceback.format_exc())
        return

    # 2. Insert Test Card
    kb_id = f"TEST_SEARCH_{uuid.uuid4().hex[:4].upper()}"
    log(f"💾 Saving test card: {kb_id}")
    
    row = {
        "kb_id": kb_id,
        "title": "M1 Mac Docker Exec Format Error",
        "category": "docker",
        "content": "Full content about exec format error...",
        "status": "published", 
        "quick_summary": "Use platform linux/amd64 or buildx",
        "tags": ["docker", "m1", "arm64"],
        "embedding": embedding # Save the vector!
    }
    
    try:
        sb.table("fixflow_kb").insert(row).execute()
        log("✅ Card saved locally in cloud DB.")
    except Exception as e:
        log(f"❌ Error saving card: {e}")
        return

    # 3. Perform Semantic Search
    search_query = "why docker crash on macbook pro m1 chip" # Different words, same meaning
    log(f"🔍 Searching for: '{search_query}'")
    
    # Generate vector for query
    try:
        q_res = sb.functions.invoke("embed", invoke_options={'body': {'input': search_query}})
        q_emb = None
        
        if hasattr(q_res, 'data'):
             if isinstance(q_res.data, bytes):
                 q_data = json.loads(q_res.data.decode('utf-8'))
             elif isinstance(q_res.data, str):
                 q_data = json.loads(q_res.data)
             else:
                 q_data = q_res.data
             q_emb = q_data.get("embedding")
        
        if q_emb:
            log("✅ Query embedded.")
            
            # RPC Call
            rpc_res = sb.rpc("search_kb_cards", {
                "query_text": search_query,
                "query_embedding": q_emb,
                "match_limit": 5
            }).execute()
            
            found = False
            for match in (rpc_res.data or []):
                log(f"   • {match['kb_id']} (sim: {match['similarity']:.4f}) - {match['title']}")
                if match['kb_id'] == kb_id:
                    found = True
            
            if found:
                log("🎯 SUCCESS! Semantic search found our card despite different wording.")
            else:
                log("⚠️  Card not found. Similarity threshold might be strict or index not ready.")
                
            # Cleanup
            log(f"🧹 Cleaning up {kb_id}...")
            sb.table("fixflow_kb").delete().eq("kb_id", kb_id).execute()
        else:
            log("❌ Failed to embed search query")

    except Exception as e:
        log(f"❌ Search error: {e}")

if __name__ == "__main__":
    test_semantic_search()
