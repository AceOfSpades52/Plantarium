from __future__ import annotations

from .domain import Plant, PlantStateEstimate, Reading, readings_by_metric


class PlantStateEstimator:
    """Small transparent state estimator; future learned models can implement the same contract."""

    def estimate(self, plant: Plant, readings: list[Reading]) -> PlantStateEstimate:
        by_metric = readings_by_metric(readings)
        moisture = by_metric.get("substrate_moisture_pct")

        if moisture is None:
            return PlantStateEstimate(
                plant_id=plant.plant_id,
                hydration="unknown",
                stress="unknown",
                confidence=0.25,
                evidence=("substrate moisture unavailable",),
            )

        if moisture.value < 35.0:
            return PlantStateEstimate(
                plant_id=plant.plant_id,
                hydration="critical_low",
                stress="high",
                confidence=0.90,
                evidence=(f"substrate moisture {moisture.value:.1f}%",),
            )
        if moisture.value <= 62.0:
            return PlantStateEstimate(
                plant_id=plant.plant_id,
                hydration="low",
                stress="possible",
                confidence=0.84,
                evidence=(f"substrate moisture {moisture.value:.1f}%",),
            )
        return PlantStateEstimate(
            plant_id=plant.plant_id,
            hydration="adequate",
            stress="not_detected",
            confidence=0.80,
            evidence=(f"substrate moisture {moisture.value:.1f}%",),
        )
