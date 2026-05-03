# Skill: Wing Vertical Placement (High / Mid / Low)

## What It Modifies
Sets the vertical position of the wing root relative to the fuselage centreline, changing the wing-body configuration.

## Parameter in generate.py
`P["wing_z"]` — current default value: 0.0 m (mid-wing)

`DESIGN/AGENTS/smooth_fuselage_redesign/generate.py` sets `wing_z_m` relative
to cockpit top and records `wing_above_cockpit_top_m` plus
`wing_high_attached_to_fuselage`.

## Physical Effect
High-wing placement (positive Z) raises the CG, improves pilot ground visibility downward, and provides natural pendulum stability (reducing required dihedral). Low-wing placement (negative Z) lowers the CG, improves over-wing visibility for the pilot, and is structurally efficient for carry-through spar. Mid-wing gives the lowest interference drag but splits the fuselage structure. For a pod-and-boom ultralight, high-wing placement also improves propeller ground clearance.

## How to Apply
Change `P["wing_z"]` in the P dict. Positive values move the wing upward (high-wing), negative values lower it (low-wing). Typical range: -0.3 to +0.3 m for this fuselage size. Adjust `P["wing_dihedral"]` accordingly: high-wing may need reduced dihedral (1–2 deg) while low-wing typically needs more (4–6 deg).

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Moved wing to high fuselage crown at `z = 1.08 m`, 0.09 m above cockpit top | 18.87 | 46.48 | 2186.7406 | Wing remains attached to the fuselage; beta sweep showed stable yaw but adverse/no dihedral effect (`Cl_beta = +0.02404`) |
| 67 / MODEL_05_02_2026_11 | Kept high attached wing at `z = 1.10 m`, 0.08 m above cockpit top after cockpit/CG shifted aft | 18.90 | 40.17 | 1873.5660 | High wing attachment preserved on curve-skinned fuselage; beta sweep not rerun for this iteration |
