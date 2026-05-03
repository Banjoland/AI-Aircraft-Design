# Skill: Taper Ratio

## What It Modifies
Sets the ratio of tip chord to root chord, controlling the spanwise chord distribution and tip loading.

## Parameter in generate.py
Derived: `taper = P["wing_tip_chord"] / P["wing_root_chord"]`  
Current baseline: 0.37 / 0.60 = 0.617

## Physical Effect
A taper ratio near 0.45 approximates an elliptical spanwise lift distribution, minimising induced drag for a given span. Too low a taper ratio (< 0.3) shifts lift inboard and causes tip stall at low speeds. Too high a taper (approaching 1.0, rectangular) wastes structural material and increases induced drag. The current 0.617 is slightly high (more rectangular than ideal) and could be reduced toward 0.45–0.50 for improved efficiency.

## How to Apply
Reduce `P["wing_tip_chord"]` toward `0.45 * P["wing_root_chord"]` = 0.27 m to approach the elliptic optimum. This also slightly reduces wing area, so verify stall speed after the change. Pair with a twist adjustment to prevent tip stall if taper is reduced below 0.4.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
