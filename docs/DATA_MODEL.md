# Data model

## Plant
Identity and lineage anchor.
- plant_id
- species/cultivar
- identity confidence
- medium/stage/container
- mother/father IDs
- genetic line ID

Unknown beginner-onboarding fields may be stored as `unknown` until perception/user evidence improves them.

## SensorProviderInfo
Persistent description of an observation source:
- provider ID
- display name
- mode (`simulation`, `replay`, `live`, etc.)
- transport
- simulated flag
- declared channels

## SensorChannel
A provider channel declares:
- channel ID
- canonical metric
- canonical unit
- scope
- description

## Raw observation
Normalized sensor evidence:
- plant ID
- metric/value/unit
- source
- quality
- timestamp
- provider ID
- channel ID
- explicit simulated flag
- context JSON for measurement position/method/calibration/notes

Provider-native signals are calibrated at the adapter boundary. Known common units are normalized before care/state reasoning. All normalized readings remain stored even when one is selected as the current best-quality signal for a metric.

## PerceptionObservation
AI/CV interpretation tied to its source photo/asset, model, payload, confidence, and timestamp. It is not raw truth.

## PlantStateEstimate
Inferred hydration/stress state with evidence and confidence.

## Environment
A physical or simulated context: windowsill, tent, greenhouse bay, controlled chamber, orbital habitat, etc.

## ChallengeProfile
Experimental constraints and selection goals, such as reduced water allocation or high heat. A challenge describes exposure; it is not itself an actuator command.

## Experiment + membership
Links plants to cohorts and a specific environment/challenge/hypothesis.

## GeneticProfile
Metadata/provenance for a plant's genetic evidence:
- format
- source file name
- SHA-256
- reference genome
- ownership scope
- variant count

## GeneticVariant
Normalized VCF evidence: chromosome, position, REF, ALT, genotype, ID, quality.

## TraitObservation
Measured phenotype/outcome with method, quality, environment, and experiment links.

Examples: harvest mass, water-use efficiency, flowering time, recovery time, canopy growth, disease score.

## Prescription / Treatment / Alert
Care-system outputs remain independent from research evidence. A prescription can exist in monitor-only mode with no treatment record because no actuator/controller is installed.


## QualitativeObservation
Non-numeric evidence such as leaf posture, root appearance, pest observations, or grower notes. It keeps source, position, confidence, and timestamp without inventing a metric value.

## KnowledgeEntry
One Living Almanac claim with topic, scope, source type, confidence, validation status, evidence count, and metadata. Supported scopes are established, global, species, cultivar, grow method, garden, and plant.
