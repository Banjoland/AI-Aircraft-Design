# Skill: Airfoil Selection (Tip)

## What It Modifies
Sets the airfoil section at the wing tip, controlling tip stall behaviour and spanwise lift distribution.

## Parameter in generate.py
Same tool as root — `DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py` targets all XSecs currently (same airfoil applied to all XSecs in baseline).

## Physical Effect
The tip airfoil operates at a lower Reynolds number (smaller chord). If the same high-camber airfoil as the root is used, the tip may stall first at high AoA (dangerous for roll control). Selecting a slightly thinner or less-cambered airfoil at the tip reduces local CL, delaying tip stall relative to the root — a desirable characteristic. This is an alternative to washout twist for preventing tip stall.

## How to Apply
Modify `airfoil_modifier.py` to accept per-XSec airfoil specification. Apply a root airfoil (e.g., NACA 2415) to XSec_1 and a tip airfoil (e.g., NACA 2412 or NACA 0012) to the outermost XSec. Currently the tool applies the same airfoil to all sections; update to accept a `--tip_airfoil` argument.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
