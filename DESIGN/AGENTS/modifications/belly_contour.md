# Skill: Belly Contour

## What It Modifies
Changes whether the lower fuselage surface is flat (slab-sided) or curved (rounded belly) in the vertical direction.

## Parameter in generate.py
Not separately parameterised — controlled by `P["fuse_max_height"]` and the OpenVSP XSec height at each station. The FUSELAGE geom uses elliptical XSecs by default, giving a naturally curved belly.

## Physical Effect
A flat belly reduces the cross-sectional area gradient on the lower surface, which can reduce interference drag with the wing root and simplify landing gear attachment. A curved belly maintains the elliptical cross-section, minimising wetted area for a given interior volume. Flat lower fuselages are common on low-wing aircraft for structural reasons; for a pod-and-boom ultralight the curved belly is aerodynamically superior.

## How to Apply
To create a flat belly: in generate.py, access each fuselage XSec and change the shape type from ellipse to a rounded-rectangle using `vsp.ChangeXSecShape(surf, idx, vsp.XS_ROUNDED_RECTANGLE)` and set the lower radius to a large value (near-flat). To maintain the elliptical belly, no change is needed from the current baseline.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
