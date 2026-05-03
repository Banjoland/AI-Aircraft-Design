# Skill: Leading-Edge Radius

## What It Modifies
Sets the radius of curvature at the airfoil leading edge, which determines the stall onset angle and maximum lift coefficient.

## Parameter in generate.py
Controlled by airfoil selection (thickness and shape parameter in NACA/Selig/Eppler families) — not a direct P dict parameter.

## Physical Effect
A larger leading-edge radius allows the flow to negotiate higher local curvature before separating, delaying leading-edge stall to higher AoA and increasing CLmax. NACA 4-digit airfoils have a leading-edge radius proportional to thickness: r_LE ≈ 1.1019 * (t/c)² * c. Thin airfoils (t/c < 10%) have negligible leading-edge radius and stall sharply. For a safe ultralight, t/c ≥ 12% (giving r_LE ≥ 1.3% chord) is recommended.

## How to Apply
Use `airfoil_modifier.py` to select an airfoil with sufficient thickness. Cross-check the leading-edge radius from the NACA formula or from the Selig .dat file shape. For maximum CLmax at the low Reynolds numbers of this aircraft (Re ≈ 0.5–1.0 × 10⁶), consider Eppler E423 or Selig S1223, which are optimised for high-lift, low-Re performance.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
