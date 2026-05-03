# Skill: Wing Height (Vertical Position)

## What It Modifies
This is the same control as wing vertical placement — sets the Z-axis position of the wing root relative to the fuselage centreline.

## Parameter in generate.py
`P["wing_z"]` — current default value: 0.0 m  
*(This skill is an alias for `wing_vertical_placement.md` — see that file for full details.)*

## Physical Effect
Same as wing vertical placement. The vertical position affects dihedral effect, interference drag at the wing-body junction, structural carry-through path, and CG height. High-wing placement provides natural pendulum stability; low-wing provides easy structural integration with a floor-level spar box.

## How to Apply
Change `P["wing_z"]` in the P dict. Positive = high wing, negative = low wing. For full analysis, see `wing_vertical_placement.md`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
