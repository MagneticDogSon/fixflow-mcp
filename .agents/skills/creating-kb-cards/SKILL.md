---
name: creating-kb-cards
description: Generates concise, actionable Knowledge Base (KB) cards for technical problem-solving. Use when documenting bug fixes, solutions, or creating new technical summaries.
---

# Creating Actionable KB Cards

## When to use this skill
- **ALWAYS Proactively**: Immediately after successfully solving a technical issue (debugging, config fix, or complex implementation), you MUST use this skill to preserve the solution. Do not wait for the user to ask.
- **Proactive Threshold**: If the solution involved non-obvious steps, specific commands, or took >2 turns to resolve, assume it remains valuable and needs documentation.
- **Explicit Triggers**: When the user asks to "document this", "save fix", "create KB", or uses `/tech-summary`.

## Workflow

1.  **Analyze Context**: Extract the problem category, platform, symptoms, diagnostic steps, and the solution from the conversation.
2.  **Generate Metadata**: Determine a unique `KB_ID` (format: `PLATFORM_CATEGORY_NUMBER`), criticality, and complexity.
3.  **Draft Content**: Create the Markdown content following the *Strict Priority Order* (Diagnosis -> Solution -> Verification).
4.  **Save & Validate (Server-Side)**: Call the `save_kb_card` MCP tool. This tool will automatically validate the content and save it to the correct location if valid.
5.  **Update Index**: The `save_kb_card` tool automatically updates the index. No manual action required.

## Feedback Loop & Card Evolution

KB cards are **living documents**. After applying a solution from any KB card, you MUST close the feedback loop:

### When you USE a KB card (`read_kb_doc`):

1. **Apply** the solution from the card.
2. **Run** the verification command from `## ✔️ Verification`.
3. **Report the outcome** — call `save_kb_card` in **outcome mode**:
   - `save_kb_card(kb_id="...", outcome="success")` → Solution worked.
   - `save_kb_card(kb_id="...", outcome="failure", enrichment="...")` → Solution failed.

### When the solution did NOT work (`outcome="failure"`):

You are REQUIRED to enrich the card. The `enrichment` parameter should contain:
- **New symptoms** discovered (to add to `## 🔍 This Is Your Problem If`).
- **New fallback option** (to add to `## 🔄 Fallback`).
- **Corrections** to the original solution (if commands changed, versions updated, etc.).
- **Platform-specific notes** (e.g., "Does not work on Windows 11 24H2").

The server will automatically insert the enrichment into the card content and update usage metrics.

### Metrics tracked per card:
| Metric | Description |
|---|---|
| `applied_count` | Total times the card was applied |
| `solved_count` | Times the solution worked as-is |
| `failed_count` | Times the solution did not work |
| `success_rate` | `solved_count / applied_count * 100` |

> **Rule**: If `success_rate` drops below 50%, the card should be reviewed and rewritten.

### Full Lifecycle Example:
```
1. Agent encounters error "exec format error"
2. → resolve_kb_id("exec format error")       → finds CROSS_DOCKER_001
3. → read_kb_doc("CROSS_DOCKER_001")           → gets solution + metrics + related
4. → Applies solution, runs verification
5a. ✅ Works → save_kb_card(kb_id="CROSS_DOCKER_001", outcome="success")
5b. ❌ Fails → Agent debugs, finds extra step
    → save_kb_card(kb_id="CROSS_DOCKER_001", outcome="failure",
        enrichment="### Option 3: Enable containerd image store\n
        Docker Desktop > Settings > Features > 'Use containerd'\n
        Required on Docker Desktop 4.35+ for buildx multi-arch.")
6. Card is automatically enriched for the next agent.
```

## Instructions

### 1. KB_ID Generation Rule
Format: `[PLATFORM]_[CATEGORY]_[NUMBER]`
- **Examples**: `WIN_TERM_001`, `CROSS_PROXY_012`
- **Number**: Increment the max ID found in the category.

### 2. Save & Validation (Server-Side)
You MUST use the `save_kb_card` MCP tool.
- **Tool**: `save_kb_card`
- **Input**: The full markdown string.
- **Process**: The server validates the content and saves the file.
- **Success**: Returns a success message with the file path.
- **Fail**: Returns an error message. Fix and retry.
**DO NOT use manual file writing tools.**

### 3. Content Structure (Strict Priority)

Your output MD file MUST follow this structure:

1.  **Frontmatter**:
    - `kb_id`, `category`, `platform`, `technologies` (list), `complexity` (1-10), `criticality` (low/medium/high/critical), `created` (YYYY-MM-DD), `tags`, `related_kb`.
2.  **Title & TL;DR**:
    - Short, descriptive title (max 5 words).
    - "TL;DR" block with Fix Time and Platform.
3.  **🔍 This Is Your Problem If**:
    - 3 specific symptoms (checkboxes).
    - "Where to Check" line.
4.  **✅ SOLUTION (copy-paste)**:
    - **Integration Pattern**: Explicitly state where to put the code (Global/Init/Event).
    - **Code**: Depersonalized, using `__VAR__` for placeholders.
    - **Drop-in Component** (if applicable): Self-contained class/fn.
    - **Self-Test**: Runtime check snippet.
    - **Critical Points**: What breaks if missing.
5.  **✔️ Verification**:
    - Single command (<30 sec execution).
    - Expected output.
6.  **🔄 Fallback**:
    - 1-2 alternative options if the main solution fails.
7.  **💡 Context**:
    - Root cause (optional, at the end).

### 4. "Actionable" Rules
- **Solution FIRST**: Code comes immediately after diagnosis.
- **Depersonalization**: No specific paths or user names. Use `__VAR__` if needed.
- **Black Box**: Prefer self-contained wrappers over snippets.
- **Verification**: MUST have a verification command.
- **Fix Time**: Estimate realistic fix time (e.g., "5min").

### 5. MCP Server Installation
If access to the MCP server is available:
- **Requirement**: You MUST use the server to install the KB card.
- **Action**: Use `save_kb_card`.

## Template

```markdown
---
kb_id: "WIN_TERM_042"
title: "Terminal Hangs on Async Command"
category: "terminal"
platform: "windows"
technologies: [powershell, cmd]
complexity: 7
criticality: "high"
created: "2026-02-11"
tags: [windows, hang, async]
related_kb: []
---

# [Title]

> **TL;DR**: [Problem] → [Solution]
> **Fix Time**: ~5 min | **Platform**: Windows

---

## 🔍 This Is Your Problem If:

- [ ] [Symptom 1]
- [ ] [Symptom 2]

**Where to Check**: [Logs/Console]

---

## ✅ SOLUTION (copy-paste)

### 🎯 Integration Pattern: [Global/Init/Event]

```bash
[Command or Code]
```

### ⚡ Critical:
- ✓ **[Point 1]**
- ✓ **[Point 2]**

---

## ✔️ Verification (<30 sec)

```bash
[Verification Command]
```

**Expected**: [Output]

---

## 🔄 Fallback

### Option 1: [Alternative]
```bash
[Command]
```

---

## 💡 Context
**Root Cause**: [Brief explanation]
```

## Resources

- **Only 3 Tools** (minimal, powerful):
  - `resolve_kb_id(query, category)` — **FIND**: Search, browse by category, or get KB stats overview
  - `read_kb_doc(kb_id)` — **READ**: Full card content + reliability metrics + related cards
  - `save_kb_card(content | kb_id+outcome)` — **WRITE**: Save new card OR report outcome after applying
- **Categories**: terminal, security, database, network, storage, devops, frontend, core, mcp-deployment, supabase, specialized.
- **Server enforces**: YAML fields (`kb_id`, `title`, `category`, `tags`) + Markdown sections (`🔍 Diagnosis`, `✅ Solution`, `✔️ Verification`).
- **Search**: PostgreSQL FTS (tsvector) across title, content, tags, category. Ranked by relevance + success rate.

