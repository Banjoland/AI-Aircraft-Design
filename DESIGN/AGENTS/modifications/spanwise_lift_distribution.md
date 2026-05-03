# Skill: Spanwise Lift Distribution

## What It Modifies
Controls how lift is distributed along the wing span, targeting an elliptical distribution for minimum induced drag.

## Parameter in generate.py
Controlled by the combination of `P["wing_twist"]`, `P["wing_tip_chord"]`/`P["wing_root_chord"]` (taper ratio), and `P["wing_sweep"]`.  
Not a single parameter — an emergent result of all three.

## Physical Effect
An elliptic spanwise CL distribution minimises induced drag for any given total lift and span. It is achieved through some combination of elliptic planform, taper + twist, or variable camber distribution. Deviations toward tip-loaded distributions increase induced drag; deviations toward root-loaded distributions are less efficient but safer (root stalls first, aileron control retained).

## How to Apply
Run VSPAERO and examine the `span_load` table in the output (CL vs y/b). Compare to the ideal elliptic distribution. If tip-loaded: increase washout twist or reduce taper ratio. If root-loaded: reduce washout or increase taper ratio. For the current baseline, reducing taper ratio from 0.617 toward 0.45 and increasing washout from -2 to -3 deg should bring the distribution closer to elliptic.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
