# Skill: Canard Configuration

## What It Modifies
Moves the horizontal stabiliser from aft of the main wing to forward of it (ahead of the CG), creating a canard layout.

## Parameter in generate.py
Not implemented — requires moving the HT geom to a position forward of the main wing (x ≈ 0.0–0.3 m), removing the aft HT, and completely redesigning pitch stability (canard must stall before the main wing for safe recovery).

## Physical Effect
A canard generates positive lift (no download), improving efficiency. The canard's wing-in-upwash of the main wing means the canard needs less area than a conventional tail. However, canard aircraft are harder to design for safe stall behaviour: the canard must stall first to prevent deep stall of the main wing. CG range is also more limited.

## How to Apply
Not yet implemented. To add: reposition `htail_id` to `P["canard_x"] ≈ 0.1–0.3 m`, increase its area relative to the current tail (since it operates at lower dynamic pressure in the nose region), and redesign the stability analysis to confirm canard-first stall sequence. Requires a complete redesign of the pitch stability model.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
