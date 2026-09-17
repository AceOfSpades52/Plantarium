from __future__ import annotations

from dataclasses import dataclass

from .adapters import WaterAdapter
from .domain import Plant, Prescription, Treatment


@dataclass(frozen=True)
class WaterSafetyLimits:
    max_single_dose_ml: float = 150.0
    min_confidence_for_automatic_action: float = 0.80


class DeterministicController:
    """Hardware-facing safety boundary. No inference belongs here."""

    def __init__(self, water_adapter: WaterAdapter, limits: WaterSafetyLimits | None = None) -> None:
        self.water_adapter = water_adapter
        self.limits = limits or WaterSafetyLimits()

    def execute(self, plant: Plant, prescription: Prescription) -> Treatment | None:
        if prescription.capability != "water":
            return None
        if prescription.confidence < self.limits.min_confidence_for_automatic_action:
            return None

        requested = max(0.0, prescription.amount)
        safe_amount = min(requested, self.limits.max_single_dose_ml)
        delivered = self.water_adapter.irrigate(plant, safe_amount)

        return Treatment(
            plant_id=plant.plant_id,
            capability="water",
            requested_amount=requested,
            executed_amount=delivered,
            unit="mL",
            adapter=self.water_adapter.name,
            safety_clamped=safe_amount < requested,
        )
