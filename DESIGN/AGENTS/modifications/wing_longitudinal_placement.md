# Skill: Wing Longitudinal Placement (Relative to CG)

## What It Modifies
Shifts the wing forward or aft along the fuselage X-axis, changing the CG-to-aerodynamic-centre relationship and longitudinal static margin.

## Parameter in generate.py
`P["wing_x"]` — current default value: 0.65 m (from nose of pod)

## Physical Effect
This is the primary pitch-stability tuning parameter. Moving the wing aft (increasing wing_x) moves the aerodynamic centre aft of the CG, reducing static margin and eventually causing instability. Moving the wing forward (decreasing wing_x) increases static margin (more stable) but requires larger tail download to trim, increasing trim drag. Target: CG at 25–30% of wing MAC, placing the AC approximately 5–10% MAC behind CG.

## How to Apply
Change `P["wing_x"]` in the P dict. After each change, estimate the static margin: AC_x ≈ `P["wing_x"] + 0.25 * P["wing_root_chord"]`; compare to CG_x (pilot + engine + fuel mass-weighted average). Stable margin = (AC_x - CG_x) / wing_MAC > 0.05. Re-run VSPAERO and check Cm vs AoA slope (must be negative for stability).

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
