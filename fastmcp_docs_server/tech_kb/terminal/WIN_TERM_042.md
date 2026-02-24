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
