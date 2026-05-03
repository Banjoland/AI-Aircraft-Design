# Skill: Wing Tip Chord

## What It Modifies
Sets the chord length at the wing tip, controlling taper ratio and tip aerodynamics.

## Parameter in generate.py
`P["wing_tip_chord"]` — current default value: 0.37 m

## Physical Effect
A smaller tip chord (lower taper ratio) moves the spanwise lift distribution toward elliptic, reducing induced drag. Very small tip chords (< 0.2 m) concentrate the tip vortex, increasing the strength of the wingtip vortex, but this is partially mitigated by adding washout twist. A larger tip chord (approaching root chord = rectangular wing) is structurally simple but aerodynamically inefficient.

## How to Apply
Change `P["wing_tip_chord"]` in the P dict. Target taper ratio: 0.40–0.50 for near-elliptical lift distribution. Current value of 0.37 gives taper = 0.617 (too rectangular). Consider reducing to 0.27–0.30 m to approach the ideal, while adding more washout twist to prevent tip stall.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
