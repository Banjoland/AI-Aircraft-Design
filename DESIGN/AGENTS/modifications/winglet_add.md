# Skill: Add Winglets

## What It Modifies
Adds near-vertical lifting surfaces at the wingtips to reduce the induced drag penalty of the finite wing span.

## Parameter in generate.py
Not implemented — requires adding a new WING geom at the tip of the main wing with approximately 90-deg rotation about the local X-axis.

## Physical Effect
Winglets increase the effective span without increasing the geometric span. They reduce the strength of the wingtip vortex, which lowers induced drag by 3–7% for a well-designed winglet. For a wing already at AR ≈ 20, the marginal gain from winglets is smaller than for lower-AR wings — but still positive. Winglets also add wetted area and structural mass, so the net benefit requires analysis.

## How to Apply
Add a WING geom child of the main wing at the tip station. Rotate it 90 deg about the X-axis using `_set(winglet_id, "X_Rel_Rotation", "XForm", 90.0)`. Position at `X_Rel_Location = P["wing_x"]`, `Y_Rel_Location = P["wing_span"] / 2`. Set span to `P["winglet_height"]` and chord distribution. Introduce `P["winglet_height"] = 0.4` and `P["winglet_root_chord"] = 0.25` as new parameters.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
