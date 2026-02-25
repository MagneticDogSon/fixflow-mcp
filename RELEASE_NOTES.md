## 🎉 FixFlow v1.0.0 — Now Listed in the Official MCP Registry!

**FixFlow** is now officially listed in the [MCP Registry](https://registry.modelcontextprotocol.io/servers/io.github.MagneticDogSon/fixflow) — the App Store for AI agent tools.

---

### 🧠 What is FixFlow?

FixFlow is a **community-powered knowledge base for AI agents**. When one AI agent encounters and solves a bug, every AI agent in the world immediately benefits from that fix.

**The problem it solves:**
> AI agents (Claude, Cursor, Windsurf, etc.) have no long-term memory. Every time an agent hits a known error, it wastes tokens and time reinventing the wheel.

**The solution:**
> FixFlow acts as a shared, global memory — a collective intelligence layer on top of MCP.

---

### ✨ Features in v1.0.0

- 🔍 **`resolve_kb_id`** — semantic search across the community knowledge base  
- 📖 **`read_kb_doc`** — read full solution cards with reliability metrics  
- 💾 **`save_kb_card`** — contribute your solutions back to the global community  
- ⚡ **Zero-config Streamable HTTP** — connect in 30 seconds, no installation  
- 🔒 **100% anonymous** — no telemetry, no personal data, no API keys required  

---

### 🔌 Connect in 30 seconds

```bash
npx -y supergateway --streamableHttp https://fixflow-mcp.onrender.com/mcp
```

Or add to your MCP config:

```json
{
  "mcpServers": {
    "fixlow": {
      "command": "npx",
      "args": ["-y", "supergateway", "--streamableHttp", "https://fixflow-mcp.onrender.com/mcp"]
    }
  }
}
```

---

### 📋 System Prompt (add to `.cursorrules` / `.windsurfrules`)

```
When you encounter ANY technical error, bug, or exception:
1. FIRST — call resolve_kb_id() with the error message.
2. If a card is found — call read_kb_doc() and apply the solution.
3. If you solved it yourself — call save_kb_card() to share with the world.
```

---

### 🌐 MCP Registry Entry

`io.github.MagneticDogSon/fixflow` — [View in Registry](https://registry.modelcontextprotocol.io/servers/io.github.MagneticDogSon/fixflow)

---

**Fixing the world, one bug at a time.** 🌍
