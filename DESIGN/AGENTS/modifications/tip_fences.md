# Skill: Tip Fences

## What It Modifies
Adds thin flat plates at the wingtip, oriented perpendicular to the wing surface, to interrupt the spanwise flow and contain the tip vortex.

## Parameter in generate.py
Not implemented — thin flat plate at wingtip would require a WING geom with very small chord (near-zero thickness) placed at the tip.

## Physical Effect
Tip fences act similarly to end plates on a finite wing, artificially increasing the effective aspect ratio by blocking spanwise flow. They are simpler to manufacture than winglets but less aerodynamically efficient per unit area. A fence height of 3–6% of semi-span gives roughly half the induced drag benefit of a winglet of the same height. They add wetted area and a small amount of structural mass.

## How to Apply
Add a WING geom at the tip station with: very small root and tip chord (0.05 m, thin disc-like), span equal to `P["fence_height"]` (e.g., 0.15 m both above and below tip), and a symmetric thin airfoil (NACA 0006). Place it at the tip Y position and apply 90-deg rotation. Introduce `P["fence_height"] = 0.15`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
