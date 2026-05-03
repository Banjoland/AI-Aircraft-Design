# Skill: Standard Wing Configuration (Forward Wing + Trailing Empennage)

## What It Modifies
Selects the conventional tractor configuration with the main wing forward of the CG and the horizontal tail aft for pitch stability.

## Parameter in generate.py
This is the current baseline configuration — no change required. Canard and tandem alternatives are not yet implemented.

## Physical Effect
The conventional aft-tail configuration provides positive pitch stability (tail produces a download in cruise, trimming the nose-up pitching moment of the cambered main wing). The tail download slightly reduces net lift, requiring a marginally larger wing area. The tail experiences the wing downwash, which reduces its effective AoA and requires larger tail area or longer moment arm to achieve adequate pitch authority.

## How to Apply
No change from baseline needed to maintain this configuration. If switching to canard or tandem, see the dedicated skill files `canard_configuration.md` and `tandem_wing.md`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline (conventional) | — | — | — | No data yet |
