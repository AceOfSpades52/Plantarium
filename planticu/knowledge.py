from __future__ import annotations

"""Layered plant knowledge without silently overwriting broader knowledge.

The platform may know something from established horticulture, from a future
network-wide learned pattern, from a particular cultivar, from one garden, or
from one individual plant. These are different evidence scopes, not competing
rows in one mutable almanac entry.
"""

from dataclasses import dataclass

from .domain import KnowledgeEntry, Plant


# Lower numbers are broader. Higher numbers are more specific to one situation.
SCOPE_SPECIFICITY = {
    "established": 0,
    "global": 1,
    "species": 2,
    "cultivar": 3,
    "grow_method": 4,
    "garden": 5,
    "plant": 6,
}


@dataclass(frozen=True)
class KnowledgeContext:
    """Known identifiers used to find knowledge relevant to one plant."""

    plant: Plant
    garden_id: str | None = None


class KnowledgeResolver:
    """Selects relevant entries while preserving every knowledge layer.

    It deliberately does *not* collapse them into one magic answer. Reasoning
    code can inspect the ordered evidence and explain which layers influenced a
    recommendation.
    """

    def relevant_entries(
        self,
        entries: list[KnowledgeEntry],
        context: KnowledgeContext,
        topic: str | None = None,
    ) -> list[KnowledgeEntry]:
        relevant: list[KnowledgeEntry] = []
        plant = context.plant

        for entry in entries:
            if topic is not None and entry.topic != topic:
                continue
            if self._matches(entry, plant, context.garden_id):
                relevant.append(entry)

        return sorted(
            relevant,
            key=lambda entry: (
                SCOPE_SPECIFICITY.get(entry.scope_type, -1),
                entry.confidence,
            ),
        )

    @staticmethod
    def _matches(entry: KnowledgeEntry, plant: Plant, garden_id: str | None) -> bool:
        if entry.scope_type in {"established", "global"}:
            return True
        if entry.scope_type == "species":
            return entry.scope_key == plant.species
        if entry.scope_type == "cultivar":
            return plant.cultivar is not None and entry.scope_key == plant.cultivar
        if entry.scope_type == "grow_method":
            return entry.scope_key == plant.medium
        if entry.scope_type == "garden":
            return garden_id is not None and entry.scope_key == garden_id
        if entry.scope_type == "plant":
            return entry.scope_key == plant.plant_id
        return False
