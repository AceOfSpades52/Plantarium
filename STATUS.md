# STATUS — v0.1.4

## Current slice
**Repository Bootstrap + Guided Observation + Living Almanac Foundation**

No physical hardware is assumed available. A person using ordinary handheld tools is now a first-class observation provider, and knowledge is explicitly layered so individual experience can refine care without silently rewriting species/global horticultural knowledge.

## Implemented
- [x] All v0.1.0-v0.1.2 plant care, simulation, provider, research, genetics, and provenance behavior
- [x] HumanMeasurementAdapter using the same `SensorAdapter` contract as hardware/simulation
- [x] Manual measurement position/method/notes persisted as reading context
- [x] Normal unit conversion for human-entered measurements
- [x] GuidedObservationRequest plain-language measurement prompts
- [x] Separate QualitativeObservation records for non-numeric evidence
- [x] Hands-on/monitor-only care path with recommendations and no actuation
- [x] Layered `KnowledgeEntry` model
- [x] Living Almanac scope resolver: established/global/species/cultivar/grow-method/garden/plant
- [x] Broad and plant-specific knowledge coexist without overwriting one another
- [x] Product map documents home modules, hydro/DWC measurements, nutrient-mixing safety, care styles, genetics/research expansion
- [x] Beginner code tour and stronger readability rules
- [x] Guided/manual demo
- [x] 18 automated tests
- [x] Canonical GitHub repository: `AceOfSpades52/Plantarium`
- [x] One-command Termux bootstrap works from any directory
- [x] Persistent `~/plantarium` checkout instead of version-specific extracted folders
- [x] Local edits preserved during updates
- [x] Downloaded `plantarium-patch-*.zip` / `plantarium-tests-*.zip` bundles auto-applied once by SHA-256

## Deliberately not claimed
- [ ] The simulation is not validated plant physiology
- [ ] No real cloud/network Almanac exists yet
- [ ] No automated scientific promotion from candidate pattern to validated knowledge yet
- [ ] No real computer vision is bundled yet
- [ ] No physical sensor transport is implemented yet
- [ ] No nutrient dosing controller is implemented yet
- [ ] No variant-to-trait biological interpretation or causal genetics model yet

## Next acceptance condition
Build the **Virtual Grow Lab** while preserving the same provider/knowledge/manual-observation contracts:

- substrate/soil/coco root-zone scenarios
- DWC/hydro reservoir scenarios
- water temperature and dissolved oxygen
- EC/pH/reservoir behavior
- plant demand and growth stages
- light/DLI/shared environment
- configurable nutrient-solution state
- failures/noise/drift/dropout
- multiple plants/challenge cohorts

The simulation must generate explicit synthetic provenance and remain replaceable by human/replayed/live data without domain or reasoning rewrites.
