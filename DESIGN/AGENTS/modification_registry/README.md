# Agent: modification_registry

## Role

This agent turns `DESIGN/DESIGN_GUIDELINES.md` into an actionable capability map.
It audits every feature listed under "Features That Can Be modified" and checks:

- whether a design-memory document exists,
- whether an implementation path is registered,
- whether the feature has a dedicated tool directory,
- which current parameters/tools can perform or partially perform the change.

## Why It Exists

The project requires enough tools and skills to eventually implement every listed
aircraft modification. A registry prevents silent gaps: if a feature exists in
the guidelines, it must appear in this audit with a status and next action.

## Usage

From the project root:

```powershell
python DESIGN/AGENTS/modification_registry/audit_guidelines.py
```

Write the default reports:

```text
DESIGN/AGENTS/modification_registry/out/guideline_capability_audit.json
DESIGN/AGENTS/modification_registry/out/guideline_capability_audit.md
```

To also create missing design-memory docs:

```powershell
python DESIGN/AGENTS/modification_registry/audit_guidelines.py --scaffold-memory-docs
```

The scaffold mode only creates missing files under:

```text
DESIGN/AGENTS/modifications/
```

It does not overwrite existing memory docs.

## Status Meanings

| Status | Meaning |
|---|---|
| `implemented` | Existing generator/tool can perform the modification directly |
| `partial` | Current tools can influence it, but a dedicated tool is still needed |
| `needs_geometry_tool` | Requires OpenVSP geometry editing beyond current parameters |
| `needs_architecture_tool` | Requires a new aircraft architecture generator |
| `needs_mass_cg_tool` | Requires explicit mass/CG/inertia modeling |
| `needs_airfoil_tool_extension` | Requires extending the airfoil tool to more surfaces or sections |
| `needs_generator_parameter` | Generator needs a new exposed parameter |
| `unmapped` | The registry has not yet assigned an implementation path |

## Test

```powershell
python DESIGN/AGENTS/modification_registry/TEST/run_test.py
```

Expected: PASS, with a test audit written under `TEST/out/`.
