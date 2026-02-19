"""
FixFlow MCP Server — Community Knowledge Base for AI Agents.

Provides tools to search, read, create, and validate
technical KB cards via the Model Context Protocol.

Architecture:
  Cloud-Only MCP Server (SSE) ←→ Supabase Cloud DB (shared)
"""

from fastmcp import FastMCP
import json
import os
import re
import sys
import yaml
from typing import List, Dict, Optional

# ─── Configuration ───────────────────────────────────────────────
mcp = FastMCP("FixFlow")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "fixflow_kb")
INDEX_FILE = os.path.join(KB_DIR, "index.json")

MAX_CONTENT_LENGTH = 100 * 1024  # 100 KB limit
MAX_QUERY_LENGTH = 200           # Query length limit (DoS protection)

# Supabase Configuration (Strictly via env vars)
SUPABASE_URL = os.environ.get("FIXFLOW_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("FIXFLOW_SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.stderr.write("❌ ERROR: FIXFLOW_SUPABASE_URL or FIXFLOW_SUPABASE_KEY not set!\n")
    # In cloud mode, we cannot function without these
    if os.environ.get("TRANSPORT") == "sse":
        sys.exit(1)

# ─── Supabase Client (lazy init) ─────────────────────────────────

_supabase_client = None

def get_supabase():
    """Lazy-initialize Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        sys.stderr.write(f"⚠️ Supabase connection failed: {e}\n")
        return None


# ─── Helpers ─────────────────────────────────────────────────────

def load_kb_index() -> List[Dict]:
    """Cloud-only index loader."""
    # In cloud-only mode, we rely on search_cloud
    return []


def validate_kb_markdown(content: str) -> tuple[bool, str]:
    """
    Validate KB card Markdown content.
    Returns (is_valid, error_message).
    """
    if len(content) > MAX_CONTENT_LENGTH:
        return False, f"Content exceeds {MAX_CONTENT_LENGTH // 1024}KB limit."

    yaml_match = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not yaml_match:
        return False, "Missing YAML frontmatter (--- ... ---)."

    try:
        metadata = yaml.safe_load(yaml_match.group(1))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(metadata, dict):
        return False, "Frontmatter is not a valid YAML mapping."

    required_fields = ['kb_id', 'category', 'platform', 'criticality']
    missing = [f for f in required_fields if f not in metadata]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}."

    kb_id = metadata.get('kb_id', '')
    if not re.match(r'^[A-Z]+_[A-Z]+_\d+$', kb_id):
        return False, f"Invalid KB_ID format '{kb_id}'. Expected: PLATFORM_CATEGORY_NUMBER (e.g. WIN_TERM_042)."

    required_sections = {
        'Title (# ...)': r'#\s+',
        '🔍 This Is Your Problem If:': r'##\s+🔍\s+This Is Your Problem If',
        '✅ SOLUTION (copy-paste)': r'##\s+✅\s+SOLUTION\s+\(copy-paste\)',
        '✔️ Verification': r'##\s+✔️\s+Verification',
    }
    for name, pattern in required_sections.items():
        if not re.search(pattern, content):
            return False, f"Missing required section: '{name}'."

    if len(content) < 200:
        return False, "Content too short (minimum 200 characters)."

    return True, ""


def extract_tldr_fields(content: str) -> dict:
    """Extract quick_summary and fix_time from TL;DR block."""
    result = {"quick_summary": "", "fix_time": ""}

    tldr_match = re.search(r'\*\*TL;DR\*\*:\s*(.+)', content)
    if tldr_match:
        result["quick_summary"] = tldr_match.group(1).strip()

    fix_match = re.search(r'\*\*Fix Time\*\*:\s*([^|]+)', content)
    if fix_match:
        result["fix_time"] = fix_match.group(1).strip()

    return result


def save_to_local(kb_id: str, category: str, content: str, metadata: dict) -> tuple[bool, str]:
    """Disabled in Cloud-Only mode."""
    return True, "cloud-only"


def save_to_cloud(kb_id: str, content: str, metadata: dict) -> tuple[bool, str]:
    """Save KB card to Supabase cloud database."""
    sb = get_supabase()
    if not sb:
        return False, "Cloud unavailable"

    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Unknown Title"
    tldr = extract_tldr_fields(content)

    # Generate embedding for semantic search
    emb_text = f"{title} {tldr['quick_summary']} {' '.join(metadata.get('tags', []))}"
    embedding = _get_embedding(emb_text)

    row = {
        "kb_id": kb_id,
        "title": title,
        "category": metadata.get('category', '').lower(),
        "platform": metadata.get('platform', 'unknown'),
        "technologies": metadata.get('technologies', []),
        "complexity": metadata.get('complexity', 1),
        "criticality": metadata.get('criticality', 'low'),
        "tags": metadata.get('tags', []),
        "related_kb": metadata.get('related_kb', []),
        "quick_summary": tldr["quick_summary"],
        "fix_time": tldr["fix_time"],
        "content": content,
        "embedding": embedding,
    }

    try:
        sb.table("fixflow_kb").upsert(row, on_conflict="kb_id").execute()
        return True, "synced (cloud)"
    except Exception as e:
        return False, str(e)


def _get_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Supabase Edge Function 'embed'."""
    sb = get_supabase()
    if not sb or not text:
        return None
    try:
        res = sb.functions.invoke("embed", invoke_options={'body': {'input': text}})
        
        data = None
        if hasattr(res, 'data'):
             if isinstance(res.data, bytes):
                 data = json.loads(res.data.decode('utf-8'))
             elif isinstance(res.data, str):
                 data = json.loads(res.data)
             else:
                 data = res.data
        elif isinstance(res, dict):
            data = res
            
        if data and "embedding" in data:
            return data["embedding"]
            
    except Exception as e:
        sys.stderr.write(f"Embedding generation failed: {e}\n")
    return None


def search_cloud(query: str) -> List[Dict]:
    """Search KB cards in Supabase using server-side search function."""
    sb = get_supabase()
    if not sb:
        return []

    try:
        query_embedding = _get_embedding(query)
        result = sb.rpc("search_kb_cards", {
            "query_text": query,
            "query_embedding": query_embedding,
            "match_limit": 20
        }).execute()
        return result.data if result.data else []
    except Exception as e:
        sys.stderr.write(f"Cloud search error: {e}\n")
        return []


# ─── Tools ───────────────────────────────────────────────────────

@mcp.tool
def resolve_kb_id(query: str) -> List[Dict]:
    """Search the Knowledge Base to find a KB ID."""
    query = query[:MAX_QUERY_LENGTH].lower()
    return search_cloud(query)


@mcp.tool
def read_kb_doc(kb_id: str) -> str:
    """Read the full Markdown content of a KB card."""
    sb = get_supabase()
    if sb:
        try:
            result = sb.table("fixflow_kb") \
                .select("content") \
                .eq("kb_id", kb_id) \
                .eq("status", "published") \
                .single() \
                .execute()
            if result.data and result.data.get("content"):
                _track_event(kb_id, "view")
                return result.data["content"]
        except Exception as e:
            sys.stderr.write(f"Cloud read error: {e}\n")

    return f"Error: KB ID '{kb_id}' not found in cloud."


@mcp.tool
def save_kb_card(content: str, overwrite: bool = False) -> str:
    """Validate and save a new Knowledge Base card to cloud."""
    is_valid, error_msg = validate_kb_markdown(content)
    if not is_valid:
        return f"❌ Validation FAILED: {error_msg}"

    yaml_match = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    metadata = yaml.safe_load(yaml_match.group(1))
    kb_id = metadata['kb_id']

    cloud_ok, cloud_msg = save_to_cloud(kb_id, content, metadata)
    status = "✅" if cloud_ok else "❌"
    return f"{status} KB card '{kb_id}' — Cloud: {cloud_msg}"


def _track_event(kb_id: str, event: str) -> None:
    """Track a card usage event."""
    sb = get_supabase()
    if sb:
        try:
            sb.rpc("track_card_event", {"p_kb_id": kb_id, "p_event": event}).execute()
        except Exception:
            pass


# ─── Resources ───────────────────────────────────────────────────

@mcp.resource("tech-kb://stats")
def get_kb_stats() -> str:
    """Get Knowledge Base statistics from cloud."""
    sb = get_supabase()
    if not sb:
        return "☁️ Cloud: unavailable"

    try:
        cards = sb.table("fixflow_kb").select("kb_id, view_count, solved_count, failed_count").eq("status", "published").execute()
        if not cards.data:
            return "Knowledge Base is empty."

        cloud_count = len(cards.data)
        total_views = sum(c.get("view_count", 0) or 0 for c in cards.data)
        return f"📊 FixFlow Cloud Statistics\n☁️ Total Cards: {cloud_count}\n👁️ Total Views: {total_views}"
    except Exception as e:
        return f"⚠️ Cloud error: {e}"


# ─── Entry Point ─────────────────────────────────────────────────

def main():
    """CLI entry point for fixflow-cloud."""
    import argparse
    parser = argparse.ArgumentParser(description="FixFlow Cloud-Only Server")
    parser.add_argument("transport", choices=["stdio", "sse"], default="stdio", nargs="?")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.run(transport='sse', host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
