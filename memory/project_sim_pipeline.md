---
name: project-sim-pipeline
description: Current simulation pipeline status and tooling for aircraft design project
metadata:
  type: project
---

As of 2026-05-18, all SIM_SPEC.md analyses have tooling.

## Full pipeline run order (SIMULATION/SIM_SPEC.md)

1. `openvsp-python DESIGN/AGENTS/spline_aircraft/generate.py` → MODEL + companion JSON
2. `openvsp-python SIMULATION/AGENTS/alpha_sweep/run_sweep.py` → alpha_sweep.json
3. `openvsp-python SIMULATION/AGENTS/beta_sweep/run_beta_sweep.py` → beta_sweep.json
4. `openvsp-python SIMULATION/AGENTS/parasite_drag/analyze.py` → parasite_drag.json
5. `python SIMULATION/AGENTS/inertia_estimator/estimate.py` → inertia.json
6. `python SIMULATION/AGENTS/dynamic_stability/analyze.py` → dynamic_stability.json
7. `python EVALUATION/AGENTS/cost_scorer/score.py` → score.json

Steps 1–4 need OpenVSP Python launcher (`openvsp-python.cmd`). Steps 5–7 are plain Python 3.

## Key design state (LOG iteration 72)

- Last model: MODEL_05_11_2026_10.vsp3 parameters (in generate.py DEFAULT_SPEC)
- Fuselage: 5.0m long, 12 sections, fineness≈4.93
- Empty mass: ~173.9 kg vs 110 kg spec → mass_cost ≈ 332
- Root cause: fuselage wetted area ~10.9 m² at 6 kg/m² skin density

## Stability scoring upgrade (iteration 73)

score.py now uses dynamic eigenvalue distance when available:
- `stability_cost = 1 / min(|λᵢ|)` over all longitudinal modes
- Falls back to Cm_alpha proxy if `_dynamic_stability.json` not present
- Reports `stability_source` field to show which method was used

**Why:** COST FUNCTION.md says "1/distance_from_origin on the s-plane plot" — eigenvalues, not static Cm_alpha.

## Known model files on disk

- `AIRCRAFT/prototype.vsp3` — early prototype (no companion JSON)
- No MODEL_05_11_* files exist on disk; those iterations were documented in LOG but never physically generated/committed
