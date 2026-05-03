# Skill: Aspect Ratio

## What It Modifies
Controls the ratio of wingspan squared to wing area, governing induced drag efficiency.

## Parameter in generate.py
Derived: `AR = P["wing_span"]**2 / wing_area`  
Current baseline: 9.8² / 4.75 ≈ 20.2 (sailplane class)

## Physical Effect
Induced drag coefficient CDi = CL²/(π·e·AR). Doubling AR halves induced drag at any given CL. High AR wings are optimal for slow, efficient flight but suffer structural penalties (heavier spar, higher bending moment) and may have aeroelastic issues. The current AR of ~20 is already very high; going beyond 25 yields diminishing aerodynamic returns relative to the mass penalty.

## How to Apply
Increase AR by increasing `P["wing_span"]` while holding chord (wing_area grows with span). Alternatively, reduce chord (decrease wing_root_chord/wing_tip_chord) while holding span, which increases AR but reduces wing area and raises stall speed. Always verify stall speed compliance when modifying AR.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
