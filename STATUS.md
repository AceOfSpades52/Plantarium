# STATUS — v0.2.0

## Current slice
**Virtual Grow Lab: Environment + Biological Clock**

The v0.1.4 repository/bootstrap, manual-observation, Living Almanac, genetics/research, and provider contracts remain intact. v0.2.0 adds the first richer simulated world without pretending the simulation is validated plant physiology.

## Implemented
- [x] All v0.1.4 behavior preserved
- [x] Deterministic `SimulationClock` with day/hour progression
- [x] Configurable day/night photoperiod
- [x] Simulated air temperature and relative humidity cycle
- [x] Air VPD calculation
- [x] Simulated CO2 cycle
- [x] Smooth PAR daylight curve
- [x] DLI accumulation and midnight reset with previous-day DLI retained in hidden truth
- [x] Configurable growth-stage rules
- [x] Environment-sensitive hidden water-demand calculation
- [x] `VirtualGrowSensorAdapter` using the existing `SensorAdapter` contract
- [x] Explicit truth firewall: hidden stage/demand are not sensor metrics or sensor context
- [x] Environment readings retain synthetic provenance and simulation day/hour
- [x] Virtual-grow demo with developer-only truth display
- [x] 23 automated tests
- [x] Existing one-command Termux bootstrap remains the normal test/update path

## Deliberately not claimed
- [ ] The virtual climate/demand equations are not validated crop physiology
- [ ] Hidden simulator truth is not biological ground truth
- [ ] No soil/coco root-zone physics yet
- [ ] No DWC/hydro reservoir physics yet
- [ ] No water temperature/dissolved-oxygen model yet
- [ ] No nutrient/pH/EC solution dynamics yet
- [ ] No sensor noise, drift, latency, or dropout yet
- [ ] No actuator-failure simulation yet
- [ ] No multi-plant resource competition yet
- [ ] No real cloud/network Living Almanac yet
- [ ] No physical sensor transport yet

## Next acceptance condition — v0.2.1
Build **Soil / Coco Root Zone** on top of this world while preserving the truth firewall:

- container water storage,
- irrigation input,
- plant uptake driven by hidden environmental demand,
- drainage/runoff,
- root-zone temperature,
- substrate moisture observations,
- pot-mass observations,
- simple root EC state,
- treatment response visible only through subsequent observations.

The care engine must continue consuming sensor-style evidence rather than directly reading root-zone truth.
