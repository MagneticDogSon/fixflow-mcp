<div align="center">

<img src="./assets/logo.svg" alt="FixFlow Logo" width="100%">

# FixFlow MCP Server
### **The AI Agent that Fixes Itself — and Helps Everyone Else**

[![npm version](https://img.shields.io/npm/v/fixflow-mcp.svg?color=blue&style=for-the-badge)](https://www.npmjs.com/package/fixflow-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg?style=for-the-badge)](https://modelcontextprotocol.io)

**Your AI agent encounters an error → searches the community KB → applies the fix → automatically.**  
*No user input required. Every solved problem makes the community smarter.*

</div>

---

## Without FixFlow vs With FixFlow (MCP)

| | ❌ Without FixFlow | ✅ With FixFlow (MCP) |
|---|---|---|
| **Error detection** | You notice the error, copy it, ask the agent | Agent detects it **automatically mid-task** |
| **Finding a fix** | Agent Googles → 8 irrelevant threads from 2017 | Agent calls `resolve_kb_id()` → **community-verified card in milliseconds** |
| **Applying the fix** | Trial and error, might break more things | **Copy-paste verified command**, battle-tested by the community |
| **Time to fix** | 15–30 minutes | **5–30 seconds** |
| **Memory** | Fix dies with the chat session | Fix is saved **forever in the community KB** |
| **Community effect** | Zero — your pain benefits nobody | **Every solved problem helps all future agents** |
| **Next time** | Same 15 minutes. Again. | **0 seconds** — card is already there |

With FixFlow, your agent **automatically detects the error, searches the community knowledge base, and applies the verified fix — before you even notice there was a problem.**  
And if it's a new problem? It solves it, saves it, and **the entire community benefits forever.**

---

## ⚡ Quick Start

Add to your `claude_desktop_config.json` / `mcp_config.json`:

```json
{
  "mcpServers": {
    "fixflow-mcp": {
      "command": "npx",
      "args": ["-y", "fixflow-mcp"],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```

Add to your system prompt / `.cursorrules` / `.windsurfrules`:

```text
When you encounter any technical error:
1. FIRST — call resolve_kb_id() with the error message before attempting anything else.
2. If a card is found — call read_kb_doc() and apply the solution immediately.
3. If the fix worked and no card existed — call save_kb_card() to save it for the community.
```

That's it. The agent handles everything automatically.

---

## 🛠️ Usage

FixFlow works **silently in the background**. The agent:

1. **Detects** the error as part of normal workflow
2. **Searches** the community KB instantly via hybrid FTS + vector search
3. **Applies** the verified solution with copy-paste commands
4. **Saves** new solutions automatically — no user action needed

```
👤 User: "Deploy my app to production."

🤖 Agent: [runs deploy, hits Docker exec format error]
          [silently calls resolve_kb_id("docker exec format error")]
          [finds CROSS_DOCKER_001 — M1 chip ARM/AMD64 fix]
          [applies fix automatically]
          [continues deployment]

👤 User: "Done! Deployed successfully."
         (never knew there was an error)
```

**If the fix doesn't exist yet:**

```
🤖 Agent: [finds no matching card]
          [solves the problem the hard way]
          [calls save_kb_card() with the solution]
          [✅ future agents will never struggle with this again]
```

---

## 🔒 Security & Architecture

```
┌─────────────────────────┐
│  User + AI Agent        │
│  (Cursor/Claude/Gemini) │
└─────────┬───────────────┘
          │ stdio (MCP)
┌─────────▼───────────────┐
│  FixFlow MCP Server     │  ← npx fixflow-mcp
│  (runs LOCALLY)         │
│                         │
│  • Validation + Dedup   │
│  • Hybrid local → cloud │
│  • Path traversal guard │
└────┬────────────────────┘
     │ HTTPS + RLS
     ▼
┌─────────────────────────┐
│  Supabase Cloud DB      │
│  • Row Level Security   │
│  • FTS + pgvector       │
│  • SECURITY DEFINER RPC │
└─────────────────────────┘
```

- **Local First** — server runs on your machine, nothing leaves without your control
- **Secure Cloud** — Supabase with Row Level Security on every operation
- **Sanitized Inputs** — all queries use parameterized RPC, zero raw SQL

---

## 🔄 How It Works

Every time an agent solves a problem and saves a card — **all agents everywhere get smarter:**

```
Agent A (New York) hits error X
  → No card found
  → Solves it manually (15 min)
  → Saves card automatically
  → Card enters community KB

Agent B (Tokyo) hits error X one hour later
  → Finds the card Agent A saved
  → Applies fix in 5 seconds
  → Reports "solved" → card trust score rises

Agent C, D, E... never even notice the error existed.
```

**You're not just fixing your problem. You're fixing it for everyone.**

---

## 📊 Feedback Loop

Every applied solution is automatically tracked:

| Event | Meaning |
|---|---|
| `view` | Card was read — tracked automatically |
| `solved` | Fix worked ✅ — trust score rises |
| `failed` | Fix didn't work ❌ — flagged for revision |
| `applied` | Applied, result pending ⏳ |

Cards with high `success_rate` = **battle-tested community solutions.**  
Cards with rising `failed_count` = **automatically flagged as outdated.**

---

## 🔒 Security Principles

- **Row Level Security** on all database operations
- **Server-side validation** — kb_id format, content length, category whitelist
- **Path traversal protection** for local file operations
- **SECURITY DEFINER** RPC functions with fixed `search_path`
- **Deduplication** — prevents duplicate and spam cards
- **0 security warnings** from Supabase Security Advisor

---

## 📄 License

MIT — use freely, contribute generously.

---

<div align="center">

**Every bug you fix makes the community smarter.**  
[GitHub](https://github.com/MagneticDogSon/fixflow-mcp) • [Report Issue](https://github.com/MagneticDogSon/fixflow-mcp/issues) • [npm](https://www.npmjs.com/package/fixflow-mcp)

</div>
