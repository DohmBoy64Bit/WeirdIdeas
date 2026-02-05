# Activate Persistent Project Ruleset

## Instruction to OpenCode

You must treat **OPENCODE_RULES.md** as persistent system instructions for this project.

### Required Behavior

1. **Load on Every Chat**
   - Always read OPENCODE_RULES.md at the start of every conversation  
   - Treat it as authoritative over any default behavior  

2. **Enforcement**
   - Enforce all rules defined in OPENCODE_RULES.md including:  
     - Anti-hallucination requirements  
     - DRY and Separation of Concerns  
     - File size and modularization discipline  
     - Official-documentation-only research  
     - Deterministic style rules  
     - No scope creep  

3. **When Uncertain**
   - If anything conflicts with OPENCODE_RULES.md → ASK ME FIRST  
   - If context is missing → request files instead of guessing  
   - If confidence < 90% → ask for clarification  

4. **Continuous Improvement**
   - When new conventions appear → propose updates to OPENCODE_RULES.md  
   - Do not silently change behavior  
   - Keep the file human readable and tool-agnostic  

5. **Violation Protocol**
   - Never violate OPENCODE_RULES.md without explicit approval  
   - If asked to do something that conflicts → explain conflict and ask  

### Confirmation Step

Reply with:

- Confirmation that OPENCODE_RULES.md will be loaded every session  
- Summary of enforcement mode activated  
- Any missing context you need from me
