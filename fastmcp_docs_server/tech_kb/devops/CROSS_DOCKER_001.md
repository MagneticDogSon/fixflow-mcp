---
kb_id: "CROSS_DOCKER_001"
category: "devops"
platform: "cross-platform"
technologies: [docker, buildx, multi-arch]
complexity: 4
criticality: "high"
created: "2026-02-17"
tags: [docker, exec-format-error, arm64, amd64, multi-arch, buildx]
related_kb: []
---

# Docker exec format error — Wrong Architecture

> **TL;DR**: Container fails with `exec format error` → rebuild image with correct `--platform`
> **Fix Time**: ~5 min | **Platform**: Any OS (common on Apple Silicon M1/M2/M3)

---

## 🔍 This Is Your Problem If:

- [ ] Container exits immediately after `docker run`
- [ ] Error log contains `exec /usr/bin/... : exec format error`
- [ ] You built image on Mac M1/M2 and deploying to Linux x86_64 (or vice versa)
- [ ] Image pulled from registry shows wrong architecture

**Where to Check**: `docker logs <container>`, `docker inspect --format='{{.Architecture}}' <image>`

---

## ✅ SOLUTION (copy-paste)

### 🎯 Integration Pattern: [Build Phase — Dockerfile]

```bash
# Option A: Build for specific platform
docker build --platform linux/amd64 -t __IMAGE_NAME__ .  # 🖍️ VAR

# Option B: Build multi-arch with buildx (recommended)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t __IMAGE_NAME__ --push .  # 🖍️ VAR
```

### ⚡ Critical (won't work without this):
- ✓ **`--platform` flag** — explicitly specify target architecture
- ✓ **buildx** — must be installed (`docker buildx version`)
- ✓ **For existing images** — re-pull with `docker pull --platform linux/amd64 image:tag`

### 📌 Versions:
- **Works**: Docker 20.10+, Docker Desktop 4.x
- **buildx required for**: multi-arch builds

---

## ✔️ Verification (<30 sec)

```bash
# Check image architecture
docker inspect __IMAGE_NAME__ | grep Architecture  # 🖍️ VAR

# Test run
docker run --rm __IMAGE_NAME__ echo "Architecture OK"  # 🖍️ VAR
```

**Expected**:
✓ Architecture shows `amd64` (or your target)
✓ Container prints "Architecture OK" and exits cleanly

**If it didn't work** → see Fallback below ⤵

---

## 🔄 Fallback (if main solution failed)

### Option 1: Use QEMU emulation
```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker run --platform linux/amd64 __IMAGE_NAME__  # 🖍️ VAR
```
**When**: Can't rebuild image, need quick workaround | **Risks**: 5-10x slower performance

### Option 2: Find native image
```bash
# Search for arm64 variant of the image
docker manifest inspect __IMAGE_NAME__  # 🖍️ VAR
```
**When**: Image maintainer provides multi-arch support

---

## 💡 Context (optional)

**Root Cause**: Docker images contain binaries compiled for a specific CPU architecture. Running an amd64 binary on arm64 (or vice versa) causes the kernel to reject the executable format.

**Side Effects**: Multi-arch builds take longer, image size may increase

**Best Practice**: Always specify `--platform` in CI/CD pipelines and Dockerfiles (`FROM --platform=linux/amd64 node:20`)

**Anti-Pattern**: ✗ Using QEMU emulation in production (severe performance penalty)

---

**Applicable**: Docker 20.10+, Apple Silicon Macs, CI/CD cross-compilation
**Frequency**: Very common since Apple M1 release (2020)
