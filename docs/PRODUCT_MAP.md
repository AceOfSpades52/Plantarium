# High-level product map

## Product idea
A medical-chart + monitor + bounded autopilot + research platform for plants.

The same evidence-first core should scale from a person with a phone and thermometer to breeding companies with sequencing data and controlled-environment experiments.

## User levels

### Home grower
- photo-first plant identification and onboarding,
- plain-language health/care status,
- optional manual measurements,
- optional connected sensors,
- plant timeline and photos,
- growth/harvest records,
- individual-plant learning,
- Living Almanac recommendations.

### Advanced grower
Adds root-zone chemistry, PAR/DLI, CO2, irrigation data, reservoir data, automation adapters, detailed charts, and grow comparisons.

### Breeder/researcher
Adds lineage, trait vectors, experimental cohorts, environment/challenge profiles, phenotype measurement, genetics/genomics evidence, and genotype-by-environment analysis.

## Home product modules

### Core
- phone/app camera,
- AI identification and setup guidance,
- grow record,
- photo health/growth tracking,
- manual Guided Observation Mode,
- alerts/recommendations,
- Living Almanac + individual plant knowledge.

### Soil/coco/substrate module
- substrate moisture,
- root-zone temperature,
- optional EC/pH,
- pot/load-cell mass,
- optional irrigation capability.

### Hydro/DWC module
- reservoir/water temperature,
- dissolved oxygen,
- pH,
- EC,
- reservoir volume/level,
- flow/circulation,
- optional water top-off, aeration, dosing, and pH-control capabilities.

### Environment module
- PAR/DLI,
- CO2,
- airflow,
- controllable light,
- temperature/humidity adapters.

## Nutrient mixing boundary
AI proposes targets; it does not freely run dosing pumps.

A deterministic nutrient mixer should know:
- concentrate identity,
- channel/pump calibration,
- tank remaining amount,
- product-specific mixing restrictions,
- maximum dose per step,
- stabilization/mixing delay,
- re-measure-before-more rules.

Typical closed-loop sequence:

```text
small dose -> mix/circulate -> wait -> measure -> decide next small dose
```

Concentrates that must not be mixed directly remain physically/logically separated.

## Knowledge flow

```text
Established knowledge
        +
validated network learning
        +
species/cultivar/line knowledge
        +
grow-method knowledge
        +
garden history
        +
individual plant history
        +
current observations
        -> personalized prescription with evidence + confidence
```

## UX principle
Beginner view answers: **How is my plant doing, what needs attention, and what should I do?**

Advanced/research details use progressive disclosure. Users should not need to understand EC, VPD, DLI, QTLs, or provider IDs to start growing.
