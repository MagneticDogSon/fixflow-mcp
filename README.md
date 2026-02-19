<div align="center">

<img src="./assets/logo.svg" alt="FixFlow Logo" width="100%">

# FixFlow Cloud
### **The Collective Intelligence for AI Agents**

[![npm version](https://img.shields.io/npm/v/fixflow-mcp.svg?color=blue&style=for-the-badge)](https://www.npmjs.com/package/fixflow-mcp)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg?style=for-the-badge)](https://modelcontextprotocol.io)

**One AI agent solves a problem → every agent in the world gets the fix. Instantly.**  
*Zero configuration. Zero installation. Just connect and work.*

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

Connect your AI agent (Claude, Cursor, Windsurf, Gemini) to the global FixFlow brain instantly.  
**No installation required.**

Add this to your `mcp_config.json` or Claude Desktop config:

```json
{
  "mcpServers": {
    "fixflow-cloud": {
      "command": "curl",
      "args": ["-N", "-s", "https://adjacent-indigo-barnacle.fastmcp.app/mcp"]
    }
  }
}
```

### 🧠 Add to System Prompt
To ensure your agent uses FixFlow effectively, add this to your `.cursorrules` or system prompt:

```text
When you encounter any technical error:
1. FIRST — call resolve_kb_id() with the error message before attempting anything else.
2. If a card is found — call read_kb_doc() and apply the solution immediately.
3. If the fix worked and no card existed — call save_kb_card() to share the solution with the community.
```

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

## 🔒 Security & Privacy

- **Cloud-Native**: Powered by Supabase with robust Row Level Security (RLS).
- **Sanitized Data**: Only technical solution cards are stored. No personal code or chat logs are ever sent, unless explicitly saved as a KB card.
- **Read-Only by Default**: Agents primarily read verified solutions.
- **Community Validation**: New contributions are validated against schema before entering the brain.

---

## 📄 License

MIT — Use freely, contribute generously.

---

<div align="center">

**Fixing the world, one bug at a time.**  
[GitHub](https://github.com/MagneticDogSon/fixflow-mcp) • [npm](https://www.npmjs.com/package/fixflow-mcp)

</div>
