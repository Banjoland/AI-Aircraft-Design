# Skill: Winglet Toe Angle

## What It Modifies
Rotates the winglet about its own span axis to set the local incidence of the winglet airfoil relative to the local flow at the tip.

## Parameter in generate.py
Not implemented — requires winglet geom. Proposed parameter: `P["winglet_toe_deg"]`, typical range -3 to +5 deg.

## Physical Effect
Positive toe-in (winglet leading edge angled inward toward fuselage) increases the effective AoA on the winglet, generating more lateral force that reduces the induced drag of the main wing. Excessive toe-in causes the winglet to operate near stall and increases its own profile drag, negating the benefit. Typical optimal toe angle is 2–4 deg inward. Toe-out reduces the winglet's contribution to induced drag reduction.

## How to Apply
After implementing winglet_add.md, apply a rotation about the winglet's local Y-axis: `_set(winglet_id, "Y_Rel_Rotation", "XForm", P["winglet_toe_deg"])`. Start at 0 deg and optimise in 1-deg steps by comparing total drag from VSPAERO.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
