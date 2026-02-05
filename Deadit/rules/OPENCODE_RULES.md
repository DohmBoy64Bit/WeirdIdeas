# OPENCODE_RULES.md

## Purpose
This file defines how the AI must behave in this project.  
It is treated as system instructions and must be loaded on every interaction.

---

## 1. Core Principles (Python-First)

### Architecture
- Primary language: **Python**
- Follow **DRY – Don’t Repeat Yourself**
- Enforce **Separation of Concerns**
- Prefer small, focused modules over large files
- One class → one responsibility
- Prefer composition over inheritance
- Explicit is better than implicit (Pythonic)
- Avoid circular imports and god modules

### File Size Discipline
- No single file should become huge  
- If code can be broken down → **BREAK IT DOWN**
- Create clear layers:
  - domain / business logic  
  - infrastructure  
  - interfaces / API  
  - utilities  
- Extract helpers, services, and models instead of monoliths

---

## 2. Use of Official Documentation ONLY

- When you are unsure about any module, function, or behavior → **consult the OFFICIAL documentation first**
- Do NOT rely on blogs, forum posts, or imagined knowledge
- For Python standard library → use python.org docs
- For third-party packages → use the project’s official docs or repository
- If the docs are unclear → ASK ME instead of guessing
- Never fabricate parameters, return types, or behaviors not explicitly documented
- Prefer quoting/paraphrasing official sources over assumptions

---

## 3. Anti-Hallucination & Uncertainty Rules

- If you do not know something → **SAY you don’t know**
- If something is ambiguous → **ASK me before proceeding**
- Never invent:
  - APIs  
  - business rules  
  - file paths  
  - undocumented behavior  
- Do not guess:
  - library versions  
  - internal utilities  
  - hidden requirements  
- Prefer small clarifying questions over wrong output
- If confidence is below 90% → ask instead of generating

---

## 4. No Scope Creep

- Implement ONLY what was explicitly asked  
- Do not add features “just in case”  
- Do not refactor unrelated code  
- Do not change architecture without approval  
- One problem = one change

---

## 5. Deterministic Style Enforcement

- Prefer existing project patterns over new ones  
- Match surrounding code exactly  
- Simplest working solution by default  
- Do not mix multiple concerns  
- Avoid unnecessary abstractions  
- Keep behavior predictable and reproducible

---

## 6. Hallucination Prevention Checklist

Before responding, verify:

- [ ] I am using real files from the repo  
- [ ] I am not inventing functions or types  
- [ ] I have not assumed hidden requirements  
- [ ] I requested missing context if needed  
- [ ] I consulted OFFICIAL documentation when uncertain  
- [ ] The solution matches existing patterns

If any box is unchecked → ASK THE USER FIRST.

---

## 7. Project Conventions (To Be Auto-Filled)

The AI must derive and maintain:

- Tech stack & dependencies  
- Folder responsibilities  
- Naming conventions  
- Testing approach  
- Commit message style  
- Performance & security rules  
- Do / Don’t examples

---

## 8. Continuous Maintenance

- Always treat this file as system instructions  
- When new conventions appear → propose updates here  
- Ask before violating any rule  
- Keep this file human readable and tool-agnostic

---

## 9. Sources of Truth

Rules must be based on:

- pyproject.toml / requirements / package.json  
- linter & formatter configs  
- folder structure  
- existing code patterns  
- explicit user instructions  
- **OFFICIAL documentation of Python and libraries**

---

## 10. Subagent Governance

All subagents must operate under strict control of the main agent. The following rules apply:

### 10.1 Communication Protocol
- Subagents **do not communicate directly with the user**.  
- All output from subagents is **returned to the main agent** only.  
- The main agent is responsible for interpreting and formatting responses for the user.  

### 10.2 Context and Rules
- Subagents must **receive the relevant portion of OPENCODE_RULES.md** for their task.  
- Subagents **must follow all rules** including:
  - Anti-hallucination and uncertainty rules  
  - DRY and separation of concerns  
  - File size limits and modularization  
  - Deterministic style enforcement  
  - Official documentation research  
- Subagents cannot override or ignore any rules.  

### 10.3 Output Validation
- Main agent must **validate all subagent outputs** before presenting them.  
- If a subagent output conflicts with OPENCODE_RULES.md → main agent must **reject it or ask the user for clarification**.  
- Subagents must never produce speculative code, fake files, or imaginary APIs.  

### 10.4 Handling Uncertainty
- Subagents encountering ambiguous instructions must **signal the uncertainty to the main agent** rather than guessing.  
- The main agent will convert these signals into questions for the user if needed.  

### 10.5 Persistence and Memory
- Subagents **cannot persist memory** between tasks.  
- Only the main agent can propose updates to OPENCODE_RULES.md or store long-term knowledge.  

### 10.6 Task Assignment
- Main agent must assign **narrow, focused tasks** to subagents.  
- Each subagent should have **one clear responsibility**.  
- Multiple subagents can work in parallel, but outputs must always merge through the main agent.

---

**End of Rules**
