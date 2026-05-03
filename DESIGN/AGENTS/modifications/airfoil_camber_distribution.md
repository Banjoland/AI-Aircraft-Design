# Skill: Airfoil Camber Distribution

## What It Modifies
Varies the camber of the airfoil from root to tip, adjusting the local zero-lift AoA across the span.

## Parameter in generate.py
Via airfoil tool — can apply different camber at root vs tip using `airfoil_modifier.py` on individual XSecs.  
Current baseline: same airfoil (default) at all span stations.

## Physical Effect
Increasing camber toward the root raises local CL at zero incidence, loading the root more and unloading the tip — similar in effect to washout but achieved through airfoil geometry rather than twist. A cambered root + symmetric tip combination can produce a near-elliptic lift distribution without geometric twist, which is structurally advantageous (no washout-induced torsional loads).

## How to Apply
Apply a high-camber airfoil (e.g., NACA 4415 or Selig S1223) at the root XSec and a lower-camber or symmetric airfoil (e.g., NACA 0012) at the tip XSec using `airfoil_modifier.py`. OpenVSP will interpolate the shape between sections. Evaluate the resulting spanwise CL distribution in VSPAERO.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
