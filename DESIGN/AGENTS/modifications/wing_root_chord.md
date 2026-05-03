# Skill: Wing Root Chord

## What It Modifies
Sets the chord length at the wing root (fuselage centreline), directly affecting wing area and taper ratio.

## Parameter in generate.py
`P["wing_root_chord"]` — current default value: 0.60 m

## Physical Effect
Increasing root chord raises wing area (lowering stall speed), deepens the root airfoil section (improving spar structural efficiency), and increases wetted area. It also changes the taper ratio for a fixed tip chord. A larger root chord relative to tip chord shifts lift inboard, which reduces the bending moment but moves the spanwise lift distribution away from elliptical.

## How to Apply
Change `P["wing_root_chord"]` in the P dict. For area-neutral change: scale tip chord proportionally to maintain taper ratio. After changing, verify stall speed and aspect ratio in the summary JSON. Typical root chord for this aircraft class: 0.50–0.75 m.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
