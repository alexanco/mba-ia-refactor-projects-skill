# Audit Report Template

Use this exact format when generating the Phase 2 audit report.

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
Total findings: <N>

## Findings
(sorted by severity: CRITICAL → HIGH → MEDIUM → LOW)

### [<SEVERITY>] <Anti-pattern Name> (AP-XX)
File: <relative/path/to/file.py>:<line_start>-<line_end>
Description: <Specific description of the problem found in THIS codebase>
Code snippet:
  <exact lines from the file showing the problem>
Impact: <Concrete impact for this specific project>
Recommendation: <Specific fix to apply>

### [<SEVERITY>] <Anti-pattern Name> (AP-XX)
...

================================
Total: <N> findings
Estimated refactoring effort: <Low/Medium/High>
================================
```

---

## Format Rules

1. **Severity tag** must be one of: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`
2. **File path** must be the relative path from the project root, followed by `:line_start-line_end`
   - Example: `models.py:28` or `src/AppManager.js:43-78`
3. **Code snippet** must contain the actual lines from the file (not paraphrased)
4. **Description** must be specific to this codebase — not generic
5. **Recommendation** must name the specific transformation to apply (reference the playbook)
6. **Findings must be sorted** by severity (CRITICAL first, LOW last)
7. **Deprecated API findings** should be included as MEDIUM or LOW findings

## Counting Lines of Code

Estimate total lines by summing the line counts of all analyzed source files (excluding blank lines and comments is optional).

## Estimating Refactoring Effort

- **Low:** Mostly config extraction and naming fixes. No structural changes needed.
- **Medium:** Need to reorganize files into MVC structure. Some logic needs to move between layers.
- **High:** God class/file must be split. Multiple CRITICAL security issues. Complete restructuring needed.
