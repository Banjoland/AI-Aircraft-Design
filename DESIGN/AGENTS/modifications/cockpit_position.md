# Skill: Cockpit Position

## What It Modifies
Shifts the cockpit (and therefore pilot CG) forward or aft relative to the wing aerodynamic centre.

## Parameter in generate.py
Not directly parameterised — `P["wing_x"]` (currently 0.65 m) shifts the wing relative to the pod, which indirectly changes the CG margin. A dedicated `P["cockpit_x"]` offset is not yet in P.

`DESIGN/AGENTS/smooth_fuselage_redesign/generate.py` writes explicit
`x_cg_m` and `pilot_x_m` metadata for full-fuselage redesigns.

## Physical Effect
Moving the cockpit forward increases the nose-heavy moment, requiring a larger horizontal tail download to trim, which increases trim drag. Moving it aft reduces the tail trim load but shrinks the static margin, risking pitch instability. The ideal position places the CG at 25–30% of the wing MAC with the current tail volume.

## How to Apply
Adjust `P["wing_x"]` to shift the wing aft (increasing wing_x) or forward (decreasing wing_x) relative to the fixed cockpit/CG. Alternatively, add `P["cockpit_x_offset"]` to the fuselage XForm in generate.py. Always re-evaluate static margin after changing this parameter using the VSPAERO output pitching-moment coefficient.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Placed pilot station at `x_cg_m = pilot_x_m = 2.35 m` with 1.5 m cockpit height | 18.87 | 46.48 | 2186.7406 | Metadata and geometry satisfy pilot-at-CG request; VSPAERO still ignores attempted CG input names, so moment reference needs tool fix |
| 67 / MODEL_05_02_2026_11 | Shifted pilot/CG station aft to `x_cg_m = pilot_x_m = 2.65 m` within curve-skinned cockpit | 18.90 | 40.17 | 1873.5660 | Maintains 1.5 m cockpit height and high wing over cockpit; VSPAERO CG reference warning remains |
