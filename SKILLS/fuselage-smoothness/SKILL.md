---
name: fuselage-smoothness
description: Analyze aircraft fuselage smoothness, curvature, fineness ratio, taper angle, and pressure-recovery drag risk. Use when evaluating fuselage shape, pod-and-boom transitions, cockpit pod taper, tail boom integration, high pressure regions, or when asked to improve fuselage streamlining.
compatibility: Designed for this OpenVSP aircraft design project. Requires Python and the project companion MODEL_*.json files.
---

# Fuselage Smoothness Skill

Use this skill when the task involves fuselage curvature, fuselage drag, pressure recovery, pod-and-boom shape, smooth/elegant fuselage sections, or deciding whether to lengthen or taper a fuselage.

## Tool

Run the project tool:

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/analyze.py
```

To target a specific model:

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/analyze.py AIRCRAFT/MODEL_05_01_2026_62.json
```

The tool writes a JSON report to `EVALUATION/fuselage_reports/`.

## Workflow

1. Read the latest companion `MODEL_*.json` or pass a specific model path.
2. Run the analyzer before changing fuselage length, pod taper, boom diameter, canopy height, or cabin width.
3. Inspect:
   - `max_radius_profile_curvature_1_per_m`
   - `max_profile_slope_angle_deg`
   - `fineness_ratio`
   - `pressure_recovery_risk`
   - `recommendations`
4. Prefer changes that reduce curvature and aft taper angle while keeping cockpit and engine constraints valid.
5. Record the report path and key metrics in `LOG.md`.

## Design Rules

- Aft pressure-recovery taper angles above about 12 degrees are risky.
- Abrupt pod-to-boom radius changes should be replaced with intermediate sections or a longer transition.
- Fineness ratio below 4 is a warning for bluff-body drag unless the shape is intentionally a lifting body or canopy pod.
- Do not use the smoothness score alone. Treat it as a heuristic that guides candidate geometry changes before VSPAERO verification.

## Test

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/TEST/run_test.py
```
