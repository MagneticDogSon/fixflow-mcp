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
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhid3JkdXFibXV1cHhodG5kcnRhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNzQxNDQsImV4cCI6MjA4Njg1MDE0NH0.t37Ag0pQHuYdyflfviST69ZX8R2FTNCdLzhpN2tt_s0"
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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
    return JSONResponse({"status": "healthy", "service": "fixlow"})

# Mounting FastMCP app at /mcp explicitly to avoid path conflicts
mcp_app = mcp.http_app()

app = Starlette(
    routes=[
        Route("/", endpoint=health_check),
        Route("/health", endpoint=health_check),
        Mount("/mcp", app=mcp_app),
    ]
)
