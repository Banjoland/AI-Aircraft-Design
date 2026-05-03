# Skill: Cabin Cross-Section Shape

## What It Modifies
Changes the shape of the fuselage mid-body cross-section between circular/oval and other profiles.

## Parameter in generate.py
Controlled by `P["fuse_max_width"]` and `P["fuse_max_height"]` — elliptical by default.  
Aspect ratio of cross-section: width/height = 1.10/0.75 = 1.47 (wide ellipse).

## Physical Effect
A circular cross-section (width = height) minimises wetted area for a given cross-sectional area, reducing skin-friction drag. A wide, flat ellipse can lower the aircraft's centre of gravity and reduce side-projected area, improving roll stability and lowering side-force drag. Super-elliptical ("squircle") shapes offer structural efficiency for pressurised cabins, though this aircraft is unpressurised.

## How to Apply
Set `P["fuse_max_width"]` equal to `P["fuse_max_height"]` for a circular section (minimum wetted area). Increase width relative to height for a wide-oval section that lowers CG. The shape type in OpenVSP defaults to ellipse for FUSELAGE XSecs; no code change is needed to switch between circular and elliptical — just adjust the two dimension parameters.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
