# Skill: Wing Sweep Angle

## What It Modifies
Sets the quarter-chord sweep angle of the main wing in degrees.

## Parameter in generate.py
`P["wing_sweep"]` — current default value: 1.0 deg

## Physical Effect
Forward sweep (negative) is destabilising in yaw and increases tip load. Aft sweep (positive) improves high-speed stability and moves the aerodynamic centre aft, which may require less horizontal tail trim but shifts lift distribution toward the tip, promoting tip stall. At low subsonic speeds (< 60 m/s), sweep has little aerodynamic benefit and mainly serves to position the wing AC relative to the CG. Large sweep angles increase structural bending/torsion coupling and add mass.

## How to Apply
Change `P["wing_sweep"]` in the P dict. For this low-speed ultralight, values in the range 0–5 deg are appropriate. Larger sweep (10–20 deg) may be used for aesthetic or CG-positioning reasons but will not provide aerodynamic benefits at these speeds. Negative sweep is not recommended without a canard or swept tail for stability.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
