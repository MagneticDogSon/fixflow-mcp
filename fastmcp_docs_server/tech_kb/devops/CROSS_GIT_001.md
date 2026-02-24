---
kb_id: "CROSS_GIT_001"
category: "devops"
platform: "cross-platform"
technologies: [git, github]
complexity: 3
criticality: "medium"
created: "2026-02-17"
tags: [git, merge, conflict, resolve]
related_kb: []
---

# Git Merge Conflict Resolution

> **TL;DR**: Merge conflict in pull request → use rebase + manual resolve
> **Fix Time**: ~10 min | **Platform**: Any OS

---

## 🔍 This Is Your Problem If:

- [ ] `git pull` shows CONFLICT markers
- [ ] PR cannot be merged automatically
- [ ] Files contain `<<<<<<<` markers

**Where to Check**: terminal output, GitHub/GitLab PR page

---

## ✅ SOLUTION (copy-paste)

### 🎯 Integration Pattern: [Event — on merge conflict]

```bash
git fetch origin
git rebase origin/main
git add __CONFLICTED_FILE__
git rebase --continue
git push --force-with-lease
```

### ⚡ Critical:
- ✓ **`--force-with-lease`** — safer than `--force`
- ✓ **Remove ALL conflict markers**
- ✓ **Test after resolve**

---

## ✔️ Verification (<30 sec)

```bash
git log --oneline -5
git diff --check
```

**Expected**: Clean log, no conflict markers

---

## 🔄 Fallback

### Option 1: Merge instead of rebase
```bash
git merge origin/main
```

---

## 💡 Context
**Root Cause**: Divergent changes to same file lines on different branches
