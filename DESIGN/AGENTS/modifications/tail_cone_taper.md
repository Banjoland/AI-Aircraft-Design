# Skill: Tail Cone Taper

## What It Modifies
Controls how sharply the aft end of the cockpit pod narrows before blending into the tail boom.

## Parameter in generate.py
`P["fuse_taper_width"]` — current default value: 0.20 m  
`P["fuse_taper_height"]` — current default value: 0.20 m

## Physical Effect
A gradual taper (larger taper values approaching max diameter) creates a bluff body that separates flow, producing high base drag. Reducing the taper dimensions to a smaller exit cross-section forces a longer, gentler pressure recovery, reducing separation and base drag. Values that are too small relative to the boom diameter create a sharp discontinuity that may also trigger separation.

## How to Apply
Reduce `P["fuse_taper_width"]` and `P["fuse_taper_height"]` toward the boom diameter (`P["boom_diameter"]` = 0.12 m) for the smoothest transition. Values in the range 0.14–0.25 m are reasonable. The ideal target is a smooth, continuous blend from pod to boom with no abrupt step change.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
