# AGENTS.md

## Product intent
Build a longitudinal plant intelligence platform: a medical-chart + monitor + bounded autopilot for individual plants, plus a research system that can connect genotype, phenotype, environment, lineage, and outcome.

## User assumption
Assume the end user may know nothing about horticulture, sensors, genetics, or grow-system terminology. Prefer photo/setup inference and plain-language questions. Ask only for facts the system cannot safely infer.

## Non-negotiable architecture
- Plant is the primary domain object.
- Raw observations are never discarded in favor of summaries or AI conclusions.
- Raw genetics files/data are evidence; interpretations are separate and confidence-bearing.
- Genetics/lineage are first-class data.
- Environment, challenge, intervention, phenotype, experiment, and outcome remain separable.
- AI perception is an adapter; no core domain object depends on one vendor/model.
- Perception -> Plant State -> Reasoning -> Safe Control are separate layers.
- Intelligence proposes prescriptions; deterministic controllers enforce hardware limits.
- Hardware is accessed only through capability adapters.
- Until physical hardware is available, simulation is a first-class provider and must exercise the same interfaces intended for real sensors.
- Every reading must preserve provenance sufficient to distinguish simulation, replayed real evidence, and live evidence.
- Real sensors/data must be swappable in at provider boundaries without modifying plant-domain, reasoning, genetics, experiment, or research models.
- Sensor-only / manual-treatment operation is a supported product mode; actuation is optional.
- Human-entered measurements are first-class evidence providers; preserve measurement position/method provenance.
- Qualitative observations remain qualitative; never invent numeric values merely to fit sensor schemas.
- Living Almanac knowledge is layered (established -> global -> species -> cultivar/line -> grow method -> garden -> plant); more-specific knowledge must not silently overwrite broader knowledge.
- Traditional hands-on growing is a valid care style. Automation must be progressively adoptable rather than required.
- Recommendations carry confidence/evidence; do not pretend requirements are exact when inferred.
- Correlation/association must never be silently promoted to causation.
- Shared environmental capabilities and individual-plant capabilities must remain distinguishable.
- Sensitive commercial genetics must support private/local use; do not assume data may be pooled.
- Every behavior change updates relevant docs and STATUS.md.

## Development style
Work in small vertical slices. Preserve working behavior. Add tests for behavior changes. Prefer readable names and explicit data flow over clever abstractions. Assume a beginner coder may read any module: use small single-purpose files/functions, descriptive names, comments explaining why before what, and avoid unnecessary metaprogramming or compressed one-liners.
