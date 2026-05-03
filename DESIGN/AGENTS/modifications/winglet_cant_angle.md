# Skill: Winglet Cant Angle

## What It Modifies
Sets the angle the winglet makes with the vertical (cant angle = 0 deg is perfectly vertical; 90 deg is horizontal = span extension).

## Parameter in generate.py
Not implemented — requires winglet geom. Proposed parameter: `P["winglet_cant_deg"]`, typical range 10–25 deg.

## Physical Effect
A canted winglet (15–25 deg from vertical) balances the drag-reduction benefit of increasing effective span (cant toward horizontal) against the structural efficiency of a near-vertical surface. At 0 deg (vertical), the winglet maximally reduces induced drag per unit height but generates no additional lift. At intermediate cant (15–20 deg), it also generates a small outboard lift component that partially offsets structural bending. Boeing 737 winglets use ~25 deg cant.

## How to Apply
After implementing winglet_add.md, adjust the rotation of the winglet geom from 90 deg (vertical) by `cant_angle` degrees using `_set(winglet_id, "X_Rel_Rotation", "XForm", 90.0 - P["winglet_cant_deg"])`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
