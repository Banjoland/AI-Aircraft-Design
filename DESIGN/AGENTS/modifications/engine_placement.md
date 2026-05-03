# Skill: Engine Placement

## What It Modifies
Moves the engine and propeller disk from the nose tractor position to an alternative location (wing-mounted or aft pusher).

## Parameter in generate.py
`P["prop_x"]` — current default value: -0.05 m (nose tractor)  
Aft pusher configuration not yet implemented — requires relocating prop geom to `prop_x ≈ boom_x + boom_length` and reversing thrust direction.

`DESIGN/AGENTS/smooth_fuselage_redesign/generate.py` stores `engine_x_m` and
`engine_z_m` for low-engine single-fuselage layouts.

## Physical Effect
A nose tractor configuration keeps the propeller slip-stream over the wing, increasing effective dynamic pressure and thus lift at low speed. An aft pusher eliminates the propeller wake over the fuselage but may cause cooling and CG issues. Wing-mounted engines increase wetted area and structural mass substantially. For a lightweight ultralight, nose tractor is typically optimal.

## How to Apply
For nose tractor: adjust `P["prop_x"]` slightly (–0.10 to 0.0 m) to fine-tune clearance.  
For aft pusher: change `P["prop_x"]` to approximately `P["boom_x"] + P["boom_length"] + 0.1`, add a rotation of 180° on X-axis for the prop geom, and rebalance CG.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Kept tractor prop/engine low at `z = -0.30 m` while cockpit and wing rise above it | 18.87 | 46.48 | 2186.7406 | Satisfies low-engine visual/packaging requirement; thrust-line-to-CG effects still need dedicated analysis |
| 67 / MODEL_05_02_2026_11 | Moved low engine bay center aft to `x = 1.35 m`, `z = -0.18 m` and sized bay to spec | 18.90 | 40.17 | 1873.5660 | Engine compartment is 0.8 m long with min 0.660 m width and 0.680 m height; thrust-line-to-CG analysis still needed |
