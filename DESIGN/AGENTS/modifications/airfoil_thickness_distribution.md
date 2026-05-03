# Skill: Airfoil Thickness Distribution

## What It Modifies
Varies airfoil thickness from root to tip, tapering structural depth and profile drag characteristics spanwise.

## Parameter in generate.py
Via airfoil tool — apply different NACA thickness digits at root and tip XSecs.  
Current baseline: same thickness at all span stations.

## Physical Effect
A thick root (t/c 16–18%) provides deep spar section to resist bending efficiently, while a thinner tip (t/c 12–14%) reduces tip wetted area and profile drag where the chord is already small. The resulting taper in both chord and thickness is typical of well-designed sailplane wings. Root thickening also delays root stall, keeping aileron effectiveness at high AoA.

## How to Apply
Apply a thick airfoil at root XSec (e.g., NACA 2418) and a thinner airfoil at tip XSec (e.g., NACA 2412) using `airfoil_modifier.py`. OpenVSP interpolates the cross-section shapes between span stations. This can be combined with the camber distribution skill for a fully spanwise-optimised wing.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
