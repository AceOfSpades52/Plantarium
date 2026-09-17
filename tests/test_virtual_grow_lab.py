from __future__ import annotations

import tempfile
import unittest

from planticu.domain import Plant, readings_by_metric
from planticu.engine import PlantCareEngine
from planticu.store import PlantStore
from planticu.supervisor import PlantSupervisor
from planticu.virtual_grow import (
    GrowthStageRule,
    SimulationClock,
    VirtualEnvironmentProfile,
    VirtualGrowLab,
    VirtualGrowSensorAdapter,
    VirtualPlantProfile,
)


class VirtualGrowLabTests(unittest.TestCase):
    def make_plant(self) -> Plant:
        return Plant(
            plant_id="virtual-p1",
            display_name="Virtual Plant",
            species="Test species",
            cultivar=None,
            medium="coco",
            growth_stage="unknown",
            container_volume_l=3.0,
        )

    def test_clock_moves_through_day_and_night(self):
        lab = VirtualGrowLab(clock=SimulationClock(elapsed_hours=0.0))
        midnight = lab.snapshot()
        self.assertEqual(1, midnight.day_number)
        self.assertEqual(0.0, midnight.hour_of_day)
        self.assertEqual(0.0, midnight.par_umol_m2_s)

        noon = lab.advance(12.0)
        self.assertEqual(1, noon.day_number)
        self.assertAlmostEqual(12.0, noon.hour_of_day, places=6)
        self.assertGreater(noon.par_umol_m2_s, 0.0)
        self.assertGreater(noon.dli_mol_m2_day, 0.0)

        next_midnight = lab.advance(12.0)
        self.assertEqual(2, next_midnight.day_number)
        self.assertAlmostEqual(0.0, next_midnight.hour_of_day, places=6)
        self.assertEqual(0.0, next_midnight.par_umol_m2_s)
        self.assertAlmostEqual(0.0, next_midnight.dli_mol_m2_day, places=6)
        self.assertGreater(next_midnight.previous_day_dli_mol_m2_day, 0.0)

    def test_environment_changes_vpd_and_light_across_photoperiod(self):
        profile = VirtualEnvironmentProfile(
            lights_on_hour=6.0,
            lights_off_hour=18.0,
            day_temp_c=30.0,
            night_temp_c=18.0,
            day_relative_humidity_pct=40.0,
            night_relative_humidity_pct=75.0,
        )
        lab = VirtualGrowLab(environment=profile)
        night = lab.snapshot()
        day = lab.advance(12.0)

        self.assertGreater(day.air_temp_c, night.air_temp_c)
        self.assertLess(day.relative_humidity_pct, night.relative_humidity_pct)
        self.assertGreater(day.vpd_kpa, night.vpd_kpa)
        self.assertGreater(day.par_umol_m2_s, night.par_umol_m2_s)

    def test_growth_stage_changes_hidden_water_demand(self):
        plant_profile = VirtualPlantProfile(
            base_daily_water_demand_ml=400.0,
            stage_rules=(
                GrowthStageRule(1, "seedling", 0.5),
                GrowthStageRule(2, "vegetative", 1.0),
            ),
        )
        lab = VirtualGrowLab(plant_profile=plant_profile, clock=SimulationClock(elapsed_hours=12.0))
        day_one = lab.snapshot()
        day_two = lab.advance(24.0)

        self.assertEqual("seedling", day_one.growth_stage)
        self.assertEqual("vegetative", day_two.growth_stage)
        self.assertGreater(day_two.true_water_demand_ml_day, day_one.true_water_demand_ml_day)

    def test_sensor_adapter_does_not_leak_hidden_truth(self):
        lab = VirtualGrowLab(clock=SimulationClock(elapsed_hours=12.0))
        adapter = VirtualGrowSensorAdapter(lab)
        readings = adapter.read(self.make_plant())
        by_metric = readings_by_metric(readings)

        self.assertEqual(
            {
                "air_temp_c",
                "relative_humidity_pct",
                "vpd_kpa",
                "co2_ppm",
                "par_umol_m2_s",
                "dli_mol_m2_day",
            },
            set(by_metric),
        )
        self.assertNotIn("true_water_demand_ml_day", by_metric)
        self.assertNotIn("growth_stage", by_metric)
        self.assertTrue(all(reading.simulated for reading in readings))
        self.assertTrue(all(reading.provider_id == "virtual_grow_environment" for reading in readings))
        self.assertTrue(all("true_water_demand_ml_day" not in reading.context for reading in readings))
        self.assertTrue(all("growth_stage" not in reading.context for reading in readings))

    def test_virtual_environment_uses_existing_provider_and_storage_contracts(self):
        plant = self.make_plant()
        lab = VirtualGrowLab(clock=SimulationClock(elapsed_hours=12.0))
        adapter = VirtualGrowSensorAdapter(lab)

        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            engine = PlantCareEngine(store, adapter, PlantSupervisor(), controller=None)
            result = engine.run_cycle(plant)

            # Root-zone sensors deliberately do not exist in v0.2.0 yet, so
            # hydration stays unknown instead of the simulator leaking truth.
            self.assertEqual("unknown", result.state.hydration)
            self.assertEqual(6, len(result.readings))
            self.assertEqual(1, store.counts()["sensor_providers"])
            self.assertEqual(6, store.counts()["sensor_channels"])
            self.assertEqual(6, store.counts()["observations"])
            store.close()


if __name__ == "__main__":
    unittest.main()
