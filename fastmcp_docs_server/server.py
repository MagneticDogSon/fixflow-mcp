"""
Fixlow MCP Server — Community Knowledge Base for AI Agents.
Only 3 tools. Minimal. Powerful.

  1. resolve_kb_id  →  FIND (search / list / stats)
  2. read_kb_doc    →  READ (content + metrics + related)
  3. save_kb_card   →  WRITE (save card / report outcome)
"""

import os
import re
import json
import yaml
import logging
from datetime import datetime, timezone
from typing import List
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route

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


# ═══════════════════════════════════════════════════════════════
# TOOL 1: FIND  (search / browse / stats — all in one)
# ═══════════════════════════════════════════════════════════════

@mcp.tool(description="""
FIRST STEP in any troubleshooting workflow. Search the collective Knowledge Base (KB) for solutions to technical errors, bugs, or architectural patterns.

Uses full-text search across titles, content, tags, and categories. Results are ranked by relevance and success rate.

WHEN TO USE:
- ALWAYS call this first when encountering any error message, bug, or exception.
- Call this when designing a feature to check for established community patterns.

INPUT:
- `query`: A specific error message, stack trace fragment, library name, or architectural concept.
- `category`: (Optional) Filter by category (e.g., 'devops', 'terminal', 'supabase').

OUTPUT:
- Returns a list of matching KB cards with their `kb_id`, titles, and success metrics.
- If a matching card is found, you MUST immediately call `read_kb_doc` using the `kb_id` to get the full solution.
""")
def resolve_kb_id(query: str = "", category: str = "") -> str:
    """Search the Knowledge Base. Empty query returns stats overview."""
    if not supabase:
        return "⚠️ Error: Cloud connection not initialized."

    try:
        # MODE: Stats overview (nothing provided)
        if not query.strip() and not category.strip():
            stats_resp = supabase.rpc("get_kb_stats").execute()
            stats = stats_resp.data
            # Handle both { } and [{ "get_kb_stats": { } }] formats
            if isinstance(stats, list) and stats:
                stats = stats[0].get("get_kb_stats", stats[0]) if isinstance(stats[0], dict) else stats[0]

            if not stats:
                return "📭 Knowledge Base is empty."

            lines = [f"📊 **Fixlow KB Overview**"]
            lines.append(f"📦 Total: **{stats.get('total_cards', 0)}** cards")

            total_applied = stats.get('total_applied', 0)
            if total_applied > 0:
                lines.append(
                    f"🔄 Applied: {total_applied} | "
                    f"✅ Solved: {stats.get('total_solved', 0)} | "
                    f"❌ Failed: {stats.get('total_failed', 0)} | "
                    f"Rate: {stats.get('global_success_rate', 0)}%"
                )

            categories = stats.get("categories", [])
            if categories:
                cat_str = ", ".join(f"{c['category']}({c['count']})" for c in categories)
                lines.append(f"📁 Categories: {cat_str}")

            review = stats.get("needs_review", [])
            if review:
                lines.append("\n⚠️ **Cards needing review (rate < 50%):**")
                for r in review:
                    lines.append(f"  🔴 `{r['kb_id']}`: {r['title']} (rate={r.get('success_rate', '?')}%)")

            return "\n".join(lines)

        # MODE: Search or list by category
        params = {
            "search_query": query.strip(),
            "filter_category": category.strip() if category.strip() else None,
            "sort_field": "rank",
            "max_results": 10
        }
        response = supabase.rpc("search_kb", params).execute()
        results = response.data

        if not results:
            return "No KB cards found matching your query."

        lines = []
        for c in results:
            rate = float(c.get("success_rate", 0) or 0)
            applied = c.get("applied_count", 0) or 0
            badge = ""
            if applied > 0:
                badge = f" ✅{rate}%" if rate >= 80 else (f" ⚠️{rate}%" if rate >= 50 else f" 🔴{rate}%")
            lines.append(f"- ID: `{c['kb_id']}` | {c['title']} [{c.get('category', '?')}]{badge}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return f"Error searching KB: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# TOOL 2: READ  (content + metrics + related cards)
# ═══════════════════════════════════════════════════════════════

@mcp.tool(description="""
SECOND STEP in the troubleshooting workflow. Read the full content and solution of a specific Knowledge Base card.

Returns the card content WITH reliability metrics and related cards so you can assess trustworthiness and explore connected issues.

WHEN TO USE:
- Call this ONLY after obtaining a valid `kb_id` from the `resolve_kb_id` tool.

INPUT:
- `kb_id`: The exact ID of the card (e.g., 'CROSS_DOCKER_001').

OUTPUT:
- Returns reliability metrics followed by the full Markdown content of the card, plus related cards.
- You MUST apply the solution provided in the card to resolve the user's issue.
- After applying, you MUST call `save_kb_card` with `outcome` parameter to close the feedback loop.
""")
def read_kb_doc(kb_id: str) -> str:
    """Read KB card with metrics and related cards."""
    if not supabase:
        return "⚠️ Error: Cloud connection not initialized."
    try:
        response = supabase.table("fixflow_kb") \
            .select("content, applied_count, solved_count, failed_count, view_count") \
            .eq("kb_id", kb_id).execute()

        if not response.data:
            return f"KB card not found: {kb_id}"

        card = response.data[0]
        content = card.get("content", "")
        applied = card.get("applied_count") or 0
        solved = card.get("solved_count") or 0
        failed = card.get("failed_count") or 0
        views = (card.get("view_count") or 0) + 1

        # Reliability badge
        if applied > 0:
            rate = round(solved / applied * 100, 1)
            if rate >= 80:
                reliability = f"✅ RELIABLE ({rate}%)"
            elif rate >= 50:
                reliability = f"⚠️ MODERATE ({rate}%)"
            else:
                reliability = f"🔴 UNRELIABLE ({rate}%) — verify carefully"
        else:
            reliability = "📭 NEW (never applied)"

        # Increment view_count (non-blocking)
        try:
            supabase.table("fixflow_kb").update({"view_count": views}).eq("kb_id", kb_id).execute()
        except Exception:
            pass

        # Build response
        parts = [
            f"📊 applied={applied} solved={solved} failed={failed} views={views} | {reliability}",
            "---",
            content,
        ]

        # Auto-append related cards
        try:
            related = supabase.rpc("find_related_cards", {
                "target_kb_id": kb_id,
                "max_results": 3
            }).execute()
            if related.data:
                parts.append("\n---\n🔗 **Related cards:**")
                for r in related.data:
                    parts.append(f"- `{r['kb_id']}` — {r['title']} [{r.get('category', '?')}]")
        except Exception:
            pass

        return "\n".join(parts)

    except Exception as e:
        logger.error(f"Read Error: {e}")
        return f"Error reading KB card: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# TOOL 3: WRITE  (save new card OR report outcome)
# ═══════════════════════════════════════════════════════════════

@mcp.tool(description="""
WRITE to the Knowledge Base. This tool has TWO modes:

**MODE 1 — SAVE a new card**: Provide `content` with full Markdown following the ACTIONABLE schema.
Required YAML fields: `kb_id`, `title`, `category`, `tags`.
Required Markdown sections: `## 🔍 This Is Your Problem If:`, `## ✅ SOLUTION (copy-paste)`, `## ✔️ Verification`.

**MODE 2 — REPORT OUTCOME**: After applying a KB card solution, report whether it worked.
Provide `kb_id` + `outcome` ('success' or 'failure'). Optionally add `enrichment` text if the solution needed extra steps.

WHEN TO USE:
- Mode 1: After successfully fixing a bug IF no existing KB card covered it.
- Mode 2: ALWAYS after applying a solution from `read_kb_doc` and running verification.

INPUT:
- `content`: (Mode 1) Full Markdown KB card content.
- `overwrite`: (Mode 1) Set to True to update an existing card.
- `kb_id`: (Mode 2) ID of the card to report outcome for.
- `outcome`: (Mode 2) 'success' or 'failure'.
- `enrichment`: (Mode 2, optional) Additional context to merge into the card when outcome is 'failure'.
""")
def save_kb_card(
    content: str = "",
    overwrite: bool = False,
    kb_id: str = "",
    outcome: str = "",
    enrichment: str = ""
) -> str:
    """Save a new KB card or report outcome of applying an existing card."""
    if not supabase:
        return "⚠️ Error: Cloud connection not initialized."

    # ─── MODE 2: Report Outcome ──────────────────────────────
    if kb_id.strip() and outcome.strip():
        return _report_outcome(kb_id.strip(), outcome.strip().lower(), enrichment)

    # ─── MODE 1: Save Card ───────────────────────────────────
    if not content.strip():
        return "❌ Either `content` (to save) or `kb_id` + `outcome` (to report) must be provided."

    try:
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not frontmatter_match:
            return "❌ Invalid KB Card: Missing YAML frontmatter."
        fm = yaml.safe_load(frontmatter_match.group(1))

        # Strict YAML validation
        required_keys = ["kb_id", "title", "category", "tags"]
        missing_keys = [k for k in required_keys if k not in fm]
        if missing_keys:
            return f"❌ Invalid KB Card: Missing YAML fields: {', '.join(missing_keys)}"

        # Strict Markdown structure validation
        required_sections = {
            "## 🔍 This Is Your Problem If:": "Diagnosis section",
            "## ✅ SOLUTION (copy-paste)": "Solution section",
            "## ✔️ Verification": "Verification section",
        }
        for section, label in required_sections.items():
            if section not in content:
                return f"❌ Invalid KB Card: Missing '{section}' ({label})."

        card_kb_id = fm["kb_id"]
        data = {
            "kb_id": card_kb_id,
            "title": fm["title"],
            "content": content,
            "category": fm.get("category", "uncategorized"),
            "tags": fm.get("tags", []),
            "status": fm.get("status", "published"),
            "quick_summary": fm.get("description", fm.get("quick_summary", "")),
            "complexity": fm.get("complexity", 1),
            "criticality": fm.get("criticality", "low"),
        }

        existing = supabase.table("fixflow_kb").select("kb_id").eq("kb_id", card_kb_id).execute()
        if existing.data and not overwrite:
            return f"❌ Card `{card_kb_id}` already exists. Use overwrite=True to update."
        if existing.data:
            supabase.table("fixflow_kb").update(data).eq("kb_id", card_kb_id).execute()
            return f"✅ Updated card `{card_kb_id}`."
        else:
            supabase.table("fixflow_kb").insert(data).execute()
            return f"✅ Created card `{card_kb_id}`."

    except Exception as e:
        logger.error(f"Save Error: {e}")
        return f"❌ Error saving to cloud: {str(e)}"


def _report_outcome(kb_id: str, outcome: str, enrichment: str) -> str:
    """Internal: report outcome of applying a KB card."""
    if outcome not in ("success", "failure"):
        return "❌ `outcome` must be 'success' or 'failure'."
    try:
        success = outcome == "success"
        response = supabase.table("fixflow_kb") \
            .select("kb_id, content, applied_count, solved_count, failed_count") \
            .eq("kb_id", kb_id).execute()

        if not response.data:
            return f"❌ KB card not found: {kb_id}"

        card = response.data[0]
        applied = (card.get("applied_count") or 0) + 1
        solved = (card.get("solved_count") or 0) + (1 if success else 0)
        failed = (card.get("failed_count") or 0) + (0 if success else 1)
        rate = round(solved / applied * 100, 1) if applied > 0 else 0.0

        update_data = {
            "applied_count": applied,
            "solved_count": solved,
            "failed_count": failed,
            "last_used_at": datetime.now(timezone.utc).isoformat(),
        }

        result_parts = [
            f"📊 Card `{kb_id}`: applied={applied}, solved={solved}, failed={failed}, rate={rate}%"
        ]

        # Enrich card content on failure
        if not success and enrichment.strip():
            original_content = card.get("content", "")
            insertion_marker = "## 💡 Context"
            enrichment_block = f"\n\n### 🆕 Community Addition (auto-enriched)\n{enrichment.strip()}\n\n"

            if insertion_marker in original_content:
                updated_content = original_content.replace(
                    insertion_marker, enrichment_block + insertion_marker
                )
            else:
                updated_content = original_content.rstrip() + "\n" + enrichment_block

            update_data["content"] = updated_content
            result_parts.append("📝 Card enriched with additional context.")

        supabase.table("fixflow_kb").update(update_data).eq("kb_id", kb_id).execute()
        result_parts.append("✅ Solution confirmed working." if success else "⚠️ Solution did not fully resolve the issue.")
        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"Report Outcome Error: {e}")
        return f"❌ Error reporting outcome: {str(e)}"


# ─── ASGI Application ───────────────────────────────────────────

from starlette.responses import JSONResponse
from starlette.routing import Route

async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "fixflow"})

mcp_app = mcp.http_app()
mcp_app.routes.insert(0, Route("/", endpoint=health_check))
mcp_app.routes.insert(1, Route("/health", endpoint=health_check))

app = mcp_app
