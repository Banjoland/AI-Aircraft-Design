---
name: guideline-modification-registry
description: Audit DESIGN_GUIDELINES.md and map every requested aircraft modification to existing tools, generator parameters, memory documents, and missing implementation work. Use when deciding what tool or skill must be built before modifying aircraft geometry.
compatibility: Designed for this OpenVSP aircraft design project. Requires Python and project markdown files.
---

# Guideline Modification Registry Skill

Use this skill whenever the task mentions implementing all possible guideline
changes, building missing design tools, or checking whether a modification is
already supported.

## Tool

Run:

```powershell
python DESIGN/AGENTS/modification_registry/audit_guidelines.py
```

To create missing design-memory documents:

```powershell
python DESIGN/AGENTS/modification_registry/audit_guidelines.py --scaffold-memory-docs
```

## Workflow

1. Run the audit before starting a new modification-tool build.
2. Inspect `status_counts` and the feature matrix.
3. Prefer building tools for features marked `partial`, `needs_geometry_tool`,
   `needs_architecture_tool`, `needs_airfoil_tool_extension`, or
   `needs_generator_parameter`.
4. Keep existing memory docs; use scaffold mode only to fill missing docs.
5. Record new tools, test results, and coverage changes in `LOG.md`.

## Output

Reports are written to:

```text
DESIGN/AGENTS/modification_registry/out/guideline_capability_audit.json
DESIGN/AGENTS/modification_registry/out/guideline_capability_audit.md
```

## Test

```powershell
python DESIGN/AGENTS/modification_registry/TEST/run_test.py
```
