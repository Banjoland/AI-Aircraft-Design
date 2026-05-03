# Guideline Modification Capability Audit

Source: `C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRCRAFT DESIGN 2\DESIGN\DESIGN_GUIDELINES.md`

## Summary

- Features in DESIGN_GUIDELINES.md: 63
- Memory docs present: 63
- Memory docs missing: 0
- Dedicated feature tool dirs present: 0
- Dedicated feature tool dirs missing: 63

## Status Counts

- `implemented`: 24
- `needs_airfoil_tool_extension`: 1
- `needs_architecture_tool`: 6
- `needs_generator_parameter`: 2
- `needs_geometry_tool`: 17
- `needs_mass_cg_tool`: 2
- `partial`: 11

## Feature Matrix

| Feature | Slug | Status | Memory | Dedicated Tool | Tools | Implementation |
|---|---|---|---|---|---|---|
| Fuselage length | `fuselage_length` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `EVALUATION/AGENTS/fuselage_smoothness` | baseline_generator override |
| Maximum fuselage diameter | `fuselage_max_diameter` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `EVALUATION/AGENTS/fuselage_smoothness` | baseline_generator override |
| Fuselage fineness ratio | `fuselage_fineness_ratio` | `implemented` | yes | missing | `DESIGN/AGENTS/parameter_modifier`, `EVALUATION/AGENTS/fuselage_smoothness` | derived by changing length and diameter parameters |
| Nose shape (blunt → sharp) | `nose_shape` | `needs_geometry_tool` | yes | missing | `EVALUATION/AGENTS/fuselage_smoothness` | requires OpenVSP fuselage section insertion/profile control |
| Tail cone taper angle | `tail_cone_taper` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `EVALUATION/AGENTS/fuselage_smoothness` | baseline_generator pod taper override |
| Cabin cross-sectional shape (circular, oval, rectangular) | `cabin_cross_section_shape` | `partial` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | width/height available; circular/oval/rectangular profiles need section-shape tool |
| Cockpit position (forward vs aft shift) | `cockpit_position` | `needs_mass_cg_tool` | yes | missing | - | requires cockpit station and CG/mass model |
| Engine placement (nose, wing-mounted, aft fuselage) | `engine_placement` | `partial` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | tractor nose prop exists; wing/aft engine placement needs architecture generator |
| Payload location (CG distribution tuning) | `payload_location` | `needs_mass_cg_tool` | yes | missing | - | requires payload mass station and CG calculator |
| Surface smoothness / roughness factor | `surface_smoothness` | `partial` | yes | missing | `EVALUATION/AGENTS/fuselage_smoothness` | fuselage profile smoothness exists; roughness factor needs drag model input |
| Canopy shape and angle | `canopy_shape` | `needs_geometry_tool` | yes | missing | `EVALUATION/AGENTS/fuselage_smoothness` | requires canopy/fuselage upper-profile section controls |
| Belly contour (flat vs curved) | `belly_contour` | `needs_geometry_tool` | yes | missing | - | requires lower-profile section controls |
| Fuselage camber (lifting fuselage concept) | `fuselage_camber` | `needs_geometry_tool` | yes | missing | - | requires vertical section-centerline offsets |
| Wingspan | `wingspan` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing area | `wing_area` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | derived from span and root/tip chords |
| Aspect ratio | `aspect_ratio` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | derived from span and area |
| Taper ratio | `taper_ratio` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | derived from tip/root chord |
| Wing sweep angle | `wing_sweep` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing dihedral angle | `wing_dihedral` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `SIMULATION/AGENTS/beta_sweep` | baseline_generator override |
| Wing anhedral angle | `wing_anhedral` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `SIMULATION/AGENTS/beta_sweep` | negative wing_dihedral override |
| Wing vertical placement (high, mid, low) | `wing_vertical_placement` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing longitudinal placement (relative to CG) | `wing_longitudinal_placement` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing thickness-to-chord ratio | `wing_thickness_chord_ratio` | `implemented` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | NACA airfoil thickness selection |
| Wing root chord | `wing_root_chord` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing tip chord | `wing_tip_chord` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing planform shape (elliptical, rectangular, trapezoidal) | `wing_planform_shape` | `partial` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | trapezoid available; elliptical/rectangular need planform generator mode |
| Wing leading-edge shape | `wing_leading_edge_shape` | `needs_geometry_tool` | yes | missing | - | requires per-section sweep or custom wing outline |
| Wing trailing-edge shape | `wing_trailing_edge_shape` | `needs_geometry_tool` | yes | missing | - | requires per-section chord/sweep outline tool |
| Standard wing configuration (forward wing, trailing empenage) | `standard_wing_configuration` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator` | baseline_generator pod-and-boom tractor with aft tail |
| Tandem Wing | `tandem_wing` | `needs_architecture_tool` | yes | missing | - | requires alternate generator architecture |
| Canard configuration | `canard_configuration` | `needs_architecture_tool` | yes | missing | - | requires canard generator and canard-first stall checks |
| Wing height | `wing_height` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | same as wing vertical placement |
| Airfoil selection (root) | `airfoil_root` | `partial` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/parameter_modifier` | global wing NACA tool exists; root-only section selection still needed |
| Airfoil selection (tip) | `airfoil_tip` | `partial` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/parameter_modifier` | global wing NACA tool exists; tip-only section selection still needed |
| Airfoil camber distribution | `airfoil_camber_distribution` | `partial` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/parameter_modifier` | NACA camber can be changed globally; spanwise distribution needs per-XSec tool |
| Airfoil thickness distribution | `airfoil_thickness_distribution` | `partial` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/parameter_modifier` | NACA thickness can be changed globally; spanwise distribution needs per-XSec tool |
| Twist (washout/washin) | `wing_twist` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Wing incidence angle | `wing_incidence` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator override |
| Spanwise lift distribution | `spanwise_lift_distribution` | `partial` | yes | missing | `DESIGN/AGENTS/parameter_modifier`, `SIMULATION/AGENTS/alpha_sweep` | changed by span/chord/twist; needs dedicated load-distribution evaluator |
| Leading-edge radius | `leading_edge_radius` | `partial` | yes | missing | `DESIGN/AGENTS/airfoil_tool`, `DESIGN/AGENTS/parameter_modifier` | controlled indirectly by airfoil thickness; direct leading-edge shaping needed |
| Add winglets | `winglet_add` | `needs_geometry_tool` | yes | missing | - | requires winglet geometry generator |
| Winglet height | `winglet_height` | `needs_geometry_tool` | yes | missing | - | requires winglet geometry generator |
| Winglet cant angle | `winglet_cant_angle` | `needs_geometry_tool` | yes | missing | - | requires winglet geometry generator |
| Winglet toe angle | `winglet_toe_angle` | `needs_geometry_tool` | yes | missing | - | requires winglet geometry generator |
| Winglet airfoil | `winglet_airfoil` | `needs_geometry_tool` | yes | missing | `DESIGN/AGENTS/airfoil_tool` | requires winglet geometry and airfoil assignment |
| Winglet sweep | `winglet_sweep` | `needs_geometry_tool` | yes | missing | - | requires winglet geometry generator |
| Raked wingtip length | `raked_wingtip` | `needs_geometry_tool` | yes | missing | - | requires multi-section wing tip generator |
| Tip fences | `tip_fences` | `needs_geometry_tool` | yes | missing | - | requires wingtip endplate/fence geometry generator |
| Split winglets (upper/lower) | `split_winglets` | `needs_geometry_tool` | yes | missing | - | requires upper/lower winglet geometry generator |
| Endplate size | `endplate_size` | `needs_geometry_tool` | yes | missing | - | requires endplate geometry generator |
| Wingtip vortex control devices | `wingtip_vortex_control_devices` | `needs_geometry_tool` | yes | missing | `SIMULATION/AGENTS/alpha_sweep` | requires wingtip device generator and induced-drag evaluation |
| Horizontal tail area | `horizontal_tail_area` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | derived from horizontal tail span and chords |
| Vertical tail area | `vertical_tail_area` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier`, `SIMULATION/AGENTS/beta_sweep` | derived from vertical tail height and chords |
| Tail moment arm length | `tail_moment_arm_length` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | tail x-location and boom length overrides |
| Tail airfoil selection | `tail_airfoil_selection` | `needs_airfoil_tool_extension` | yes | missing | `DESIGN/AGENTS/airfoil_tool` | requires airfoil modifier support for HorizTail/VertTail geoms |
| Tail incidence angle | `tail_incidence_angle` | `needs_generator_parameter` | yes | missing | `DESIGN/AGENTS/baseline_generator` | requires htail/vtail incidence parameters in baseline generator |
| T-tail vs conventional tail | `t_tail_vs_conventional_tail` | `needs_architecture_tool` | yes | missing | - | requires alternate tail attachment/placement generator |
| V-tail configuration | `v_tail_configuration` | `needs_architecture_tool` | yes | missing | - | requires V-tail geometry generator and control-axis mapping |
| Twin tail vs single tail | `twin_tail_vs_single_tail` | `needs_architecture_tool` | yes | missing | - | requires twin vertical tail generator |
| Canard configuration (presence/size) | `canard_configuration_presence_size` | `needs_architecture_tool` | yes | missing | - | requires canard generator and canard-first stall checks |
| Tail dihedral/anhedral | `tail_dihedral_anhedral` | `needs_generator_parameter` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `SIMULATION/AGENTS/beta_sweep` | requires horizontal tail dihedral parameter |
| Propeller diameter | `propeller_diameter` | `implemented` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | baseline_generator prop disk override |
| Thrust line relative to CG | `thrust_line_relative_to_cg` | `partial` | yes | missing | `DESIGN/AGENTS/baseline_generator`, `DESIGN/AGENTS/parameter_modifier` | prop x-position exists; vertical thrust-line and CG model still needed |
