# Skill: Wing Anhedral Angle

## What It Modifies
Introduces a downward wing-panel angle (negative dihedral), typically used with high-wing or T-tail configurations for lateral stability tuning.

## Parameter in generate.py
Uses negative value of `P["wing_dihedral"]` — set `P["wing_dihedral"]` to a negative number (e.g., -3.0) to apply anhedral.

## Physical Effect
Anhedral reduces the dihedral effect, making the aircraft less sensitive to sideslip roll coupling. It is commonly used on high-wing military transports (where the high-wing position provides strong inherent dihedral effect) to avoid over-sensitivity. For a mid/low-wing ultralight, anhedral would typically make the aircraft laterally unstable and is not recommended unless a specific stability design requires it.

## How to Apply
Set `P["wing_dihedral"]` to a negative value (e.g., -2.0 deg for mild anhedral). This uses the same OpenVSP parameter — a negative dihedral is anhedral. Monitor lateral-directional stability via VSPAERO Clbeta output; ensure Clbeta < 0 (stable) is maintained.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
