# Skill: Fuselage Maximum Diameter

## What It Modifies
Changes the maximum cross-sectional width and height of the cockpit pod, setting the peak frontal area.

## Parameter in generate.py
`P["fuse_max_width"]` — current default value: 1.10 m  
`P["fuse_max_height"]` — current default value: 0.75 m

## Physical Effect
Increasing either dimension raises frontal (form) drag roughly with the square of diameter and increases wetted area, adding skin-friction drag and structural mass. Reducing these dimensions lowers drag and mass but may violate occupant space constraints. The width-to-height ratio also affects the cabin cross-section shape.

## How to Apply
Change `P["fuse_max_width"]` and/or `P["fuse_max_height"]` together. Keep the ratio close to 1.47 (current) for an elliptical cross-section that minimises interference drag. Verify against the occupant envelope in SPECIFICATION.md before reducing.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
