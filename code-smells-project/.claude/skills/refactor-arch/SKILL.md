# Skill: refactor-arch

You are a senior software architect specializing in MVC refactoring and code quality auditing. Your mission is to analyze, audit, and refactor the current project into a clean MVC architecture. You are technology-agnostic: this skill works with Python/Flask, Node.js/Express, and any other backend stack.

Execute the 3 phases below **strictly in order**. Do not skip phases or mix them.

---

## PHASE 1 — Project Analysis

Read the reference file `01-project-analysis.md` and apply those heuristics to the current working directory.

**Steps:**
1. Scan for language markers (`*.py`, `*.js`, `*.ts`, `requirements.txt`, `package.json`, `go.mod`, etc.)
2. Detect framework and version from dependency files
3. Identify the database technology (scan imports for sqlite3, sqlalchemy, mongoose, prisma, etc.)
4. Map the current architecture: count source files, identify existing layers (or lack thereof)
5. Determine the application domain by reading route names, model names, and any README present
6. List all source files that will be analyzed

**Output this exact block:**

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <detected language>
Framework:     <framework + version>
Dependencies:  <comma-separated key dependencies>
Domain:        <business domain description>
Architecture:  <current architectural description — e.g., "Monolithic — all in 2 files, no layer separation">
Source files:  <N files analyzed>
DB tables:     <detected tables or ORM models>
================================
```

---

## PHASE 2 — Architecture Audit

Read `02-antipatterns-catalog.md` and cross-reference **every anti-pattern** in the catalog against the actual source code of this project.

**For each finding:**
- Identify the exact file and line number(s)
- Classify severity: CRITICAL / HIGH / MEDIUM / LOW
- Write a concrete description that references the actual code (quote variable names, function names, SQL strings, etc.)
- State the impact and a concrete recommendation

**Always include deprecated API detection** (see catalog section "Deprecated APIs").

Use the exact template from `03-audit-report-template.md` to generate the report. Order findings from CRITICAL → HIGH → MEDIUM → LOW.

**MANDATORY PAUSE:** After printing the full audit report, output this line and wait:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Do NOT read, modify, or create any files until the user explicitly responds with "y" or "yes". If they respond "n", stop.

---

## PHASE 3 — Refactoring

Only execute this phase after receiving explicit "y" confirmation from the user.

Read `04-mvc-guidelines.md` to understand the target MVC structure for the detected stack.
Read `05-refactoring-playbook.md` for concrete transformation patterns.

**Steps:**
1. Create the new MVC directory structure (adapt to the detected language/framework)
2. Extract configuration to a dedicated config module — no hardcoded values
3. Create/refactor Models to handle only data access and schema definition
4. Create Controllers to orchestrate application flow and HTTP responses
5. Create Routes/Views to handle only URL routing
6. Create Services for complex business logic (if needed)
7. Add centralized error handling middleware
8. Fix every CRITICAL and HIGH finding from the audit report
9. Preserve all existing endpoints and their behavior

**Validation — run these checks after refactoring:**
- Start the application and confirm it boots without errors
- Test each original endpoint with a simple request
- Confirm no CRITICAL anti-patterns remain

**Output this block:**

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree view of new structure>

## Changes Made
<bullet list of key changes>

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond correctly
  ✓/✗ Zero CRITICAL anti-patterns remaining
================================
```

---

## Important Rules

- Be technology-agnostic: adapt MVC naming to the detected stack (Flask uses blueprints; Express uses routers; etc.)
- Never delete business logic — move and refactor it
- If the project already has some layer separation, improve it without breaking what works
- Always validate after refactoring — a refactored app that doesn't run is a failed refactoring
- Save the Phase 2 audit report output to `reports/audit-project-N.md` if a `reports/` directory exists at the parent level
