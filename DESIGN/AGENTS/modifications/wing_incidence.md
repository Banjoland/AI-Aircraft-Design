# Skill: Wing Incidence Angle

## What It Modifies
Sets the angle between the wing chord line and the fuselage reference line, allowing cruise without fuselage pitch attitude.

## Parameter in generate.py
Not yet in P — add `P["wing_incidence_deg"] = 0.0` to enable. Requires `_set(wing_id, "Incidence", "XSec_1", P["wing_incidence_deg"])` in generate.py.

## Physical Effect
Setting wing incidence to the cruise AoA allows the fuselage to fly level (zero body pitch) at cruise, minimising fuselage drag. For this aircraft the cruise CL is modest (~0.5–0.7), so the cruise AoA is approximately 3–5 deg; setting wing incidence to this value permits a zero-pitch fuselage attitude. Incorrect incidence causes the fuselage to fly pitched, increasing its projected frontal area and drag.

## How to Apply
Add `P["wing_incidence_deg"] = 3.0` to the P dict. In generate.py, after creating the wing geom, add: `_set(wing_id, "Incidence", "XSec_1", P["wing_incidence_deg"])`. Verify the incidence parameter name with `vsp.FindParm(wing_id, "Incidence", "XSec_1")` — it may be labelled differently in OpenVSP 3.49.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
