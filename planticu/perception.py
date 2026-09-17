from __future__ import annotations

from abc import ABC, abstractmethod

from .domain import PerceptionObservation, Plant, PlantIdentityCandidate


class PerceptionAdapter(ABC):
    """Boundary for cloud or local multimodal/computer-vision models."""

    @abstractmethod
    def identify_plant(self, plant: Plant, source_asset: str) -> tuple[list[PlantIdentityCandidate], PerceptionObservation]:
        raise NotImplementedError


class SimulatedVisionAdapter(PerceptionAdapter):
    """Deterministic stand-in proving the contract without pretending to run vision."""

    name = "simulated_multimodal_vision"

    def identify_plant(self, plant: Plant, source_asset: str) -> tuple[list[PlantIdentityCandidate], PerceptionObservation]:
        candidates = [
            PlantIdentityCandidate(
                species="Fragaria × ananassa",
                cultivar=None,
                confidence=0.94,
                evidence=("compound serrated leaves visible", "strawberry-like crown architecture"),
            ),
            PlantIdentityCandidate(
                species="Fragaria vesca",
                cultivar=None,
                confidence=0.05,
                evidence=("similar leaf morphology",),
            ),
        ]
        observation = PerceptionObservation(
            plant_id=plant.plant_id,
            source_asset=source_asset,
            model_name=self.name,
            observation_type="plant_identity",
            payload={
                "candidates": [
                    {"species": c.species, "cultivar": c.cultivar, "confidence": c.confidence}
                    for c in candidates
                ]
            },
            confidence=candidates[0].confidence,
        )
        return candidates, observation
