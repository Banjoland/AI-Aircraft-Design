# Agent: alpha_sweep

## Role
You are the aerodynamic simulation agent. Your job is to run a VSPAERO VLM alpha sweep on the most recent aircraft model and extract the aerodynamic polar plus stability and performance metrics.

## Skill: run_alpha_sweep

### When to use
When asked to simulate the aerodynamics of the current aircraft model — either after a new model is generated or to re-evaluate after a geometry change.

### Steps
1. Identify the most recent `MODEL_*.vsp3` in `AIRCRAFT/` (newest by modification time). If a specific model path is given, use that.
2. Run `run_sweep.py` via the OpenVSP launcher:
   ```
   "C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" run_sweep.py
   ```
   Run this from the `SIMULATION/AGENTS/alpha_sweep/` directory. To target a specific model:
   ```
   "C:\...\openvsp-python.cmd" run_sweep.py "C:\...\AIRCRAFT\MODEL_xx.vsp3"
   ```
3. Capture stdout. The results file path is emitted as `RESULTS_FILE:<path>`. The JSON summary is between `BEGIN_JSON` and `END_JSON` sentinels.
4. Confirm the results file was written to `SIMULATION/results/<model_stem>_alpha_sweep.json`.
5. Report back: model name, V_stall, V_cruise, Cm_alpha, longitudinal_stable, and whether vstall_ok.

### Outputs
- `SIMULATION/results/<model_stem>_alpha_sweep.json` — full polar + derived metrics
- JSON summary on stdout (between `BEGIN_JSON` / `END_JSON`) with the fields listed below

### Key output fields
| Field | Description |
|-------|-------------|
| `polar` | 11-point table: alpha_deg, CL, CD, CM (CMytot), L/D |
| `CL_alpha_per_deg` | Lift curve slope (linear fit) |
| `Cm_alpha_per_deg` | Pitching moment slope — negative = longitudinally stable |
| `CL_max_vlm` | Peak CL from the alpha sweep |
| `vstall_est_ms` | V_stall = sqrt(2W / rho S CL_max) at MTOW=218 kg, sea level |
| `vstall_ok` | True if vstall_est_ms <= 21.0 m/s |
| `vcruise_75pct_ms` | Cruise speed at 75% engine power (bisection solve) |
| `LD_cruise` | L/D at cruise |
| `longitudinal_stable` | True if Cm_alpha_per_deg < 0 |

### Reference constants (hard-coded in run_sweep.py)
| Constant | Value | Notes |
|----------|-------|-------|
| MTOW_KG | 218 kg | From SPECIFICATION.md |
| RHO_SL | 1.225 kg/m³ | Sea-level ISA |
| P_ENGINE_W | 13,423 W | 18 hp from SPECIFICATION.md |
| WING_AREA | read from model companion JSON | Falls back only if JSON is missing |
| WING_MAC | read from model companion JSON | Falls back only if JSON is missing |
| X_CG | read from model companion JSON | Uses `x_cg_m`, then `pilot_x_m`, then 1.35 m fallback |
| VSTALL_LIMIT | 21.0 m/s | From SPECIFICATION.md |

> **Important:** `WING_AREA` and `WING_MAC` are now read from the companion JSON written by `generate.py`, so batch geometry changes stay synchronized with simulation.

### Known limitations
- VLM is inviscid — CDtot is induced drag only. Absolute CD is a lower bound; profile drag is not modelled.
- CL can be non-monotonic at very low alpha (−4° to 0°) due to fuselage/prop-disk VLM interference. Alpha > 2° is most reliable.
- The CG reference input still produces OpenVSP warnings in 3.49.0 and should be fixed before deeper stability optimization.

### Test
```
python TEST/run_test.py
```
Expected: PASS, results file created in `SIMULATION/results/`, vstall_ok and longitudinal_stable values present.
