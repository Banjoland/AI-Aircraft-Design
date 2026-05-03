# Skill: Wing Leading-Edge Shape

## What It Modifies
Controls the curvature and radius of the wing leading edge, affecting stall behaviour and low-speed lift.

## Parameter in generate.py
Set via airfoil tool (leading-edge radius is determined by airfoil family and thickness).  
A thicker or more cambered airfoil generally has a larger leading-edge radius.

## Physical Effect
A sharp leading edge (thin, low-camber airfoil) produces leading-edge separation at moderate AoA, causing an abrupt stall. A round leading edge (thick airfoil, high leading-edge radius) promotes leading-edge suction and delays separation to higher AoA, giving a gentler stall break with higher CLmax. For a low-speed ultralight, a round leading edge is strongly preferred for safety.

## How to Apply
Use `DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py` to apply an airfoil with a larger leading-edge radius. NACA 4-digit series: increase thickness digit (12→15→18%) to enlarge the leading-edge radius. Alternatively, use a Selig or Eppler low-speed profile with an explicitly optimised leading edge. Check stall AoA and CLmax via XFLR5 analysis.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
