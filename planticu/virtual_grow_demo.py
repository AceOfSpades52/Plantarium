from __future__ import annotations

import argparse
from pathlib import Path

from .domain import Plant
from .metrics import normalize_readings
from .store import PlantStore
from .virtual_grow import (
    GrowthStageRule,
    VirtualEnvironmentProfile,
    VirtualGrowLab,
    VirtualGrowSensorAdapter,
    VirtualPlantProfile,
)


def run_demo(database: str, hours: float, step_hours: float) -> None:
    """Run the first Virtual Grow Lab slice without exposing truth to care logic."""

    if hours <= 0.0:
        raise ValueError("hours must be greater than zero")
    if step_hours <= 0.0:
        raise ValueError("step-hours must be greater than zero")

    plant = Plant(
        plant_id="virtual-lab-001",
        display_name="Virtual Lab Plant 001",
        species="Fragaria × ananassa",
        cultivar="Albion",
        medium="not_modeled_yet",
        growth_stage="unknown",
        container_volume_l=0.0,
        genetic_line_id="virtual-albion-demo",
    )

    # The short stage schedule is intentionally accelerated so a 3-day demo
    # visibly proves that biological time is working. It is not a strawberry
    # growth recommendation.
    plant_profile = VirtualPlantProfile(
        base_daily_water_demand_ml=360.0,
        stage_rules=(
            GrowthStageRule(1, "seedling", 0.45),
            GrowthStageRule(2, "vegetative", 1.00),
            GrowthStageRule(3, "flowering_demo", 1.18),
        ),
    )
    environment = VirtualEnvironmentProfile(
        lights_on_hour=6.0,
        lights_off_hour=18.0,
        peak_par_umol_m2_s=650.0,
        day_temp_c=27.0,
        night_temp_c=20.0,
        day_relative_humidity_pct=52.0,
        night_relative_humidity_pct=70.0,
        day_co2_ppm=850.0,
        night_co2_ppm=600.0,
    )
    lab = VirtualGrowLab(environment=environment, plant_profile=plant_profile)
    sensors = VirtualGrowSensorAdapter(lab)
    store = PlantStore(database)

    print("[VIRTUAL_GROW_LAB] v0.2.0 environment + biological clock")
    print("[BOUNDARY] TRUE WORLD -> virtual sensors -> normalized observations")
    print("[BOUNDARY] growth stage and true water demand are developer-only hidden truth")

    try:
        store.upsert_plant(plant)
        store.upsert_sensor_provider(sensors.info)

        sample = 0
        elapsed = 0.0
        while elapsed <= hours + 1e-9:
            sample += 1
            truth = lab.snapshot()
            readings = normalize_readings(sensors.read(plant))
            store.record_readings(readings)
            observed = {reading.metric: reading.value for reading in readings}

            print(
                f"[SAMPLE {sample:02d}] day={truth.day_number} hour={truth.hour_of_day:04.1f} "
                f"T={observed['air_temp_c']:.1f}C RH={observed['relative_humidity_pct']:.1f}% "
                f"VPD={observed['vpd_kpa']:.2f}kPa CO2={observed['co2_ppm']:.0f}ppm "
                f"PAR={observed['par_umol_m2_s']:.0f} DLI={observed['dli_mol_m2_day']:.2f}"
            )
            print(
                f"  [HIDDEN_TRUTH] stage={truth.growth_stage} "
                f"true_water_demand={truth.true_water_demand_ml_day:.1f}mL/day-equivalent"
            )

            if elapsed >= hours - 1e-9:
                break
            step = min(step_hours, hours - elapsed)
            lab.advance(step)
            elapsed += step

        stored_metrics = {
            row[0]
            for row in store.conn.execute("SELECT DISTINCT metric FROM observations").fetchall()
        }
        hidden_leaked = bool({"growth_stage", "true_water_demand_ml_day"} & stored_metrics)
        print(f"[TRUTH_FIREWALL] hidden_metrics_stored={hidden_leaked}")
        print(f"[DATABASE] {Path(database).resolve()}")
        print(f"[COUNTS] {store.counts()}")
    finally:
        store.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plantarium Virtual Grow Lab v0.2.0 demo")
    parser.add_argument("--hours", type=float, default=72.0)
    parser.add_argument("--step-hours", type=float, default=6.0)
    parser.add_argument("--database", default="plant_virtual_grow_demo.sqlite3")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_demo(args.database, args.hours, args.step_hours)


if __name__ == "__main__":
    main()
