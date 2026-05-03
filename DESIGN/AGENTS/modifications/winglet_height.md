# Skill: Winglet Height

## What It Modifies
Sets the span (height) of the winglet surface above the wingtip.

## Parameter in generate.py
Not implemented — requires winglet geom from `winglet_add.md` to be in place first.  
Proposed parameter: `P["winglet_height"]`, target range 0.3–0.6 m.

## Physical Effect
Taller winglets increase the effective span more, reducing induced drag further. However, structural loads on the wing tip rise with winglet height (bending moment increases). Beyond a height of about 15% of the semi-span, the structural mass penalty begins to exceed the drag reduction benefit. For a 9.8 m span wing, 0.4–0.6 m winglets (8–12% semi-span) are typical.

## How to Apply
After implementing winglet_add.md, set `P["winglet_height"]` and pass it to the winglet TotalSpan parameter in generate.py. Iterate: increase height in 0.05 m steps and evaluate total_cost after each VSPAERO run.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
