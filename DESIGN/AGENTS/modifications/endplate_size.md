# Skill: Endplate Size

## What It Modifies
Sets the area of flat vertical plates at the wingtips that act as end-caps to suppress spanwise flow and reduce induced drag.

## Parameter in generate.py
Not implemented — similar to tip fences but typically larger and symmetrically above/below the tip. Requires a WING geom with zero sweep and very thin chord at the tip.

## Physical Effect
End plates effectively increase the aspect ratio of the wing. The correction to AR for end plates of height h on a wing of span b is approximately AR_eff = AR * (1 + 1.9 * h / b). For a 0.3 m end plate on a 9.8 m wing: AR_eff ≈ AR * 1.058. End plates add wetted area and some weight, so the drag benefit must be weighed against these penalties. Below h/b ≈ 0.03 the benefit is negligible.

## How to Apply
Add a WING geom at each tip with: chord equal to tip chord (0.37 m), span = `P["endplate_height"]` (both directions), and no airfoil camber. Rotate 90 deg to vertical. Introduce `P["endplate_height"] = 0.20`. For the current wing, an end plate of 0.20 m gives AR_eff boost of about 3.9%.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
