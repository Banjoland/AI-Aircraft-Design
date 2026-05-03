# Skill: Winglet Airfoil

## What It Modifies
Sets the airfoil section of the winglet surface, optimising its lift and drag at the local flow conditions at the wingtip.

## Parameter in generate.py
Not implemented — requires winglet geom.

## Physical Effect
The winglet operates in the complex flow field of the wingtip vortex at an effective AoA set by the local induced velocity field. A symmetric or low-camber airfoil is typically used (NACA 0012, NACA 0010) since the winglet must generate force in both directions depending on flight condition. A thinner winglet airfoil has lower profile drag and is preferable at the small chord Reynolds numbers typical of winglets.

## How to Apply
After implementing winglet_add.md, use `airfoil_modifier.py` to apply an airfoil to the winglet WING geom. Start with NACA 0012 (symmetric, well-characterised at low Re) and compare performance against NACA 0010 or a low-Re symmetric section such as NACA 63-012.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
