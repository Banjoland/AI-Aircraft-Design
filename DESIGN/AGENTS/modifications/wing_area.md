# Skill: Wing Area

## What It Modifies
Changes the total planform area of the main wing, directly setting stall speed and wing loading.

## Parameter in generate.py
Derived from span and chord: `wing_area = P["wing_span"] * 0.5 * (P["wing_root_chord"] + P["wing_tip_chord"])`  
Current baseline: 9.8 × 0.5 × (0.60 + 0.37) = 4.75 m²

## Physical Effect
Larger wing area reduces stall speed (W/S decreases) and improves low-speed performance but increases wetted area, skin-friction drag, and structural mass. Smaller area increases stall speed and wing loading, raising cruise efficiency but risking violation of the stall-speed specification. Minimum area for stall limit compliance: ~4.65 m² (computed in generate.py as S_MIN_M2).

## How to Apply
Adjust `P["wing_root_chord"]` and/or `P["wing_tip_chord"]` proportionally to change area while holding aspect ratio. Alternatively, adjust `P["wing_span"]` while holding chord. Always verify `vstall_est_ms < 21.0` in the summary JSON after any area change.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
