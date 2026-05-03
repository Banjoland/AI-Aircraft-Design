# Skill: Payload Location

## What It Modifies
Shifts the longitudinal position of payload mass (pilot, fuel, baggage) to adjust the centre of gravity.

## Parameter in generate.py
Not directly in P — CG computation is not currently implemented in generate.py. Payload location affects CG which is not modelled.

## Physical Effect
Payload location is the primary real-world CG driver. Moving payload forward increases nose-heavy tendency; moving aft decreases static margin. For an ultralight, the pilot typically constitutes 40–50% of MTOW and their seat position strongly governs CG. An incorrectly located CG requires large trim deflections, increasing drag and potentially destabilising the aircraft.

## How to Apply
Requires adding a CG model to generate.py: define component masses and x-positions, compute CG_x = sum(m_i * x_i) / sum(m_i), and compare against wing AC (approx. `P["wing_x"] + 0.25 * P["wing_root_chord"]`). Adjust pilot seat x-position parameter to hit 25–30% MAC static margin.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
