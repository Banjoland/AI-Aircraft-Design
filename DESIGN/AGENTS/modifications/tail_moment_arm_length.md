# Skill: Tail Moment Arm Length

## What It Modifies
Tail moment arm length

## Current Implementation Path
Status: `implemented`

tail x-location and boom length overrides

## Parameters / Tools
Parameters: `htail_x`, `vtail_x`, `boom_length`

Tools:
- `DESIGN/AGENTS/baseline_generator`

## How To Apply
Use the implementation path above if it is marked `implemented` or `partial`.
If the status starts with `needs_`, build or extend the listed tool before using
this modification in a design iteration.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| - | Baseline | - | - | - | No data yet |
| 66 / MODEL_05_02_2026_07 | Moved horizontal tail aft to `x = 4.70 m`, `z = 0.92 m` on a 6.0 m single fuselage | 18.87 | 46.48 | 2186.7406 | Tail is placed aft and slightly below the high wing root wake line for stall buffet cueing; dynamic buffet itself is not modeled by VLM |
| 67 / MODEL_05_02_2026_11 | Moved horizontal tail to `x = 4.85 m`, vertical tail to `x = 4.80 m`, and shortened fuselage overhang to 0.345 m | 18.90 | 40.17 | 1873.5660 | Fixes excessive aft fuselage extension while keeping tail in high-wing root wake cueing position |
