# Skill: Winglet Sweep

## What It Modifies
Sets the leading-edge sweep of the winglet planform, controlling its aerodynamic and structural characteristics.

## Parameter in generate.py
Not implemented — requires winglet geom. Proposed parameter: `P["winglet_sweep_deg"]`, typical range 25–45 deg.

## Physical Effect
A swept winglet reduces the effective thickness ratio and delays local compressibility effects (not critical at ultralight speeds). Structurally, a swept winglet shifts its aerodynamic centre aft, which can create a washout moment that reduces tip bending. Visually, swept winglets are common on modern aircraft (Boeing 737 NG, Airbus A320neo blended winglet). For this low-speed ultralight, sweep of 30–35 deg is primarily aesthetic/structural rather than aerodynamic.

## How to Apply
After implementing winglet_add.md, set the Sweep parameter on the winglet XSec using `_set(winglet_id, "Sweep", "XSec_1", P["winglet_sweep_deg"])`. This is the same as setting wing sweep on the main wing.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
