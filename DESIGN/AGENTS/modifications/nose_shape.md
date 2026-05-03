# Skill: Nose Shape

## What It Modifies
Changes the forebody profile of the cockpit pod from blunt to sharp (ogive, elliptic, or conical).

## Parameter in generate.py
Not yet implemented — requires: changing the forward XSec shape type in OpenVSP via `vsp.ChangeXSecShape(surf, 0, vsp.XS_ELLIPSE)` or equivalent, and then adjusting the nose-section width/height taper over the first 1–2 XSecs.

## Physical Effect
A blunt nose creates a strong stagnation region and high form drag. Sharpening the nose to an elliptic or ogival profile moves the stagnation point and reduces pressure drag at the nose substantially. For low-speed aircraft the gains are modest compared with tail-cone shaping, but still measurable.

## How to Apply
In `generate.py`, after creating the fuselage geom, iterate over XSec indices 0–1 and reduce their width/height toward zero (point) or a small ellipse. Use `vsp.SetXSecWidth` and `vsp.SetXSecHeight`. For a proper ogive, add intermediate XSecs using `vsp.InsertXSec` with a smooth taper schedule.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
