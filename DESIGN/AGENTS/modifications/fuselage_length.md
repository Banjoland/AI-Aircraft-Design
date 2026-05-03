# Skill: Fuselage Length

## What It Modifies
Changes the total length of the cockpit pod fuselage from nose to aft taper.

## Parameter in generate.py
`P["fuse_length"]` — current default value: 1.6 m

For single-body redesigns, `DESIGN/AGENTS/smooth_fuselage_redesign/generate.py`
uses `fuse_length_m` in the companion JSON and writes explicit
`fuselage_stations` from nose to tail closeout.

## Physical Effect
Increasing fuselage length reduces the rate of cross-sectional area change (lower fineness curvature), which reduces pressure drag. A longer fuselage increases wetted area, raising skin-friction drag and shell mass. There is an optimal length where total drag is minimised for a given cross-section.

## How to Apply
Change `P["fuse_length"]` in the P dict. Increasing this value stretches the pod and shifts the aft taper rearward. Monitor `total_wetted_area_m2` and `empty_mass_est_kg` in the summary JSON to ensure the empty-mass budget is not exceeded.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Replaced pod-and-boom with one 6.0 m full-length smooth fuselage | 18.87 | 46.48 | 2186.7406 | Geometry request satisfied, but wetted area rose to 24.43 m2 and empty mass to 194.6 kg; mass dominates cost |
| 67 / MODEL_05_02_2026_11 | Shortened/refined curve-skinned full fuselage to 5.6 m and reduced aft stabilizer overhang to 0.345 m | 18.90 | 40.17 | 1873.5660 | Shorter tail overhang and better packaging; still heavy and high-drag |
