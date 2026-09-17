# Roadmap

## v0.1.0 — One Plant / Water Intelligence
Simulated sensors, longitudinal record, water prescription, deterministic safety control. **Complete.**

## v0.1.1 — Research-Ready Foundation
Perception contract, plant-state layer, genetics evidence, VCF import, environment/challenge/experiment/trait records. **Complete.**

## v0.1.2 — Simulation + Provider Boundary
First-class simulation, replay/live-provider contracts, observation provenance, monitor-only mode. **Complete.**

## v0.1.3 — Guided Observation + Living Almanac
Human/manual measurements, qualitative observations, measurement context, care styles, and layered knowledge scopes. **Current.**

## v0.2 — Virtual Grow Lab
Parameterized soil/substrate and DWC/hydro scenarios, plant demand curves, climate/light/root chemistry, failure injection, multiple plants, challenge cohorts.

## v0.3 — Time-Series Plant Intelligence
Consumption baselines, forecasting, anomaly detection, confidence calibration, sensor disagreement and stale-data handling.

## v0.4 — Simulated Vision + Phenotyping Contracts
Image timelines and model-output fixtures for identity, canopy, symptoms, flowers/fruit, growth measurements, without requiring bundled local vision inference yet.

## v0.5 — Grow Intelligence
DLI, water/nutrient efficiency, health timeline, harvest/yield/quality records, grow comparisons.

## Hardware bridge — when hardware becomes available
The existing provider boundary should accept Raspberry Pi/ESP32/MQTT/BLE/serial/API sources as adapters, not as a core rewrite. Hardware work can begin at any later version without changing the roadmap above.

## v0.6 — Multi-Plant / Shared Environment
Individual plant capabilities plus shared light/climate/CO2 scopes and resource scheduling.

## v0.7 — Breeding Intelligence
Trait vectors, lineage graph, sibling/offspring comparison, multi-trait selection support.

## v0.8 — Genomics Intelligence
Annotation, kinship, QTL/GWAS-style association, genotype-by-environment models, genomic selection contracts.

## v0.9 — Discovery + Experiment Design
Cross-grow pattern mining, candidate associations, safe controlled trials, replication/validation tracking.

## v1.0 — Plant Medical Platform
Beginner photo-first onboarding through research/enterprise modes on the same evidence-first core.


## v0.1.4 — Repository bootstrap
- Canonical `AceOfSpades52/Plantarium` GitHub repository.
- Persistent Termux checkout at `~/plantarium`.
- One-command clone/update/patch/test bootstrap.
- Local patch bundles are hash-tracked and applied once.
- Local edits are preserved instead of silently overwritten.


## Virtual Grow Lab sequence
- [x] v0.2.0 — Environment + Biological Clock
- [ ] v0.2.1 — Soil / Coco Root Zone
- [ ] v0.2.2 — DWC / Hydro Reservoir
- [ ] v0.2.3 — Nutrient Solution + Mixing
- [ ] v0.2.4 — Sensor Faults / Drift / Dropout
- [ ] v0.2.5 — Multiple Plants + Genetic Challenge Cohorts
