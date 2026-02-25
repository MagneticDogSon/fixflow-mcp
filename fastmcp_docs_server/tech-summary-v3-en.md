---
description: Generate ACTIONABLE KB cards - solution in 5 seconds
---
# Workflow: Instant-Apply KB Cards

**Goal**: Create a card that AI agents can apply in 5 seconds without reading excessive text.
**Format**: Diagnosis (3 sec) -> Solution (copy-paste) -> Verification (30 sec) -> Fallback

---

## Quick Steps

### 1. Chat Analysis -> Extract Key Information
**Required**:
- Category: terminal, encoding, proxy, dependency, config, build, runtime, etc.
- - Platform: windows, linux, macos, cross-platform
  - - Diagnostic Checklist (3 symptoms - how to identify THIS problem)
    - - Ready Solution (code without specific paths)
      - - Critical Points (what will break the solution if missing)
        - - Verification Command (30 sec test)
          - - Fallback (1-2 alternatives)
            - - Integration Pattern (Global/Init/Event - where to put it)
              - **Optional** (if applicable):
              - - Root Cause (WHY - 1 sentence)
                - - Side Effects
                  - - Versions where it works/doesn't work
                    - - Drop-in Component (Self-contained Class/Fn)
                      - - Self-Test (Runtime check snippet)
                       
                        - ### 2. Generate KB_ID
                        - ```
                          Format: [PLATFORM]_[CATEGORY]_[NUMBER]
                          Examples: WIN_TERM_001, CROSS_PROXY_012
                          Number: max ID in category + 1
                          ```

                          ### 3. Create MD Card in .agent/tech_kb/[category]/[KB_ID].md
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

                          ## This Is Your Problem If:
                          - [ ] [Symptom 1 - specific symptom]
                          - [ ] [Symptom 2 - specific error]
                          - [ ] [Symptom 3 - environment condition]

                          **Where to Check**: [console / logs / env / processes]

                          ---

                          ## SOLUTION (copy-paste)

                          ### Integration Pattern: [Global Scope] / [Inside Init Loop] / [Event Handler]

                          ```[language]
                          # [One line - what the code does]
                          const TARGET_ID = "__YOUR_ID_HERE__"; // Var
                          [depersonalized code WITHOUT specific paths]
                          ```

                          ### Package Drop-in Component (Black Box)
                          *Fully self-contained wrapper (no external deps).*

                          ```[language]
                          class FeatureManager {
                            constructor() { ... }
                            // Handles context internally
                          }
                          ```

                          ### Test Self-Test (Micro-Test)
                          *Validate integration in runtime immediately.*

                          ```[language]
                          // Copy-paste after component
                          console.log(new FeatureManager() ? "OK Live" : "Failed");
                          ```

                          ### Fast Critical (won't work without this):
                          - [ok] [Critical Point 1] - [why important]
                          - - [ok] [Critical Point 2] - [common mistake]
                           
                            - ### Note Versions:
                            - - **Works**: [OS/versions where it definitely works]
                              - - **Doesn't Work**: [OS/versions where it definitely doesn't work]
                               
                                - ---

                                ## Verify Verification (<30 sec)

                                ```bash
                                [single command to verify]
                                ```

                                **Expected**: [ok] [what should happen - specific output/behavior]
                                **If it didn't work** -> see Fallback below

                                ---

                                ## Fallback Fallback (if main solution failed)

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

                                ## Tip Context (optional - read if you need to understand WHY)

                                **Root Cause**: [1 sentence - why the problem occurs]
                                **Side Effects**: [what might change after applying]
                                **Best Practice**: [how to avoid in future - 1 point]
                                **Anti-Pattern**: [No] [what NOT to do - common mistake]

                                ---

                                **Applicable**: [OS, versions, conditions]
                                **Frequency**: [rare/common/very common]

                                ### 4. Update .agent/tech_kb/index.json
                                1. Read JSON
                                2. 2. Add entry:
                                   3. ```json
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
                                        "quick_summary": "PowerShell 7 async hang -> use CMD with WaitMs=0",
                                        "quick_fix": "cmd /c \"chcp 65001 > nul && command\"",
                                        "diagnostic_time": "5sec",
                                        "fix_time": "5min"
                                      }
                                      ```
                                      3. Update counters + last_updated
                                      4. 4. Save
                                        
                                         5. ### 5. Output Result
                                         6. ```
                                            Verify ACTIONABLE KB card created!
                                            ID WIN_TERM_003
                                            terminal | System windows | Fast 5 min fix
                                            Save .agent/tech_kb/terminal/WIN_TERM_003.md
                                            [ok] Focus Quick Fix: cmd /c "chcp 65001 > nul && command"
                                            Link Related: WIN_ENC_001, WIN_TERM_001
                                            Stats DB: 56 entries | terminal: 15 | windows: 28
                                            ```
                                            
