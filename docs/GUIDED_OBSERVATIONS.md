# Guided observations

A grower without connected sensors is still a first-class user.

## Product rule
A human can act as a measurement provider. Manual measurements use the same normalized `Reading` contract as simulated, replayed, and future live sensors.

Examples:
- canopy air temperature from a handheld thermometer,
- reservoir temperature,
- pH or EC from a pen meter,
- pot mass from a kitchen scale,
- irrigation or runoff volume from a measuring cup,
- harvest mass from a scale.

The reading should preserve context such as **where**, **how**, and **when** it was measured.

Example:

```text
metric: air_temp_c
value: 26.0 C
provider: human_manual
position: 15_cm_above_canopy
method: handheld_thermometer
```

## Qualitative evidence
Not everything should become a fake number. Observations such as:
- "roots look cream-white",
- "leaves are slightly curled",
- "no visible pests",
- "fruit is beginning to color",

are stored as `QualitativeObservation` records.

## Guided Observation Mode
The future UI should ask for the *next most useful* observation rather than showing a giant technical form.

Example:

> Check the air about 15 cm (6 in) above the top leaves.
>
> Why: temperature near the canopy can differ from the rest of the room.

The AI should not ask for information it already has or does not need.

## Care styles
All are valid:
- **Hands-on** — AI observes/advises; the grower performs actions.
- **Assisted** — safe routine actions may be automated; important changes can require approval.
- **Automatic where available** — deterministic controllers execute bounded prescriptions through installed capabilities.

Traditional/almanac-style growing is not an error state. The system should augment good grower judgment, not demand automation.
