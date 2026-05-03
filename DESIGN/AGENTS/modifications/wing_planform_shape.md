# Skill: Wing Planform Shape

## What It Modifies
Changes the overall planform from trapezoidal to elliptical (or multi-panel approximations thereof).

## Parameter in generate.py
Trapezoidal only in current implementation — elliptical requires a multi-section wing with progressively decreasing chords.  
Current: single XSec_1 taper from root to tip (trapezoidal).

## Physical Effect
An elliptical planform produces a perfectly elliptical spanwise lift distribution, giving the minimum induced drag for a given span and total lift. The Spitfire is the canonical example. In practice, a 3-panel tapered approximation (constant + taper + tip) achieves 96–98% of the elliptic ideal and is far simpler to manufacture.

## How to Apply
To implement a multi-section planform: add additional WING XSecs using `vsp.InsertXSec` and set progressively smaller chord values at each span station. Example: root panel (0–40% semi-span) at full root chord, mid panel (40–80%) tapered, tip panel (80–100%) tapered aggressively. Parameterise with `P["wing_mid_chord"]` and `P["wing_mid_span_frac"]`.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
