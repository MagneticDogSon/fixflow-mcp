# FixFlow MCP Server

A lightweight MCP server that gives AI agents persistent memory for technical solutions.

## Quick Start

```bash
uvx fixflow-mcp
```

## MCP Configuration

Add to your MCP config:

```json
{
  "fixflow": {
    "command": "uvx",
    "args": ["fixflow-mcp"],
    "env": { "PYTHONIOENCODING": "utf-8" }
  }
}
```

## Tools (3)

| Tool | Description |
|------|-------------|
| `resolve_kb_id(query)` | 🔍 Search KB — hybrid FTS + vector similarity |
| `read_kb_doc(kb_id)` | 📖 Read card content — auto-tracks views |
| `save_kb_card(content, overwrite)` | 💾 Validate, deduplicate, embed, and save |

## Resources (3)

| Resource | Description |
|----------|-------------|
| `tech-kb://index` | 📑 Full index of all KB cards (JSON) |
| `tech-kb://stats` | 📊 Usage statistics and top cards |
| `tech-kb://skill/{name}` | 📋 Agent instructions for KB card creation |
