from __future__ import annotations

import json
import tempfile
import unittest

from planticu.domain import KnowledgeEntry, Plant
from planticu.engine import PlantCareEngine
from planticu.guided_observation import GuidedObservationService, HumanMeasurementAdapter
from planticu.knowledge import KnowledgeContext, KnowledgeResolver
from planticu.store import PlantStore
from planticu.supervisor import PlantSupervisor


class GuidedObservationAndKnowledgeTests(unittest.TestCase):
    def make_plant(self) -> Plant:
        return Plant(
            plant_id="manual-p1",
            display_name="Manual Plant",
            species="Fragaria × ananassa",
            cultivar="Albion",
            medium="coco/perlite",
            growth_stage="vegetative",
            container_volume_l=11.4,
        )

    def test_manual_measurement_uses_normal_care_pipeline_and_preserves_context(self):
        plant = self.make_plant()
        manual = HumanMeasurementAdapter()
        manual.submit(
            plant.plant_id,
            "air_temp_c",
            77.0,
            "F",
            position="15_cm_above_canopy",
            method="handheld_thermometer",
        )
        manual.submit(
            plant.plant_id,
            "substrate_moisture_pct",
            58.0,
            "%",
            position="root_zone_center",
            method="handheld_moisture_meter",
        )
        manual.submit(
            plant.plant_id,
            "pot_mass_g",
            3.2,
            "kg",
            position="whole_container",
            method="kitchen_scale",
        )

        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            result = PlantCareEngine(store, manual, PlantSupervisor(), controller=None).run_cycle(plant)

            readings = {reading.metric: reading for reading in result.readings}
            self.assertAlmostEqual(25.0, readings["air_temp_c"].value, places=5)
            self.assertEqual(3200.0, readings["pot_mass_g"].value)
            self.assertEqual("human_manual", readings["air_temp_c"].provider_id)
            self.assertFalse(readings["air_temp_c"].simulated)
            self.assertTrue(result.prescriptions)
            self.assertEqual([], result.treatments)

            row = store.conn.execute(
                "SELECT context_json FROM observations WHERE metric='air_temp_c'"
            ).fetchone()
            context = json.loads(row["context_json"])
            self.assertEqual("15_cm_above_canopy", context["position"])
            self.assertEqual("handheld_thermometer", context["method"])
            store.close()

    def test_qualitative_observation_stays_non_numeric(self):
        plant = self.make_plant()
        observation = GuidedObservationService().make_visual_note(
            plant,
            observation_type="root_appearance",
            description="Roots look cream-white with no obvious slime.",
            position="root_zone",
        )

        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            store.upsert_plant(plant)
            store.record_qualitative_observation(observation)
            row = store.conn.execute("SELECT * FROM qualitative_observations").fetchone()
            self.assertEqual("root_appearance", row["observation_type"])
            self.assertEqual("human", row["source"])
            self.assertEqual(1, store.counts()["qualitative_observations"])
            store.close()

    def test_knowledge_resolver_keeps_broad_and_specific_layers(self):
        plant = self.make_plant()
        entries = [
            KnowledgeEntry("k0", "watering", "established", None, "baseline", "book", 0.9, "established"),
            KnowledgeEntry("k1", "watering", "global", None, "network", "aggregate", 0.8, "replicated", 5000),
            KnowledgeEntry("k2", "watering", "species", plant.species, "species", "aggregate", 0.9, "validated", 1000),
            KnowledgeEntry("k3", "watering", "cultivar", "Albion", "cultivar", "aggregate", 0.8, "observed", 200),
            KnowledgeEntry("k4", "watering", "grow_method", "coco/perlite", "medium", "aggregate", 0.8, "observed", 300),
            KnowledgeEntry("k5", "watering", "garden", "garden-a", "garden", "local", 0.8, "observed", 50),
            KnowledgeEntry("k6", "watering", "plant", plant.plant_id, "individual", "history", 0.8, "observed", 10),
            KnowledgeEntry("wrong", "watering", "cultivar", "Not Albion", "wrong", "test", 1.0, "observed"),
        ]

        resolved = KnowledgeResolver().relevant_entries(
            entries,
            KnowledgeContext(plant=plant, garden_id="garden-a"),
            topic="watering",
        )
        self.assertEqual(
            ["established", "global", "species", "cultivar", "grow_method", "garden", "plant"],
            [entry.scope_type for entry in resolved],
        )
        self.assertNotIn("wrong", [entry.knowledge_id for entry in resolved])

    def test_knowledge_store_does_not_overwrite_other_scopes(self):
        plant = self.make_plant()
        broad = KnowledgeEntry(
            "broad",
            "watering",
            "species",
            plant.species,
            "species statement",
            "curated",
            0.9,
            "validated",
        )
        personal = KnowledgeEntry(
            "personal",
            "watering",
            "plant",
            plant.plant_id,
            "individual statement",
            "individual_history",
            0.8,
            "observed",
        )
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            store.upsert_knowledge(broad)
            store.upsert_knowledge(personal)
            entries = store.list_knowledge("watering")
            self.assertEqual(2, len(entries))
            self.assertEqual({"species", "plant"}, {entry.scope_type for entry in entries})
            store.close()


if __name__ == "__main__":
    unittest.main()
