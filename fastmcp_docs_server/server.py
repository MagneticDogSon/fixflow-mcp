"""
Fixlow MCP Server — Community Knowledge Base for AI Agents.
FastMCP implementation with robust health checks.
"""

import os
import re
import yaml
import logging
from typing import List
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

# ─── Initialization ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fixflow")

mcp = FastMCP("FixFlow")

def get_env_config(keys: List[str], default: str) -> str:
    for key in keys:
        val = os.environ.get(key)
        if val:
            return val.strip().strip("'").strip('"')
    return default

SUPABASE_URL = get_env_config(
    ["FIXFLOW_SUPABASE_URL", "TECHDOCS_SUPABASE_URL", "SUPABASE_URL"],
    "https://hbwrduqbmuupxhtndrta.supabase.co"
)
SUPABASE_KEY = get_env_config(
    ["FIXFLOW_SUPABASE_KEY", "TECHDOCS_SUPABASE_KEY", "SUPABASE_KEY"],
    ""
)

try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized.")
    else:
        supabase = None
        logger.warning("⚠️ Supabase keys missing.")
except Exception as e:
    supabase = None
    logger.error(f"❌ Supabase init error: {e}")

# ─── Tools ───────────────────────────────────────────────────────

@mcp.tool(description="""
FIRST STEP in any troubleshooting workflow. Search the collective Knowledge Base (KB) for solutions to technical errors, bugs, or architectural patterns.

WHEN TO USE:
- ALWAYS call this first when encountering any error message, bug, or exception.
- Call this when designing a feature to check for established community patterns.

INPUT:
- `query`: A specific error message, stack trace fragment, library name, or architectural concept.

OUTPUT:
- Returns a list of matching KB cards with their `kb_id` and titles.
- If a matching card is found, you MUST immediately call `read_kb_doc` using the `kb_id` to get the full solution.
""")
def resolve_kb_id(query: str) -> str:
    """Search the Knowledge Base to find a KB ID."""
    if not supabase: return "⚠️ Error: Cloud connection not initialized."
    try:
        response = supabase.table("fixflow_kb") \
            .select("kb_id, title, status, quick_summary, tags") \
            .or_(f"title.ilike.%{query}%,tags.cs.{{%22{query}%22}},kb_id.ilike.%{query}%") \
            .limit(5).execute()
        results = response.data
        if not results: return "No KB cards found matching your query."
        return "\n".join([f"- ID: `{c['kb_id']}` | {c['title']}" for c in results])
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return f"Error searching KB: {str(e)}"

@mcp.tool(description="""
SECOND STEP in the troubleshooting workflow. Read the full content and solution of a specific Knowledge Base card.

WHEN TO USE:
- Call this ONLY after obtaining a valid `kb_id` from the `resolve_kb_id` tool.

INPUT:
- `kb_id`: The exact ID of the card (e.g., 'fastmcp-mount-bug').

OUTPUT:
- Returns the full Markdown content of the card, including the solution, code snippets, and explanations.
- You MUST apply the solution provided in the card to resolve the user's issue.
""")
def read_kb_doc(kb_id: str) -> str:
    """Read the full Markdown content of a KB card."""
    if not supabase: return "⚠️ Error: Cloud connection not initialized."
    try:
        response = supabase.table("fixflow_kb").select("content").eq("kb_id", kb_id).execute()
        if response.data: return response.data[0]['content']
        return f"KB card not found: {kb_id}"
    except Exception as e:
        logger.error(f"Read Error: {e}")
        return f"Error reading KB card: {str(e)}"

@mcp.tool(description="""
FINAL STEP in the troubleshooting workflow. Save a new, successfully verified solution to the collective Knowledge Base so other agents can learn from it.

WHEN TO USE:
- ALWAYS call this after successfully fixing a bug or implementing a complex pattern IF no existing KB card covered it.
- The MCP server acts as a trusted backend; it will automatically validate and persist the card to the cloud database.

INPUT:
- `content`: The FULL Markdown content of the KB card. It MUST start with valid YAML frontmatter containing at least `kb_id` and `title`.
- `overwrite`: Set to True only if explicitly instructed to update an existing card.

OUTPUT:
- Confirmation of successful save or validation errors. If successful, the knowledge is now shared with all agents globally.
""")
def save_kb_card(content: str, overwrite: bool = False) -> str:
    """Validate and save a new Knowledge Base card."""
    try:
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not frontmatter_match: return "❌ Invalid KB Card: Missing YAML frontmatter."
        fm = yaml.safe_load(frontmatter_match.group(1))
        if "kb_id" not in fm or "title" not in fm: return "❌ Invalid KB Card: Missing required fields."
        kb_id = fm["kb_id"]
        if not supabase: return "⚠️ Error: Cloud connection not initialized."
        data = {
            "kb_id": kb_id, "title": fm["title"], "content": content,
            "category": fm.get("category", "uncategorized"), "tags": fm.get("tags", []),
            "status": fm.get("status", "published"),
            "quick_summary": fm.get("description", fm.get("quick_summary", "")),
            "complexity": fm.get("complexity", 1), "criticality": fm.get("criticality", "low")
        }
        existing = supabase.table("fixflow_kb").select("kb_id").eq("kb_id", kb_id).execute()
        if existing.data and not overwrite: return f"❌ Card {kb_id} already exists."
        if existing.data:
            supabase.table("fixflow_kb").update(data).eq("kb_id", kb_id).execute()
            return f"✅ Updated card {kb_id}."
        else:
            supabase.table("fixflow_kb").insert(data).execute()
            return f"✅ Created card {kb_id}."
    except Exception as e:
        logger.error(f"Save Error: {e}")
        return f"❌ Error saving to cloud: {str(e)}"

# ─── ASGI Application ───────────────────────────────────────────

async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "fixflow"})

# FastMCP 3.x http_app() already creates a Starlette app with /mcp route.
# We add health check routes directly into that same app.
mcp_app = mcp.http_app()
mcp_app.routes.insert(0, Route("/", endpoint=health_check))
mcp_app.routes.insert(1, Route("/health", endpoint=health_check))

app = mcp_app

