# Skill: Wing Trailing-Edge Shape

## What It Modifies
Controls the angle and thickness of the wing trailing edge, affecting boundary-layer separation and pressure recovery.

## Parameter in generate.py
Set via airfoil tool (trailing-edge angle is determined by the selected airfoil geometry).

## Physical Effect
A cusped (reflexed) trailing edge reduces the trailing-edge pressure drag and can provide gentle pitching-moment characteristics. A thick, blunt trailing edge (as found on some laminar-flow profiles) increases drag in manufacturing but improves structural stiffness. A very thin, sharp trailing edge (classical NACA sections) is efficient but difficult to manufacture and may delaminate under aerodynamic loads.

## How to Apply
Use `DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py` to select an airfoil with the desired trailing-edge form. Low-speed airfoils like the Eppler E395 or Selig S1223 have well-optimised trailing edges for their Reynolds number range. Examine the airfoil .dat file for trailing-edge thickness before applying.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
