# Agent: baseline_generator

## Role
You are the aircraft design agent. Your job is to create or modify an OpenVSP aircraft model by editing `generate.py` and running it via the OpenVSP Python launcher.

## Skill: generate_model

### When to use
When asked to create a new aircraft model — either a fresh baseline or a modified version of the current best design.

### Steps
1. Read the current parameter values in the `P` dict at the top of `generate.py`.
2. Apply the requested change (one parameter change per iteration).
3. Run `generate.py` via the OpenVSP launcher:
   ```
   "C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" generate.py
   ```
   Run this from the `DESIGN/AGENTS/baseline_generator/` directory.
4. Capture stdout. Parse the JSON between `{` and `}` — it contains the model summary.
5. Confirm the model file was written to `AIRCRAFT/MODEL_<timestamp>.vsp3`.
6. Report back: model filename, wing_area_m2, vstall_est_ms, wingspan_m, and any constraint violations.

### Outputs
- `AIRCRAFT/MODEL_<timestamp>.vsp3` — the new model file
- `AIRCRAFT/MODEL_<timestamp>.json` — companion metadata for simulation/evaluation tools
- JSON summary on stdout with: model_file, configuration, wing_area_m2, aspect_ratio, pod/boom geometry, vstall_est_ms, wingspan_m, mass estimate, vstall_margin_ok, wingspan_ok

### Constraints (from SPECIFICATION.md)
- Wingspan ≤ 15 m
- V_stall estimate <= 21.0 m/s at MTOW = 218 kg, CL_max = 1.7 (analytic check only; VLM will confirm)
- Engine compartment: 0.8 × 0.6 × 0.6 m minimum
- All flying surfaces must be physically attached to the fuselage

### Current baseline parameters (P dict)
| Parameter | Current value |
|-----------|--------------|
| configuration | pod_and_boom |
| fuse_length | 1.60 m |
| fuse_max_width | 1.10 m |
| fuse_max_height | 0.75 m |
| fuse_taper_width | 0.20 m |
| fuse_taper_height | 0.20 m |
| boom_x | 1.30 m |
| boom_length | 1.90 m |
| boom_diameter | 0.12 m |
| wing_span | 9.80 m |
| wing_root_chord | 0.60 m |
| wing_tip_chord | 0.37 m |
| wing_sweep | 1.0 deg |
| wing_dihedral | 3.0 deg |
| wing_twist | -2.0 deg |
| wing_x | 0.65 m |
| wing_z | 0.0 m |
| htail_span | 1.60 m |
| htail_root_chord | 0.30 m |
| htail_tip_chord | 0.24 m |
| htail_x | 2.85 m |
| vtail_height | 0.70 m |
| vtail_root_chord | 0.40 m |
| vtail_tip_chord | 0.20 m |
| vtail_x | 2.65 m |
| prop_diameter | 1.10 m |

### Test
To verify the tool works:
```
python TEST/run_test.py
```
Expected: PASS, model file created in AIRCRAFT/, vstall_margin_ok and wingspan_ok both true.
