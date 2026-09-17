from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from .domain import TraitObservation


@dataclass(frozen=True)
class CohortTraitSummary:
    cohort: str
    trait: str
    count: int
    mean_value: float
    unit: str


def summarize_trait_by_cohort(
    memberships: dict[str, str],
    observations: list[TraitObservation],
    trait: str,
) -> list[CohortTraitSummary]:
    """Descriptive evidence only; it does not claim causation or genetic effect."""

    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for observation in observations:
        if observation.trait != trait or observation.plant_id not in memberships:
            continue
        grouped[(memberships[observation.plant_id], observation.unit)].append(observation.value)

    return [
        CohortTraitSummary(cohort, trait, len(values), mean(values), unit)
        for (cohort, unit), values in sorted(grouped.items())
    ]
