# Skill: Wing Thickness-to-Chord Ratio

## What It Modifies
Sets the thickness of the wing airfoil as a fraction of chord length, affecting drag, structural depth, and stall characteristics.

## Parameter in generate.py
Set via airfoil tool (airfoil_modifier.py); corresponds to the NACA 4-digit thickness digit.  
Default airfoil: OpenVSP default (no specific NACA assigned in baseline generate.py).

## Physical Effect
Thicker airfoils (t/c > 15%) have more structural depth (allowing lighter spars), gentler stall behaviour, and more room for fuel/structure, but higher profile drag due to greater adverse pressure gradient. Thinner airfoils (t/c 10–12%) have lower profile drag and are more efficient at cruise but stall more abruptly and require heavier spar structure. For a high-AR, low-speed wing, t/c of 14–18% is typical.

## How to Apply
Use `DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py` to apply a NACA 4-digit airfoil. Set the thickness digit to control t/c: e.g., NACA 2412 = 12% thick, NACA 2415 = 15% thick. Run the airfoil tool on the MainWing geom, then re-run VSPAERO to assess the drag polar change.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
