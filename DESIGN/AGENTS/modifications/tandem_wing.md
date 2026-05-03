# Skill: Tandem Wing

## What It Modifies
Replaces the conventional main wing + small tail with two equal or near-equal wings in tandem, both contributing significant lift.

## Parameter in generate.py
Not implemented — requires adding a second main wing GEOM of similar size, repositioning the CG between the two wing aerodynamic centres, and re-evaluating pitch stability with both surfaces generating positive lift.

## Physical Effect
A tandem wing allows both surfaces to lift positively (no tail download penalty), theoretically more efficient. However, the forward wing's downwash on the aft wing and the interference between the two lift surfaces complicates the design. Pitch stability requires the aft wing AC to be behind the CG (between the two wing ACs). Total wetted area is typically higher than a conventional layout.

## How to Apply
Add a second WING geom in generate.py at `x_aft ≈ 2.5–3.0 m` with similar area to the front wing. Place CG between the two ACs. Set `P["rear_wing_span"]`, `P["rear_wing_root_chord"]`, etc. Requires complete CG and stability analysis. Not recommended as a first iteration — high design complexity.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
