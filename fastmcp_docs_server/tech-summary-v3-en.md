---
description: Generate ACTIONABLE KB cards - solution in 5 seconds
---

# Workflow: Instant-Apply KB Cards

**Goal**: Create a card that AI agents can apply in 5 seconds without reading excessive text.

**Format**: Diagnosis (3 sec) → Solution (copy-paste) → Verification (30 sec) → Fallback

---

## 📋 Quick Steps

### 1. Chat Analysis → Extract Key Information

**Required**:
- Category: terminal, encoding, proxy, dependency, config, build, runtime, etc.
- Platform: windows, linux, macos, cross-platform
- **Diagnostic Checklist** (3 symptoms - how to identify THIS problem)
- **Ready Solution** (code without specific paths)
- **Critical Points** (what will break the solution if missing)
- **Verification Command** (30 sec test)
- **Fallback** (1-2 alternatives)
- **Integration Pattern** (Global/Init/Event - where to put it)

**Optional** (if applicable):
- Root Cause (WHY - 1 sentence)
- Side Effects
- Root Cause (WHY - 1 sentence)
- Side Effects
- Versions where it works/doesn't work
- **Drop-in Component** (Self-contained Class/Fn)
- **Self-Test** (Runtime check snippet)

### 2. Generate KB_ID

```
Format: [PLATFORM]_[CATEGORY]_[NUMBER]
Examples: WIN_TERM_001, CROSS_PROXY_012
Number: max ID in category + 1
```

### 3. Create MD Card in `.agent/tech_kb/[category]/[KB_ID].md`

**CRITICAL**: Structure in STRICT priority order for agents:

```markdown
---
kb_id: "[KB_ID]"
category: "[category]"
platform: "[platform]"
technologies: [tech1, tech2]
complexity: [1-10]
criticality: "[low/medium/high/critical]"
created: "[YYYY-MM-DD]"
tags: [tag1, tag2, tag3]
related_kb: [KB_ID_1, KB_ID_2]
---

# [Short Title - max 5 words]

> **TL;DR**: [One sentence - what's the problem + solution]  
> **Fix Time**: ~[5 min / 30 min / 2 hours] | **Platform**: [Windows/Linux/macOS/All]

---

## 🔍 This Is Your Problem If:

- [ ] [Symptom 1 - specific symptom]
- [ ] [Symptom 2 - specific error]
- [ ] [Symptom 3 - environment condition]

**Where to Check**: [console / logs / env / processes]

---

## ✅ SOLUTION (copy-paste)

### 🎯 Integration Pattern:
**[Global Scope]** / **[Inside Init Loop]** / **[Event Handler]**

```[language]
# [One line - what the code does]
const TARGET_ID = "__YOUR_ID_HERE__"; // 🖍️ VAR
[depersonalized code WITHOUT specific paths]
```

### 📦 Drop-in Component (Black Box)
*Fully self-contained wrapper (no external deps).*

```[language]
class FeatureManager {
  constructor() { ... }
  // Handles context internally
}
```

### 🧪 Self-Test (Micro-Test)
*Validate integration in runtime immediately.*

```[language]
// Copy-paste after component
console.log(new FeatureManager() ? "✅ Live" : "❌ Failed");
```

### ⚡ Critical (won't work without this):
- ✓ **[Critical Point 1]** - [why important]
- ✓ **[Critical Point 2]** - [common mistake]

### 📌 Versions:
- **Works**: [OS/versions where it definitely works]
- **Doesn't Work**: [OS/versions where it definitely doesn't work]

---

## ✔️ Verification (<30 sec)

```bash
[single command to verify]
```

**Expected**:  
✓ [what should happen - specific output/behavior]

**If it didn't work** → see Fallback below ⤵

---

## 🔄 Fallback (if main solution failed)

### Option 1: [approach name]
```bash
[command]
```
**When**: [application condition]

### Option 2: [alternative]
```bash
[command]
```
**When**: [condition] | **Risks**: [what might break]

---

## 💡 Context (optional - read if you need to understand WHY)

**Root Cause**: [1 sentence - why the problem occurs]

**Side Effects**: [what might change after applying]

**Best Practice**: [how to avoid in future - 1 point]

**Anti-Pattern**: ✗ [what NOT to do - common mistake]

---

**Applicable**: [OS, versions, conditions]  
**Frequency**: [rare/common/very common]
```

### 4. Update `.agent/tech_kb/index.json`

1. Read JSON
2. Add entry:
```json
{
  "kb_id": "WIN_TERM_001",
  "title": "PowerShell Async Hang",
  "category": "terminal",
  "platform": "windows",
  "technologies": ["powershell", "cmd"],
  "complexity": 7,
  "criticality": "high",
  "created": "2026-02-11",
  "tags": ["windows", "hang", "async", "utf8"],
  "related_kb": ["WIN_ENC_001"],
  "file_path": "terminal/WIN_TERM_001.md",
  "quick_summary": "PowerShell 7 async hang → use CMD with WaitMs=0",
  "quick_fix": "cmd /c \"chcp 65001 > nul && command\"",
  "diagnostic_time": "5sec",
  "fix_time": "5min"
}
```
3. Update counters + `last_updated`
4. Save

### 5. Output Result

```
✅ ACTIONABLE KB card created!

🆔 WIN_TERM_003
📂 terminal | 🖥️ windows | ⚡ 5 min fix
💾 .agent/tech_kb/terminal/WIN_TERM_003.md ✓

🎯 Quick Fix: cmd /c "chcp 65001 > nul && command"
🔗 Related: WIN_ENC_001, WIN_TERM_001
📊 DB: 56 entries | terminal: 15 | windows: 28
```

---

## 🎯 Rules for ACTIONABLE Cards

### ✅ YES - Quick Application
```markdown
## 🔍 This Is Your Problem If:
- [ ] Command hangs >10 sec
- [ ] PowerShell 7.4+ on Windows
- [ ] WaitMsBeforeAsync is used

## ✅ SOLUTION
### 🎯 Integration Pattern: [Global Scope]

```cmd
cmd /c "chcp 65001 > nul && your_command"
```

### 📦 Drop-in Component
*(Not applicable for one-liners, but essential for code logic)*

### 🧪 Self-Test
```cmd
echo "✅ Test"
```

### ⚡ Critical:
- ✓ **CMD only** - PowerShell 7 has async stdin bug
- ✓ **UTF-8 before command** - otherwise mojibake
```

### ❌ NO - Long Explanations
```markdown
## Problem
User John was working on the GigaAM project and encountered an issue where...
[3 paragraphs of story]

## Solution
We tried different approaches. First we attempted to use PowerShell, but...
[5 paragraphs of debugging process]

cd C:\Users\John\Projects\GigaAM && command
```

### 📐 Principles

1. **Solution FIRST** - after diagnosis, code immediately
2. **Depersonalization** - no names/projects/specific paths
3. **Black Box "Drop-in"** - prefer self-contained class over snippets
4. **Run-time check "Self-Test"** - enable agent to verify fix immediately
5. **Explicit integration point** - tell WHERE to put the code
6. **Use `__VAR__`** - for things that MUST be replaced
7. **Critical Points** - only what will break without it
8. **One Verification** - one command, result in 30 sec
9. **Fallback** - 1-2 options, no more
10. **Context at End** - WHY is optional for curious readers

---

## 📊 Categories (Reference)

**Core**: terminal, encoding, proxy, dependency, config, build, runtime, integration  
**Security**: authentication, authorization, security, certificates, permissions  
**Database**: database, query, migration, transaction  
**Network**: network, api, websocket, cors  
**Storage**: filesystem, memory, disk, cache  
**DevOps**: testing, debugging, git, linting, docker, kubernetes, ci-cd, deployment  
**Frontend**: ui, state-management, bundler  
**Specialized**: ai-agent, concurrency, logging, monitoring, localization

---

## 🔄 MCP Integration

### Request
```js
{"action": "search", "query": "windows terminal hang", "filters": {"platform": "windows"}}
{"action": "get", "kb_id": "WIN_TERM_001"}
```

### Response (optimized for agents)
```json
{
  "kb_id": "WIN_TERM_001",
  "title": "PowerShell Async Hang",
  "tldr": "PowerShell 7 async hang → use CMD",
  "diagnostic": ["hangs >10 sec", "PowerShell 7+", "Windows"],
  "quick_fix": "cmd /c \"chcp 65001 > nul && command\"",
  "critical_points": ["CMD only, NOT powershell", "UTF-8 required"],
  "verification": "echo Test → should output correctly",
  "fallback": ["Option 1: cmd /c command without UTF-8"],
  "fix_time": "5min",
  "related": ["WIN_ENC_001"]
}
```

---

## 🚀 Example of Perfect Card

```markdown
---
kb_id: "WIN_TERM_042"
category: "terminal"
platform: "windows"
technologies: [powershell, cmd, async]
complexity: 7
criticality: "high"
created: "2026-02-11"
tags: [windows, hang, async, utf8, powershell7]
related_kb: [WIN_ENC_001, WIN_PROXY_003]
---

# PowerShell Async Hang

> **TL;DR**: PowerShell 7 hangs on async stdin → use CMD  
> **Fix Time**: ~5 min | **Platform**: Windows 10/11

---

## 🔍 This Is Your Problem If:

- [ ] Agent command hangs >10 seconds
- [ ] PowerShell 7.4+ installed
- [ ] WaitMsBeforeAsync > 0 used

**Where to Check**: console, agent logs, Task Manager (powershell.exe hanging)

---

## ✅ SOLUTION (copy-paste)

### 🎯 Integration Pattern: [Global Scope]

```cmd
# CMD wrapper to bypass PowerShell 7 bug
cmd /c "chcp 65001 > nul && __YOUR_COMMAND__" // 🖍️ VAR
```

### ⚡ Critical (won't work without this):
- ✓ **CMD only** - PowerShell 7.4+ has bug in async stdin handling
- ✓ **UTF-8 before command** - `chcp 65001` required for Cyrillic
- ✓ **WaitMsBeforeAsync: 0** - in run_command agent parameter

### 📌 Versions:
- **Works**: Windows 10/11, CMD.exe
- **Doesn't Work**: PowerShell 7.4+, PowerShell 5 (sometimes)

---

## ✔️ Verification (<30 sec)

```cmd
cmd /c "chcp 65001 > nul && echo Test Cyrillic: Тест"
```

**Expected**:  
✓ Output: `Test Cyrillic: Тест` (correct, no "??????")

**If it didn't work** → see Fallback below ⤵

---

## 🔄 Fallback (if main solution failed)

### Option 1: CMD without UTF-8
```cmd
cmd /c "your_command"
```
**When**: English commands only, UTF-8 not critical

### Option 2: Reinstall PowerShell
```powershell
winget uninstall Microsoft.PowerShell
winget install Microsoft.PowerShell --version 7.3.9
```
**When**: last resort | **Risks**: PS version rollback

---

## 💡 Context (optional)

**Root Cause**: PowerShell 7.4+ contains regression in async stdin handling when invoked via IPC

**Side Effects**: all commands will run via CMD, not PowerShell (this is OK)

**Best Practice**: add rule to user_rules "always use cmd /c for Windows"

**Anti-Pattern**: ✗ Increasing WaitMsBeforeAsync - this masks the problem, doesn't solve it

---

**Applicable**: Windows 10/11, PowerShell 7.4+, AI agents with async execution  
**Frequency**: very common (every Windows user with PS7)
```
