# Skill: Split Winglets (Upper/Lower)

## What It Modifies
Replaces a single winglet with two smaller winglets — one angled upward and one downward from the tip — to reduce drag in both cruise and low-speed conditions.

## Parameter in generate.py
Not implemented — requires two WING geoms at the wingtip, one rotated +90 deg (upper) and one -90 deg (lower) with individual cant angle offsets.

## Physical Effect
Split winglets (as on the Boeing 737 MAX "Split Scimitar" or Airbus A350 "Sharklet") distribute the vortex reduction work between an upper and lower surface, reducing the local velocity perturbation. This provides 1–2% more drag reduction than a single winglet of the same total area, because each smaller surface operates in a less disturbed flow field. The lower winglet must clear the ground during takeoff roll.

## How to Apply
Add upper winglet geom: `X_Rel_Rotation = 90 - upper_cant_deg`. Add lower winglet geom: `X_Rel_Rotation = -(90 - lower_cant_deg)`. For an ultralight, lower winglet ground clearance is a concern; use a large lower cant angle (45 deg from vertical) or omit the lower element. Introduce `P["upper_winglet_height"]`, `P["lower_winglet_height"]`, and `P["upper_cant_deg"]` / `P["lower_cant_deg"]`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
