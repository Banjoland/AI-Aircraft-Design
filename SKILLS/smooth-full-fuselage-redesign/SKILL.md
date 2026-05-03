---
name: smooth-full-fuselage-redesign
description: Replace a pod-and-boom aircraft with a single smooth full-length fuselage, including high attached wing, low engine line, high cockpit at CG, and tail placement for high-wing root-stall buffet cueing.
compatibility: Designed for this OpenVSP aircraft design project. Requires OpenVSP Python.
---

# Smooth Full Fuselage Redesign Skill

Use this skill when a design request asks for a continuous, smooth, full-length
fuselage instead of a separate cockpit pod and tail boom.

## Tool

Run:

```powershell
& "C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" `
  DESIGN/AGENTS/smooth_fuselage_redesign/generate.py `
  AIRCRAFT/MODEL_05_02_2026_05.vsp3
```

Then analyze smoothness:

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/analyze.py AIRCRAFT/<new_model>.json
```

## Workflow

1. Start from the requested source model, not from an unrelated generator state.
2. Preserve wing/tail dimensions unless the request explicitly changes them.
3. Replace `CockpitPod` + `TailBoom` with one `SingleSwoopFuselage`.
4. Use explicit `fuselage_stations` metadata so smoothness can be audited.
   Prefer curve-derived stations over hand-stepped dimensions:
   - one top curve,
   - one bottom curve,
   - one symmetric side half-width curve unless asymmetry is requested.
5. Verify:
   - `single_fuselage_structure == true`
   - `cockpit_vertical_space_m >= 1.5`
   - `pilot_x_m == x_cg_m`
   - `wing_above_cockpit_top_m >= 0`
   - `engine_compartment.meets_spec == true`
   - `fuselage_curve_degree <= 3` unless a higher order is explicitly justified
   - `openvsp_skinning_continuity == "C2"`
   - `fuselage_extension_past_stabilizer_te_m <= 0.4`
   - smoothness report shows no avoidable abrupt pod/boom break
6. Record the model, report, and design consequences in `LOG.md`.

## Test

```powershell
python DESIGN/AGENTS/smooth_fuselage_redesign/TEST/run_test.py
```
