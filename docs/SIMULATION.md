# Simulation strategy

Simulation is a first-class product capability, not disposable mock code.

## The most important rule: truth is not observation

A real plant has internal biological state that no sensor can perfectly expose. The simulator must preserve that same separation:

1. **True world** — what the simulator secretly knows.
2. **Observed world** — what sensors, cameras, or humans can measure.
3. **Plantarium belief** — what the care/research models infer from those observations.

The AI must never receive hidden simulator truth just because it is convenient. Otherwise we would train/test software that succeeds only because the simulation cheats.

## v0.2.0 environment + biological clock

`planticu/virtual_grow.py` contains the first richer virtual-world slice.

### SimulationClock
Keeps one `elapsed_hours` value and derives day/hour from it. This avoids separate day/hour fields drifting out of sync.

### VirtualEnvironmentProfile
Defines a simple controlled environment:
- lights-on/off time,
- peak PAR,
- day/night temperature,
- day/night humidity,
- day/night CO2.

A smooth sine-shaped daylight fraction creates the virtual PAR curve.

### DLI
The lab integrates PAR through the simulated day. At midnight the current DLI resets and the completed day's DLI is retained in hidden truth.

### Growth stage and demand
`VirtualPlantProfile` contains explicit stage rules. The hidden plant model calculates a synthetic water-demand signal from:
- stage multiplier,
- light,
- VPD,
- temperature.

Those coefficients are **software test behavior**, not horticultural advice.

### VirtualGrowSensorAdapter
This is the firewall. It exposes only:
- `air_temp_c`,
- `relative_humidity_pct`,
- `vpd_kpa`,
- `co2_ppm`,
- `par_umol_m2_s`,
- `dli_mol_m2_day`.

It does **not** expose:
- hidden growth stage,
- true water demand,
- cumulative hidden demand.

Tests fail if hidden fields leak through this provider boundary.

## Older substrate simulation
`SimulatedPlantEnvironment` still supports the original v0.1 vertical slice with dry mass, water mass, moisture, root EC/temp, and irrigation response. It remains in place so working behavior is not broken while the Virtual Grow Lab is built in slices. v0.2.1 will replace/expand root-zone simulation cleanly rather than stuffing more responsibilities into that old class.

## Recorded-data replay
The replay provider remains the bridge between simulation-only development and real evidence. Real exported datasets can be mapped to normalized CSV and run through the same system without physical hardware.

## Planned next slices
- v0.2.1 soil/coco root zone
- v0.2.2 DWC/hydro reservoir
- v0.2.3 nutrient-solution state and safe mixing simulation
- v0.2.4 sensor imperfection/failure models
- v0.2.5 multiple plants, lineages, and challenge cohorts

## Scientific rule
Never label a result as a biological discovery merely because it appears in our simulator. Simulation validates software behavior and helps design hypotheses. Biological claims require real observations and appropriate experimental evidence.
