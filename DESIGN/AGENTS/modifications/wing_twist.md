# Skill: Wing Twist (Washout / Washin)

## What It Modifies
Applies a geometric rotation of the tip chord relative to the root, reducing (washout) or increasing (washin) the tip angle of attack.

## Parameter in generate.py
`P["wing_twist"]` — current default value: -2.0 deg (washout, tip trailing edge up)

## Physical Effect
Washout (negative twist, tip TE up) reduces the local AoA at the tip, ensuring the root stalls before the tip. This is the primary method of preventing tip stall on tapered wings and maintains aileron effectiveness at high AoA. Excessive washout adds a nose-up pitching moment and shifts lift inboard, slightly reducing efficiency. Typical washout: -2 to -4 deg for tapered low-speed wings.

## How to Apply
Change `P["wing_twist"]` in the P dict. Negative = washout (tip unloaded), positive = washin (tip loaded — avoid for safety). For the current taper ratio of 0.617, -2 deg is marginal; if taper is reduced toward 0.4–0.5, increase washout to -3 to -4 deg to prevent tip stall. Re-run VSPAERO and examine the spanwise CL distribution at high AoA.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
