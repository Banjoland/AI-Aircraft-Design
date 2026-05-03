# Skill: Canopy Shape and Angle

## What It Modifies
Changes the external profile of the cockpit canopy, affecting frontal area and local pressure distribution over the forward fuselage.

## Parameter in generate.py
Not modelled in OpenVSP — affects drag aesthetics and local flow field but the current FUSELAGE geom represents only the structural pod, not the transparent canopy fairing.

## Physical Effect
A tall, blunt canopy creates a large frontal area and strong adverse pressure gradient on the aft slope, promoting separation and high drag. A low-profile, teardrop-shaped canopy blends smoothly into the fuselage, reducing the local separation bubble. The canopy can contribute 10–20% of total fuselage drag in poorly designed aircraft.

## How to Apply
Add a second FUSELAGE geom in generate.py representing the canopy fairing, with XSecs that form a low teardrop profile sitting above the cockpit pod. Parameterise with `P["canopy_height"]` and `P["canopy_length"]`. Ensure the aft slope angle is less than 20° to avoid separation. Alternatively, model as an upper XSec offset on the existing pod geom using `vsp.SetXSecHeight` with position-dependent values.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
