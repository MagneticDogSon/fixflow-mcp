"""
FixFlow MCP Server — Community Knowledge Base for AI Agents.

Provides tools to search, read, create, and validate
technical KB cards via the Model Context Protocol.

Architecture:
  Local MCP Server (stdio) ←→ Supabase Cloud DB (shared)
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

# Supabase Configuration (via env vars for security)
# Support both FIXFLOW_ and TECHDOCS_ prefixes for backward compatibility
SUPABASE_URL = os.environ.get("FIXFLOW_SUPABASE_URL", os.environ.get("TECHDOCS_SUPABASE_URL", "https://hbwrduqbmuupxhtndrta.supabase.co"))
SUPABASE_KEY = os.environ.get("FIXFLOW_SUPABASE_KEY", os.environ.get("TECHDOCS_SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhid3JkdXFibXV1cHhodG5kcnRhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNzQxNDQsImV4cCI6MjA4Njg1MDE0NH0.t37Ag0pQHuYdyflfviST69ZX8R2FTNCdLzhpN2tt_s0"))

# ─── Supabase Client (lazy init) ─────────────────────────────────

_supabase_client = None

def get_supabase():
    """Lazy-initialize Supabase client. Returns None if unavailable."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        sys.stderr.write("✅ Supabase: connected\n")
        return _supabase_client
    except ImportError:
        sys.stderr.write("⚠️ Supabase: supabase-py not installed, using local-only mode\n")
        return None
    except Exception as e:
        sys.stderr.write(f"⚠️ Supabase: connection failed ({e}), using local-only mode\n")
        return None


# ─── Helpers ─────────────────────────────────────────────────────

def load_kb_index() -> List[Dict]:
    """Load the KB index from disk. Returns empty list on error."""
    if not os.path.exists(INDEX_FILE):
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Index load error: {str(e).replace(BASE_DIR, '...')}\n")
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
    """Save KB card to local filesystem."""
    category_dir = os.path.join(KB_DIR, category)
    os.makedirs(category_dir, exist_ok=True)

    filename = f"{kb_id}.md"
    file_path = os.path.join(category_dir, filename)
    rel_path = f"{category}/{filename}"

    # Security: Ensure path stays inside KB_DIR
    if not os.path.abspath(file_path).startswith(os.path.abspath(KB_DIR)):
        return False, "❌ Security Error: Access denied."

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return False, f"❌ Error saving local file: {e}"

    # Update local index
    index = load_kb_index()
    index = [item for item in index if item['kb_id'] != kb_id]

    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Unknown Title"
    tldr = extract_tldr_fields(content)

    new_entry = {
        "kb_id": kb_id,
        "title": title,
        "category": category,
        "platform": metadata.get('platform', 'unknown'),
        "technologies": metadata.get('technologies', []),
        "complexity": metadata.get('complexity', 1),
        "criticality": metadata.get('criticality', 'low'),
        "created": metadata.get('created', ''),
        "tags": metadata.get('tags', []),
        "related_kb": metadata.get('related_kb', []),
        "file_path": rel_path,
        "quick_summary": tldr["quick_summary"],
        "fix_time": tldr["fix_time"],
    }

    index.append(new_entry)

    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return False, f"⚠️ File saved, but index update failed: {e}"

    return True, rel_path


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
        result = sb.table("fixflow_kb").upsert(row, on_conflict="kb_id").execute()
        return True, "synced (with embedding)" if embedding else "synced (no embedding)"
    except Exception as e:
        return False, str(e)


def _get_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Supabase Edge Function 'embed'."""
    sb = get_supabase()
    if not sb or not text:
        return None
    try:
        # Call Edge Function
        # Note: adjust based on actual supabase-py version behavior
        res = sb.functions.invoke("embed", invoke_options={'body': {'input': text}})
        
        # Parse response
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
        # Silent fail for embeddings, core function should proceed
        sys.stderr.write(f"Embedding generation failed: {e}\n")
    return None


def search_cloud(query: str) -> List[Dict]:
    """Search KB cards in Supabase using server-side search function.
    
    Uses the `search_kb_cards` RPC function which supports:
    - Full-text search with websearch_to_tsquery (multi-word, phrases)
    - Vector similarity search (when embeddings available)
    - Hybrid ranking (FTS rank or cosine similarity)
    """
    sb = get_supabase()
    if not sb:
        return []

    try:
        # Try to generate embedding for the query
        query_embedding = _get_embedding(query)
        
        result = sb.rpc("search_kb_cards", {
            "query_text": query,
            "query_embedding": query_embedding,  # Pass embedding if available
            "match_limit": 20
        }).execute()
        return result.data if result.data else []
    except Exception as e:
        sys.stderr.write(f"Cloud search error: {e}\n")
        # Fallback to direct table query
        try:
            result = sb.table("fixflow_kb") \
                .select("kb_id, title, category, platform, technologies, complexity, criticality, tags, quick_summary, fix_time") \
                .eq("status", "published") \
                .ilike("title", f"%{query}%") \
                .limit(20) \
                .execute()
            return result.data if result.data else []
        except Exception:
            return []


# ─── Tools ───────────────────────────────────────────────────────

@mcp.tool
def resolve_kb_id(query: str) -> List[Dict]:
    """
    Search the Knowledge Base to find a KB ID.

    Call this FIRST to find the correct `kb_id` before reading a document.
    Returns list of matching entries with metadata.
    Searches both local index AND cloud database.

    Args:
        query: User question, error message, or technology name.
    """
    query = query[:MAX_QUERY_LENGTH].lower()
    
    # 1. Local search
    index = load_kb_index()
    local_results = []
    for item in index:
        searchable = " ".join([
            item.get('title', ''),
            item.get('quick_summary', ''),
            item.get('kb_id', ''),
            " ".join(item.get('tags', [])),
            " ".join(item.get('technologies', [])),
        ]).lower()
        if query in searchable:
            item_copy = dict(item)
            item_copy["_source"] = "local"
            local_results.append(item_copy)

    # 2. Cloud search (full-text)
    cloud_results = search_cloud(query)
    for item in cloud_results:
        item["_source"] = "cloud"

    # 3. Merge: local first, then cloud (deduplicate by kb_id)
    seen_ids = {r["kb_id"] for r in local_results}
    merged = local_results[:]
    for item in cloud_results:
        if item["kb_id"] not in seen_ids:
            merged.append(item)
            seen_ids.add(item["kb_id"])

    return merged


@mcp.tool
def read_kb_doc(kb_id: str) -> str:
    """
    Read the full Markdown content of a KB card.

    Requires a valid `kb_id` (e.g., 'WIN_TERM_042') obtained from `resolve_kb_id`.
    Returns the solution, checklist, and verification steps.
    Reads from local cache first, falls back to cloud.
    Automatically tracks view count in cloud.

    Args:
        kb_id: The unique ID of the card to read.
    """
    content = None

    # 1. Try local first
    index = load_kb_index()
    entry = next((item for item in index if item["kb_id"] == kb_id), None)

    if entry:
        rel_path = entry.get("file_path", "")
        if rel_path:
            full_path = os.path.abspath(os.path.join(KB_DIR, rel_path))
            if full_path.startswith(os.path.abspath(KB_DIR)) and os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    pass

    # 2. Try cloud
    if not content:
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
                    content = result.data["content"]
            except Exception as e:
                sys.stderr.write(f"Cloud read error: {e}\n")

    if not content:
        return f"Error: KB ID '{kb_id}' not found (checked local + cloud)."

    # 3. Track view (fire-and-forget)
    _track_event(kb_id, "view")

    return content


@mcp.tool
def save_kb_card(content: str, overwrite: bool = False) -> str:
    """
    Validate and save a new Knowledge Base card.

    Performs server-side validation of Markdown structure and metadata.
    Checks for duplicates before saving.
    Saves BOTH locally and to the cloud database for community access.

    Args:
        content: Full Markdown content with YAML frontmatter.
        overwrite: Set to True to update an existing card.
    """
    # 1. Validate
    is_valid, error_msg = validate_kb_markdown(content)
    if not is_valid:
        return f"❌ Validation FAILED: {error_msg}"

    # 2. Parse Metadata
    yaml_match = re.match(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    metadata = yaml.safe_load(yaml_match.group(1))

    kb_id = metadata['kb_id']
    category = metadata['category'].lower()

    # Security: Validate category name
    if not re.match(r'^[a-z0-9_-]+$', category):
        return f"❌ Security Error: Invalid category '{category}'."

    # 3. Deduplication check (cloud)
    if not overwrite:
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else ""
        duplicates = _find_duplicates(kb_id, title, metadata.get('tags', []))
        if duplicates:
            dup_list = "\n".join([
                f"  • {d['kb_id']} — {d['title']} (similarity: {d.get('similarity', 'N/A')})"
                for d in duplicates[:3]
            ])
            return (
                f"⚠️ Similar cards already exist:\n{dup_list}\n\n"
                f"If this is intentionally different, use overwrite=True."
            )

    # 4. Check existence (local)
    category_dir = os.path.join(KB_DIR, category)
    file_path = os.path.join(category_dir, f"{kb_id}.md")
    if os.path.exists(file_path) and not overwrite:
        return f"❌ Card '{kb_id}' already exists. Use overwrite=True to update."

    # 5. Save locally
    local_ok, local_msg = save_to_local(kb_id, category, content, metadata)
    
    # 6. Save to cloud
    cloud_ok, cloud_msg = save_to_cloud(kb_id, content, metadata)

    # 7. Build response
    parts = []
    if local_ok:
        parts.append(f"📁 Local: saved to {local_msg}")
    else:
        parts.append(f"📁 Local: {local_msg}")
    
    if cloud_ok:
        parts.append(f"☁️ Cloud: {cloud_msg}")
    else:
        parts.append(f"☁️ Cloud: {cloud_msg}")

    status = "✅" if local_ok else "⚠️"
    return f"{status} KB card '{kb_id}' — " + " | ".join(parts)


def _find_duplicates(kb_id: str, title: str, tags: list) -> List[Dict]:
    """Check if similar KB cards already exist in the cloud."""
    sb = get_supabase()
    if not sb or not title:
        return []

    try:
        # Search by title keywords (first 3 significant words)
        words = [w for w in title.split() if len(w) > 3][:3]
        if not words:
            return []
        
        query = " ".join(words)
        result = sb.rpc("search_kb_cards", {
            "query_text": query,
            "match_limit": 5
        }).execute()
        
        if not result.data:
            return []

        # Filter: exclude the card itself, only show high similarity
        return [
            r for r in result.data
            if r["kb_id"] != kb_id and r.get("similarity", 0) > 0.3
        ]
    except Exception:
        return []


@mcp.resource("tech-kb://skill/{skill_name}")
def get_skill(skill_name: str = "create-kb-card") -> str:
    """Get instructions for a specific skill (e.g. creating a KB card)."""
    skills_map = {
        "create-kb-card": "skills/creating-kb-cards.md",
    }

    if skill_name not in skills_map:
        available = ", ".join(skills_map.keys())
        return f"Skill '{skill_name}' not found. Available: {available}"

    skill_path = os.path.join(BASE_DIR, skills_map[skill_name])

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Skill file not found for '{skill_name}'."
    except Exception as e:
        return f"Error loading skill '{skill_name}': {e}"


def report_card_result(kb_id: str, result: str) -> str:
    """Internal: report result of applying a KB card solution.
    
    Called automatically, not exposed as a tool.
    """
    if result not in ("solved", "failed", "applied"):
        return ""
    data = _track_event(kb_id, result)
    return f"Feedback '{result}' recorded for {kb_id}" if data else ""


def _track_event(kb_id: str, event: str) -> dict | None:
    """Track a card usage event via Supabase RPC. Returns stats or None."""
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.rpc("track_card_event", {
            "p_kb_id": kb_id,
            "p_event": event
        }).execute()
        return result.data if result.data else None
    except Exception as e:
        sys.stderr.write(f"Track event error: {e}\n")
        return None


# ─── Resources ───────────────────────────────────────────────────

@mcp.resource("tech-kb://index")
def get_full_index() -> str:
    """Get the full index of all KB cards."""
    return json.dumps(load_kb_index(), indent=2, ensure_ascii=False)


@mcp.resource("tech-kb://stats")
def get_kb_stats() -> str:
    """Get Knowledge Base statistics: total cards, categories, top rated."""
    sb = get_supabase()
    
    index = load_kb_index()
    local_count = len(index)
    local_categories = list(set(item.get("category", "unknown") for item in index))
    
    parts = [f"📊 FixFlow KB Statistics\n"]
    parts.append(f"📁 Local cards: {local_count}")
    parts.append(f"📁 Categories: {', '.join(local_categories) if local_categories else 'none'}")

    if sb:
        try:
            cards = sb.table("fixflow_kb") \
                .select("kb_id, title, category, view_count, solved_count, failed_count") \
                .eq("status", "published") \
                .execute()
            
            if cards.data:
                cloud_count = len(cards.data)
                total_views = sum(c.get("view_count", 0) or 0 for c in cards.data)
                total_solved = sum(c.get("solved_count", 0) or 0 for c in cards.data)
                total_failed = sum(c.get("failed_count", 0) or 0 for c in cards.data)

                parts.append(f"\n☁️ Cloud cards: {cloud_count}")
                parts.append(f"👁️ Total views: {total_views}")
                parts.append(f"✅ Solved: {total_solved} | ❌ Failed: {total_failed}")
                
                if total_solved + total_failed > 0:
                    rate = round(total_solved / (total_solved + total_failed) * 100, 1)
                    parts.append(f"📈 Success rate: {rate}%")

                by_views = sorted(cards.data, key=lambda x: x.get("view_count", 0) or 0, reverse=True)[:5]
                parts.append(f"\n🏆 Most viewed:")
                for i, card in enumerate(by_views, 1):
                    v = card.get("view_count", 0) or 0
                    parts.append(f"  {i}. {card['kb_id']} — {card['title']} (👁️{v})")
        except Exception as e:
            parts.append(f"\n⚠️ Cloud error: {e}")
    else:
        parts.append("\n☁️ Cloud: unavailable")

    return "\n".join(parts)


# ─── Entry Point ─────────────────────────────────────────────────

def main():
    """CLI entry point for fixflow-mcp."""
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
