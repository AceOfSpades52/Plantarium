from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Plant:
    plant_id: str
    display_name: str
    species: str
    cultivar: str | None
    medium: str
    growth_stage: str
    container_volume_l: float
    started_at: str = field(default_factory=utc_now_iso)
    mother_plant_id: str | None = None
    father_plant_id: str | None = None
    genetic_line_id: str | None = None
    identity_confidence: float | None = None


@dataclass(frozen=True)
class Environment:
    """A precisely described place/setup in which plants are observed."""

    environment_id: str
    name: str
    environment_type: str
    description: str = ""
    parent_environment_id: str | None = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class ChallengeProfile:
    """A bounded experimental stress/constraint profile, never an actuator command."""

    challenge_id: str
    name: str
    description: str
    constraints: dict[str, float | int | str | bool]
    selection_goals: tuple[str, ...]
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    name: str
    environment_id: str
    challenge_id: str | None = None
    hypothesis: str = ""
    status: str = "planned"
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class ExperimentMembership:
    experiment_id: str
    plant_id: str
    cohort: str
    role: str = "subject"
    enrolled_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GeneticProfile:
    """Metadata about genetics. Raw files remain external evidence assets."""

    genetic_profile_id: str
    plant_id: str
    source_format: str
    source_name: str
    source_sha256: str
    reference_genome: str | None = None
    ownership_scope: str = "private"
    variant_count: int = 0
    imported_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GeneticVariant:
    genetic_profile_id: str
    chromosome: str
    position: int
    reference: str
    alternate: str
    genotype: str | None = None
    variant_id: str | None = None
    quality: float | None = None


@dataclass(frozen=True)
class TraitObservation:
    """Measured phenotype/outcome. This is evidence, not a breeding score."""

    plant_id: str
    trait: str
    value: float
    unit: str
    method: str
    environment_id: str | None = None
    experiment_id: str | None = None
    quality: float = 1.0
    observed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class PlantIdentityCandidate:
    species: str
    confidence: float
    cultivar: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class PerceptionObservation:
    """An AI/computer-vision interpretation linked to its source evidence."""

    plant_id: str
    source_asset: str
    model_name: str
    observation_type: str
    payload: dict[str, object]
    confidence: float
    observed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class PlantStateEstimate:
    plant_id: str
    hydration: str
    stress: str
    confidence: float
    evidence: tuple[str, ...]
    estimated_at: str = field(default_factory=utc_now_iso)




@dataclass(frozen=True)
class SensorChannel:
    """A normalized measurement contract exposed by a sensor provider."""

    channel_id: str
    metric: str
    unit: str
    scope: str = "plant"
    description: str = ""


@dataclass(frozen=True)
class SensorProviderInfo:
    """Describes where readings come from without coupling care logic to hardware."""

    provider_id: str
    display_name: str
    mode: str
    transport: str
    simulated: bool
    channels: tuple[SensorChannel, ...]

@dataclass(frozen=True)
class Reading:
    plant_id: str
    metric: str
    value: float
    unit: str
    source: str
    quality: float = 1.0
    observed_at: str = field(default_factory=utc_now_iso)
    provider_id: str | None = None
    channel_id: str | None = None
    simulated: bool = False
    # Optional provenance such as measurement position, method, calibration, or notes.
    # The reasoning engine may ignore this today, but the evidence record must retain it.
    context: dict[str, str | float | int | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class QualitativeObservation:
    """A human or AI observation that should not be forced into a number."""

    plant_id: str
    observation_type: str
    description: str
    source: str
    position: str | None = None
    confidence: float = 1.0
    observed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class KnowledgeEntry:
    """One claim in the layered Living Almanac.

    ``scope_type`` is one of: established, global, species, cultivar,
    grow_method, garden, or plant. More specific knowledge does not erase
    broader knowledge; both remain available to reasoning.
    """

    knowledge_id: str
    topic: str
    scope_type: str
    scope_key: str | None
    statement: str
    source_type: str
    confidence: float
    validation_status: str
    evidence_count: int = 0
    metadata: dict[str, str | float | int | bool] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Prescription:
    plant_id: str
    capability: str
    amount: float
    unit: str
    confidence: float
    reason: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class Treatment:
    plant_id: str
    capability: str
    requested_amount: float
    executed_amount: float
    unit: str
    adapter: str
    safety_clamped: bool
    treated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class Alert:
    plant_id: str
    severity: str
    category: str
    message: str
    human_action_required: bool
    evidence: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now_iso)


def readings_by_metric(readings: Iterable[Reading]) -> dict[str, Reading]:
    """Choose the highest-quality reading when multiple providers expose one metric."""
    chosen: dict[str, Reading] = {}
    for reading in readings:
        current = chosen.get(reading.metric)
        if current is None or reading.quality >= current.quality:
            chosen[reading.metric] = reading
    return chosen
