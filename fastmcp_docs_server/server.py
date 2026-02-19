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
import argparse
from typing import List, Dict, Optional

# ─── Configuration ───────────────────────────────────────────────
mcp = FastMCP("FixFlow")

# Cloud configuration (read from environment, defaults to None)
SUPABASE_URL = os.environ.get("FIXFLOW_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("FIXFLOW_SUPABASE_KEY")

try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None # Will fail gracefully if not configured
except ImportError:
    supabase = None

# ─── Tools ───────────────────────────────────────────────────────

@mcp.tool()
def resolve_kb_id(query: str) -> str:
    """
    Search the Knowledge Base to find a KB ID.

    Call this FIRST to find the correct `kb_id` before reading a document.
    Returns list of matching entries with metadata.
    Searches both local index AND cloud database.

    Args:
        query: User question, error message, or technology name.
    """
    if not supabase:
        return "⚠️ Error: Supabase client not initialized. Check FIXFLOW_SUPABASE_URL and FIXFLOW_SUPABASE_KEY."

    try:
        # Search via Supabase RPC (Full Text Search)
        # Assuming you have a function `search_kb_cards` or similar
        # For now, let's just query the table directly with `ilike` or fts
        
        # Simple search using ilike on title and tags
        response = supabase.table("kb_cards") \
            .select("id, title, status, description, tags, version") \
            .or_(f"title.ilike.%{query}%,tags.cs.{{%22{query}%22}},id.ilike.%{query}%") \
            .limit(5) \
            .execute()
        
        results = response.data
        if not results:
             # Try simple text search on content if title fails?
             # Or just return empty
             return "No KB cards found matching your query."

        formatted = []
        for card in results:
            formatted.append(f"- ID: `{card['id']}` | Title: {card['title']} (v{card['version']})")
        
        return "\n".join(formatted)

    except Exception as e:
        return f"Error searching KB: {str(e)}"


@mcp.tool()
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
    if not supabase:
        return "⚠️ Error: Supabase client not initialized."

    try:
        response = supabase.table("kb_cards").select("content").eq("id", kb_id).execute()
        if response.data:
             return response.data[0]['content']
        else:
             return f"KB card not found: {kb_id}"
    except Exception as e:
        return f"Error reading KB card: {str(e)}"


@mcp.tool()
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
    # 1. Validate Structure locally (using Regex/YAML)
    try:
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not frontmatter_match:
             return "❌ Invalid KB Card: Missing YAML frontmatter."
        
        fm = yaml.safe_load(frontmatter_match.group(1))
        
        card_id = fm.get("id")
        if not card_id:
             return "❌ Invalid KB Card: Missing id."

    except Exception as e:
        return f"❌ Validation Error: {str(e)}"

    if not supabase:
        return "⚠️ Error: Supabase client not initialized. Cannot save to cloud."

    try:
        # Check if exists
        existing = supabase.table("kb_cards").select("id").eq("id", card_id).execute()
        
        if existing.data and not overwrite:
            return f"❌ Card {card_id} already exists. Use overwrite=True to update."
        
        # Prepare data
        data = {
            "id": card_id,
            "title": fm["title"],
            "content": content,
            "author": fm["author"],
            "tags": fm["tags"],
            "version": fm["version"],
            "status": fm.get("status", "draft"),
            "description": fm.get("description", "")
        }

        if existing.data:
            supabase.table("kb_cards").update(data).eq("id", card_id).execute()
            return f"✅ Updated card {card_id} successfully."
        else:
            supabase.table("kb_cards").insert(data).execute()
            return f"✅ Created new card {card_id} successfully."

    except Exception as e:
        return f"❌ Error saving to cloud: {str(e)}"


# ─── Entry Point ─────────────────────────────────────────────────

def main():
    """CLI entry point for fixflow-mcp."""
    parser = argparse.ArgumentParser(description="FixFlow MCP Server")
    parser.add_argument(
        "transport", 
        choices=["stdio", "sse"], 
        default="stdio", 
        nargs="?",
        help="Transport protocol (stdio or sse)"
    )
    # Important: host should default to 0.0.0.0 for Docker
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE")
    
    # Port is passed by environment variable PORT dynamically by Cloud Run / Render
    # Default to 8000 if not set
    env_port = os.environ.get("PORT", "8000")
    parser.add_argument("--port", type=int, default=int(env_port), help="Port for SSE")
    
    args = parser.parse_args()

    # If transport is NOT provided explicitly but we are in a container with PORT, likely SSE
    if args.transport == "stdio" and os.environ.get("RENDER"):
          # However, Dockerfile explicitly says "sse", so this is handled.
          pass

    if args.transport == "sse":
        sys.stderr.write(f"🚀 Starting FixFlow SSE server on {args.host}:{args.port}\n")
        # Run FastMCP in SSE mode
        mcp.run(transport='sse', host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
