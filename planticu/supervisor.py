from __future__ import annotations

from dataclasses import dataclass

from .domain import Alert, Plant, Prescription, Reading, readings_by_metric


@dataclass(frozen=True)
class WaterPolicy:
    target_moisture_pct: float = 78.0
    irrigation_trigger_pct: float = 62.0
    ml_per_percentage_point: float = 11.0
    maximum_recommended_ml: float = 240.0


class PlantSupervisor:
    """Inference layer: estimates needs; it never talks to hardware directly."""

    def __init__(self, water_policy: WaterPolicy | None = None) -> None:
        self.water_policy = water_policy or WaterPolicy()

    def assess(self, plant: Plant, readings: list[Reading]) -> tuple[list[Prescription], list[Alert]]:
        by_metric = readings_by_metric(readings)
        prescriptions: list[Prescription] = []
        alerts: list[Alert] = []

        moisture = by_metric.get("substrate_moisture_pct")
        pot_mass = by_metric.get("pot_mass_g")

        if moisture is None:
            alerts.append(
                Alert(
                    plant_id=plant.plant_id,
                    severity="warning",
                    category="missing_sensor",
                    message="Substrate moisture is unavailable; automatic irrigation inference is disabled.",
                    human_action_required=True,
                )
            )
            return prescriptions, alerts

        policy = self.water_policy
        if moisture.value <= policy.irrigation_trigger_pct:
            deficit_points = max(0.0, policy.target_moisture_pct - moisture.value)
            recommended_ml = min(
                policy.maximum_recommended_ml,
                deficit_points * policy.ml_per_percentage_point,
            )

            # Confidence grows when we have two independent water-related signals.
            confidence = 0.72
            evidence = [f"substrate moisture {moisture.value:.1f}% <= trigger {policy.irrigation_trigger_pct:.1f}%"]
            if pot_mass is not None:
                confidence = 0.88
                evidence.append(f"pot mass measured at {pot_mass.value:.1f} g")

            prescriptions.append(
                Prescription(
                    plant_id=plant.plant_id,
                    capability="water",
                    amount=round(recommended_ml, 1),
                    unit="mL",
                    confidence=confidence,
                    reason="Estimated root-zone water deficit",
                    evidence=tuple(evidence),
                )
            )

        if moisture.value < 35.0:
            alerts.append(
                Alert(
                    plant_id=plant.plant_id,
                    severity="urgent",
                    category="water_stress",
                    message="Root-zone moisture is critically low; inspect the plant and irrigation path.",
                    human_action_required=True,
                    evidence=(f"substrate moisture {moisture.value:.1f}%",),
                )
            )

        return prescriptions, alerts
