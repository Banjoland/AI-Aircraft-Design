# Agent: beta_sweep

## Role

You are the lateral-directional stability simulation agent.  Your job is to
run a VSPAERO VLM sideslip (beta) sweep on the most recent aircraft model at
a fixed angle of attack, extract the side-force, rolling-moment, and
yawing-moment coefficients across the sideslip range, and report the
lateral-directional stability derivatives.

---

## Purpose

Directional and lateral stability are determined by how the aircraft responds
to a perturbation in sideslip angle (beta — the angle between the velocity
vector and the aircraft longitudinal axis, measured in the horizontal plane).

This agent sweeps beta from -15 deg to +15 deg at a fixed alpha of 4.0 deg
(representative cruise angle of attack) and computes stability derivatives via
linear regression.  The sign conventions follow standard aerospace practice
(right-hand body-axis system, beta positive to the right).

---

## How to run

Run from the `SIMULATION/AGENTS/beta_sweep/` directory.

### Automatically select the most recent model

```
"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" run_beta_sweep.py
```

### Target a specific model

```
"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" run_beta_sweep.py "C:\...\AIRCRAFT\MODEL_xx.vsp3"
```

### Capture and inspect results

The script prints:
- `RESULTS_FILE:<path>` — absolute path to the JSON output file
- `BEGIN_JSON ... END_JSON` — the full JSON summary inline in stdout

Results are also written to `SIMULATION/results/<model_stem>_beta_sweep.json`.

---

## Key output fields

| Field | Units | Description |
|-------|-------|-------------|
| `CY_beta` | /rad | Side-force derivative dCY/d_beta_rad |
| `Cl_beta` | /rad | Rolling-moment derivative dCl/d_beta_rad (dihedral effect) |
| `Cn_beta` | /rad | Yawing-moment derivative dCn/d_beta_rad |
| `directionally_stable` | bool | True if Cn_beta > 0 |
| `dihedral_effect` | bool | True if Cl_beta < 0 |
| `Cn_beta_sign` | string | Human-readable stability verdict for Cn_beta |
| `Cl_beta_sign` | string | Human-readable stability verdict for Cl_beta |
| `sweep_table` | list | Per-beta-point: CY, Cl, Cn, CL_lift |
| `beta_sweep_failed` | bool | True if fewer than 2 valid data points returned |

---

## Physical interpretation of each derivative

### CY_beta — side-force derivative (per radian)
- Defined as dCY/d_beta where beta is in radians.
- A **negative** value is typical and physically correct: positive sideslip
  (nose yawed left relative to the wind) produces a restoring side force to
  the right (negative CY in body axes).
- Dominated by the vertical tail area and fuselage side area.

### Cl_beta — rolling-moment derivative / dihedral effect (per radian)
- Defined as dCl/d_beta where beta is in radians.
- A **negative** value indicates a positive dihedral effect: when the aircraft
  sideslips right (positive beta), the right wing sees a higher effective
  angle of attack and generates more lift, rolling the aircraft left (negative
  Cl in body axes) — a restoring roll moment.
- Negative Cl_beta corresponds to positive geometric dihedral, effective
  sweep, or both.
- If Cl_beta is too large a negative value, the aircraft may be over-stable
  (Dutch roll dominated, uncomfortable handling).

### Cn_beta — directional stability derivative (per radian)
- Defined as dCn/d_beta where beta is in radians.
- A **positive** value means the aircraft is **directionally stable**
  (weathercock stable): when sideslipped to the right, the vertical tail
  produces a restoring yaw moment back to the left (positive Cn in body axes).
- A negative Cn_beta indicates a directionally unstable aircraft that will
  diverge in yaw.
- Dominated by the vertical tail volume coefficient.

---

## Stability quick-reference

| Derivative | Stable sign | Physical mechanism |
|-----------|-------------|-------------------|
| CY_beta   | negative    | Fuselage + vertical tail side force |
| Cl_beta   | negative    | Wing dihedral / sweep dihedral effect |
| Cn_beta   | positive    | Vertical tail weathercock effect |

---

## Reference constants

| Constant | Value | Source |
|----------|-------|--------|
| MTOW_KG | 218 kg | SPECIFICATION.md |
| RHO_SL | 1.225 kg/m3 | Sea-level ISA |
| P_ENGINE_W | 13,423 W | 18 hp, SPECIFICATION.md |
| ALPHA_FIXED | 4.0 deg | Near-cruise hold point |
| BETA range | -15 to +15 deg, 11 pts | 3 deg spacing |
| MACH | 0.15 | Approx. 51 m/s sea level |
| WING_AREA | from companion JSON | Falls back to 6.86 m2 |
| WING_MAC  | from companion JSON | Falls back to 0.71 m |
| X_CG | from companion JSON | Uses `x_cg_m`, then `pilot_x_m`, then 1.35 m fallback |

---

## Known limitations

- VLM is **inviscid** — no boundary-layer or separation effects.  At high
  sideslip angles (|beta| > ~12 deg) real aircraft will show non-linear
  behaviour that VLM cannot capture.
- Dihedral effect (Cl_beta) depends on spanwise lift distribution and sweep;
  VLM captures these geometric effects but not viscous corrections.
- The CG reference input (`X_cg`) is populated from companion JSON when
  available, but OpenVSP 3.49.0 may still warn if the analysis input name is
  unsupported for a particular solver path.
- If `beta_sweep_failed` is True in the results, VSPAERO did not produce valid
  multi-beta results for this model.  All derivatives will be 0.0 and the
  sweep_table will be empty or very short.

---

## Test

```
python TEST/run_test.py
```

Expected output: `PASS`, results file written to
`SIMULATION/results/<model_stem>_beta_sweep.json`, with `Cn_beta` and
`directionally_stable` fields present.
