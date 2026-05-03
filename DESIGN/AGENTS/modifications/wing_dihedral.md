# Skill: Wing Dihedral Angle

## What It Modifies
Sets the upward angle of the wing panels from the horizontal, providing roll stability.

## Parameter in generate.py
`P["wing_dihedral"]` — current default value: 3.0 deg

## Physical Effect
Dihedral creates a restoring roll moment when the aircraft sideslips: the lower wing sees higher effective AoA, generating more lift and rolling the aircraft level. Too little dihedral (< 2 deg for a low-wing aircraft) gives sluggish roll stability. Too much (> 7 deg) makes the aircraft overly responsive to gusts (Dutch-roll prone). The current 3 deg is appropriate for a mid-wing pod-and-boom configuration.

## How to Apply
Change `P["wing_dihedral"]` in the P dict. For a low-wing layout, 3–5 deg is standard. For a high-wing layout, 1–2 deg is typical (the high-wing position itself provides pendulum stability). Increasing dihedral beyond the baseline has minimal drag effect but may require VT sizing adjustment to manage Dutch-roll tendency.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
