# Skill: Fuselage Fineness Ratio

## What It Modifies
Controls the ratio of fuselage length to maximum diameter, governing the slenderness of the pod.

## Parameter in generate.py
Not directly in P — derived: `P["fuse_length"] / max(P["fuse_max_width"], P["fuse_max_height"])`  
Current baseline: 1.6 / 1.10 = 1.45 (very blunt; ideal is 3–6 for minimum drag)

## Physical Effect
Fineness ratio below ~3 produces large pressure drag due to rapid cross-sectional area changes. Increasing fineness ratio (longer pod or smaller diameter) transitions the fuselage toward a Sears–Haack-like body and significantly reduces form drag. Above a ratio of about 6, skin-friction drag begins to dominate and total drag starts rising again.

## How to Apply
Adjust `P["fuse_length"]` upward or `P["fuse_max_width"]`/`P["fuse_max_height"]` downward to target a fineness ratio of 3–5. Compute the ratio manually: `fuse_length / fuse_max_width`. Aim for at least 3.0 to see meaningful drag reduction.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
