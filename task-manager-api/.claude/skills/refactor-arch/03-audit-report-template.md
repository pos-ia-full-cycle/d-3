# Audit Report Template

Use this exact format for the Phase 2 audit report output. Fill in all fields based on the actual project being analyzed. Do not omit sections even if they are empty (write "None found" instead).

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework>
Files:   <N analyzed> | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Anti-Pattern Name>
File: <relative/path/to/file.py>:<start_line>-<end_line>
Description: <Concrete description referencing actual variable/function/SQL names found in the code>
Impact: <What can go wrong or what already goes wrong>
Recommendation: <Specific action to fix — name the target pattern or library>

### [CRITICAL] <Next Critical Finding>
File: <file>:<line>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <Anti-Pattern Name>
File: <file>:<line>
Description: ...
Impact: ...
Recommendation: ...

[... repeat for all HIGH findings ...]

### [MEDIUM] <Anti-Pattern Name>
File: <file>:<line>
Description: ...
Impact: ...
Recommendation: ...

[... repeat for all MEDIUM findings ...]

### [LOW] <Anti-Pattern Name>
File: <file>:<line>
Description: ...
Impact: ...
Recommendation: ...

[... repeat for all LOW findings ...]

================================
Total: <total number> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Formatting Rules

1. **Order**: Always CRITICAL first, then HIGH, MEDIUM, LOW — never mix severity levels
2. **File references**: Always use relative paths from the project root (e.g., `src/app.js:45` not `/Users/.../app.js:45`)
3. **Line numbers**: Provide the exact range (`models.py:105-120`) or single line (`app.py:7`) — do not write "around line X"
4. **Description**: Must reference actual code — quote function names, variable names, SQL strings, class names found in the file. Never write generic descriptions.
5. **Total count**: Count every finding including LOW-severity ones

## Example Finding (do not copy verbatim — always use actual project data)

```
### [CRITICAL] SQL Injection
File: models.py:28
Description: Function `get_produto_por_id` builds the SQL query by string concatenation:
  `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
  The `id` parameter comes directly from the URL and is not parameterized.
  Same pattern repeated in `criar_produto` (line 47-50), `login_usuario` (line 109-110),
  and `buscar_produtos` (lines 289-295) — 4 separate injection points.
Impact: Attacker can send `1 OR 1=1` to dump the entire table, or `1; DROP TABLE produtos` to destroy data.
Recommendation: Replace all concatenated queries with parameterized queries using `?` placeholders.
```
