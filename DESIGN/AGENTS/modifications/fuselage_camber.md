# Skill: Fuselage Camber (Lifting Fuselage)

## What It Modifies
Introduces a vertical offset (camber line) to the fuselage centreline so the body generates positive lift, reducing the load on the wing.

## Parameter in generate.py
Not implemented — requires offsetting the fuselage XSec Z_Rel_Location values along the body length to curve the centreline upward aft of the CG.

`DESIGN/AGENTS/smooth_fuselage_redesign/generate.py` implements a fixed
smooth centerline using per-station `z_center_m` values, but it is not yet a
parameterized lifting-fuselage optimizer.

## Physical Effect
A lifting fuselage can contribute 5–15% of total lift, allowing wing area (and thus induced drag and mass) to be reduced. However, fuselage camber introduces a pitching moment that the tail must trim, potentially increasing trim drag. The net benefit requires careful analysis; it is most useful in wide-body aircraft where the fuselage cross-section is large relative to the wing.

## How to Apply
Not yet implemented. To add: iterate over fuselage XSec positions in generate.py and apply a sinusoidal or polynomial Z offset using `vsp.SetParmVal(vsp.FindParm(fuse_id, "Z_Rel_Location", "XForm"), z_offset)` per XSec. Introduce `P["fuse_camber_z"]` as the maximum centreline vertical offset (metres). Evaluate lift contribution via VSPAERO Cm output.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Added low-nose to high-cockpit to aft-tail swooping fuselage centerline | 18.87 | 46.48 | 2186.7406 | Max centerline slope 20.56 deg, max centerline curvature 0.4446 1/m; intended as packaging/smoothness, not credited as lifting-fuselage benefit |
