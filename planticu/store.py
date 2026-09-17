from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .domain import (
    Alert,
    ChallengeProfile,
    Environment,
    Experiment,
    ExperimentMembership,
    GeneticProfile,
    GeneticVariant,
    KnowledgeEntry,
    PerceptionObservation,
    Plant,
    PlantStateEstimate,
    QualitativeObservation,
    Reading,
    SensorProviderInfo,
    TraitObservation,
    Treatment,
)


class PlantStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def close(self) -> None:
        self.conn.close()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS plants (
                plant_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                species TEXT NOT NULL,
                cultivar TEXT,
                medium TEXT NOT NULL,
                growth_stage TEXT NOT NULL,
                container_volume_l REAL NOT NULL,
                started_at TEXT NOT NULL,
                mother_plant_id TEXT,
                father_plant_id TEXT,
                genetic_line_id TEXT,
                identity_confidence REAL
            );

            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                quality REAL NOT NULL,
                provider_id TEXT,
                channel_id TEXT,
                simulated INTEGER NOT NULL DEFAULT 0,
                context_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS sensor_providers (
                provider_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                mode TEXT NOT NULL,
                transport TEXT NOT NULL,
                simulated INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sensor_channels (
                provider_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                unit TEXT NOT NULL,
                scope TEXT NOT NULL,
                description TEXT NOT NULL,
                PRIMARY KEY (provider_id, channel_id)
            );

            CREATE TABLE IF NOT EXISTS treatments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                treated_at TEXT NOT NULL,
                capability TEXT NOT NULL,
                requested_amount REAL NOT NULL,
                executed_amount REAL NOT NULL,
                unit TEXT NOT NULL,
                adapter TEXT NOT NULL,
                safety_clamped INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                human_action_required INTEGER NOT NULL,
                evidence_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS environments (
                environment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                environment_type TEXT NOT NULL,
                description TEXT NOT NULL,
                parent_environment_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS challenge_profiles (
                challenge_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                constraints_json TEXT NOT NULL,
                selection_goals_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                environment_id TEXT NOT NULL,
                challenge_id TEXT,
                hypothesis TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS experiment_memberships (
                experiment_id TEXT NOT NULL,
                plant_id TEXT NOT NULL,
                cohort TEXT NOT NULL,
                role TEXT NOT NULL,
                enrolled_at TEXT NOT NULL,
                PRIMARY KEY (experiment_id, plant_id)
            );

            CREATE TABLE IF NOT EXISTS genetic_profiles (
                genetic_profile_id TEXT PRIMARY KEY,
                plant_id TEXT NOT NULL,
                source_format TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                reference_genome TEXT,
                ownership_scope TEXT NOT NULL,
                variant_count INTEGER NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS genetic_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                genetic_profile_id TEXT NOT NULL,
                chromosome TEXT NOT NULL,
                position INTEGER NOT NULL,
                reference TEXT NOT NULL,
                alternate TEXT NOT NULL,
                genotype TEXT,
                variant_id TEXT,
                quality REAL
            );

            CREATE TABLE IF NOT EXISTS trait_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                trait TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                method TEXT NOT NULL,
                environment_id TEXT,
                experiment_id TEXT,
                quality REAL NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS perception_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                source_asset TEXT NOT NULL,
                model_name TEXT NOT NULL,
                observation_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS plant_state_estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                hydration TEXT NOT NULL,
                stress TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_json TEXT NOT NULL,
                estimated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS qualitative_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id TEXT NOT NULL,
                observation_type TEXT NOT NULL,
                description TEXT NOT NULL,
                source TEXT NOT NULL,
                position TEXT,
                confidence REAL NOT NULL,
                observed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_entries (
                knowledge_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_key TEXT,
                statement TEXT NOT NULL,
                source_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                validation_status TEXT NOT NULL,
                evidence_count INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._ensure_column("plants", "identity_confidence", "REAL")
        self._ensure_column("observations", "provider_id", "TEXT")
        self._ensure_column("observations", "channel_id", "TEXT")
        self._ensure_column("observations", "simulated", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column("observations", "context_json", "TEXT NOT NULL DEFAULT '{}'")
        self.conn.commit()

    def _ensure_column(self, table: str, name: str, sql_type: str) -> None:
        columns = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
        if name not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")

    def upsert_plant(self, plant: Plant) -> None:
        self.conn.execute(
            """
            INSERT INTO plants
            (plant_id, display_name, species, cultivar, medium, growth_stage, container_volume_l,
             started_at, mother_plant_id, father_plant_id, genetic_line_id, identity_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plant_id) DO UPDATE SET
              display_name=excluded.display_name,
              species=excluded.species,
              cultivar=excluded.cultivar,
              medium=excluded.medium,
              growth_stage=excluded.growth_stage,
              container_volume_l=excluded.container_volume_l,
              mother_plant_id=excluded.mother_plant_id,
              father_plant_id=excluded.father_plant_id,
              genetic_line_id=excluded.genetic_line_id,
              identity_confidence=excluded.identity_confidence
            """,
            (
                plant.plant_id,
                plant.display_name,
                plant.species,
                plant.cultivar,
                plant.medium,
                plant.growth_stage,
                plant.container_volume_l,
                plant.started_at,
                plant.mother_plant_id,
                plant.father_plant_id,
                plant.genetic_line_id,
                plant.identity_confidence,
            ),
        )
        self.conn.commit()

    def upsert_environment(self, environment: Environment) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO environments
            (environment_id, name, environment_type, description, parent_environment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                environment.environment_id,
                environment.name,
                environment.environment_type,
                environment.description,
                environment.parent_environment_id,
                environment.created_at,
            ),
        )
        self.conn.commit()

    def upsert_challenge(self, challenge: ChallengeProfile) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO challenge_profiles
            (challenge_id, name, description, constraints_json, selection_goals_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                challenge.challenge_id,
                challenge.name,
                challenge.description,
                json.dumps(challenge.constraints, sort_keys=True),
                json.dumps(challenge.selection_goals),
                challenge.created_at,
            ),
        )
        self.conn.commit()

    def upsert_experiment(self, experiment: Experiment) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO experiments
            (experiment_id, name, environment_id, challenge_id, hypothesis, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                experiment.experiment_id,
                experiment.name,
                experiment.environment_id,
                experiment.challenge_id,
                experiment.hypothesis,
                experiment.status,
                experiment.created_at,
            ),
        )
        self.conn.commit()

    def enroll(self, membership: ExperimentMembership) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO experiment_memberships
            (experiment_id, plant_id, cohort, role, enrolled_at)
            VALUES (?, ?, ?, ?, ?)""",
            (
                membership.experiment_id,
                membership.plant_id,
                membership.cohort,
                membership.role,
                membership.enrolled_at,
            ),
        )
        self.conn.commit()

    def upsert_sensor_provider(self, provider: SensorProviderInfo) -> None:
        with self.conn:
            self.conn.execute(
                """INSERT INTO sensor_providers
                (provider_id, display_name, mode, transport, simulated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider_id) DO UPDATE SET
                  display_name=excluded.display_name,
                  mode=excluded.mode,
                  transport=excluded.transport,
                  simulated=excluded.simulated
                """,
                (
                    provider.provider_id,
                    provider.display_name,
                    provider.mode,
                    provider.transport,
                    int(provider.simulated),
                ),
            )
            self.conn.execute("DELETE FROM sensor_channels WHERE provider_id=?", (provider.provider_id,))
            self.conn.executemany(
                """INSERT INTO sensor_channels
                (provider_id, channel_id, metric, unit, scope, description)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        provider.provider_id,
                        channel.channel_id,
                        channel.metric,
                        channel.unit,
                        channel.scope,
                        channel.description,
                    )
                    for channel in provider.channels
                ],
            )

    def record_readings(self, readings: list[Reading]) -> None:
        self.conn.executemany(
            """INSERT INTO observations
            (plant_id, observed_at, metric, value, unit, source, quality, provider_id, channel_id, simulated, context_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    r.plant_id,
                    r.observed_at,
                    r.metric,
                    r.value,
                    r.unit,
                    r.source,
                    r.quality,
                    r.provider_id,
                    r.channel_id,
                    int(r.simulated),
                    json.dumps(r.context, sort_keys=True),
                )
                for r in readings
            ],
        )
        self.conn.commit()


    def record_qualitative_observation(self, observation: QualitativeObservation) -> None:
        """Store a non-numeric human/AI observation without inventing a metric value."""
        self.conn.execute(
            """INSERT INTO qualitative_observations
            (plant_id, observation_type, description, source, position, confidence, observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                observation.plant_id,
                observation.observation_type,
                observation.description,
                observation.source,
                observation.position,
                observation.confidence,
                observation.observed_at,
            ),
        )
        self.conn.commit()

    def upsert_knowledge(self, entry: KnowledgeEntry) -> None:
        """Store one Living Almanac entry without deleting broader or narrower scopes."""
        self.conn.execute(
            """INSERT INTO knowledge_entries
            (knowledge_id, topic, scope_type, scope_key, statement, source_type, confidence,
             validation_status, evidence_count, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(knowledge_id) DO UPDATE SET
              topic=excluded.topic,
              scope_type=excluded.scope_type,
              scope_key=excluded.scope_key,
              statement=excluded.statement,
              source_type=excluded.source_type,
              confidence=excluded.confidence,
              validation_status=excluded.validation_status,
              evidence_count=excluded.evidence_count,
              metadata_json=excluded.metadata_json
            """,
            (
                entry.knowledge_id,
                entry.topic,
                entry.scope_type,
                entry.scope_key,
                entry.statement,
                entry.source_type,
                entry.confidence,
                entry.validation_status,
                entry.evidence_count,
                json.dumps(entry.metadata, sort_keys=True),
                entry.created_at,
            ),
        )
        self.conn.commit()

    def list_knowledge(self, topic: str | None = None) -> list[KnowledgeEntry]:
        """Return persisted knowledge entries as domain objects."""
        if topic is None:
            rows = self.conn.execute("SELECT * FROM knowledge_entries ORDER BY created_at").fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM knowledge_entries WHERE topic=? ORDER BY created_at",
                (topic,),
            ).fetchall()
        return [
            KnowledgeEntry(
                knowledge_id=row["knowledge_id"],
                topic=row["topic"],
                scope_type=row["scope_type"],
                scope_key=row["scope_key"],
                statement=row["statement"],
                source_type=row["source_type"],
                confidence=float(row["confidence"]),
                validation_status=row["validation_status"],
                evidence_count=int(row["evidence_count"]),
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def record_state_estimate(self, state: PlantStateEstimate) -> None:
        self.conn.execute(
            """INSERT INTO plant_state_estimates
            (plant_id, hydration, stress, confidence, evidence_json, estimated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                state.plant_id,
                state.hydration,
                state.stress,
                state.confidence,
                json.dumps(state.evidence),
                state.estimated_at,
            ),
        )
        self.conn.commit()

    def record_perception(self, observation: PerceptionObservation) -> None:
        self.conn.execute(
            """INSERT INTO perception_observations
            (plant_id, source_asset, model_name, observation_type, payload_json, confidence, observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                observation.plant_id,
                observation.source_asset,
                observation.model_name,
                observation.observation_type,
                json.dumps(observation.payload, sort_keys=True),
                observation.confidence,
                observation.observed_at,
            ),
        )
        self.conn.commit()

    def record_genetic_profile(self, profile: GeneticProfile, variants: list[GeneticVariant]) -> None:
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO genetic_profiles
                (genetic_profile_id, plant_id, source_format, source_name, source_sha256, reference_genome,
                 ownership_scope, variant_count, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.genetic_profile_id,
                    profile.plant_id,
                    profile.source_format,
                    profile.source_name,
                    profile.source_sha256,
                    profile.reference_genome,
                    profile.ownership_scope,
                    profile.variant_count,
                    profile.imported_at,
                ),
            )
            self.conn.execute(
                "DELETE FROM genetic_variants WHERE genetic_profile_id=?",
                (profile.genetic_profile_id,),
            )
            self.conn.executemany(
                """INSERT INTO genetic_variants
                (genetic_profile_id, chromosome, position, reference, alternate, genotype, variant_id, quality)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        v.genetic_profile_id,
                        v.chromosome,
                        v.position,
                        v.reference,
                        v.alternate,
                        v.genotype,
                        v.variant_id,
                        v.quality,
                    )
                    for v in variants
                ],
            )

    def record_trait(self, observation: TraitObservation) -> None:
        self.conn.execute(
            """INSERT INTO trait_observations
            (plant_id, trait, value, unit, method, environment_id, experiment_id, quality, observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                observation.plant_id,
                observation.trait,
                observation.value,
                observation.unit,
                observation.method,
                observation.environment_id,
                observation.experiment_id,
                observation.quality,
                observation.observed_at,
            ),
        )
        self.conn.commit()

    def record_treatment(self, treatment: Treatment) -> None:
        self.conn.execute(
            """INSERT INTO treatments
            (plant_id, treated_at, capability, requested_amount, executed_amount, unit, adapter, safety_clamped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                treatment.plant_id,
                treatment.treated_at,
                treatment.capability,
                treatment.requested_amount,
                treatment.executed_amount,
                treatment.unit,
                treatment.adapter,
                int(treatment.safety_clamped),
            ),
        )
        self.conn.commit()

    def record_alert(self, alert: Alert) -> None:
        self.conn.execute(
            """INSERT INTO alerts
            (plant_id, created_at, severity, category, message, human_action_required, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                alert.plant_id,
                alert.created_at,
                alert.severity,
                alert.category,
                alert.message,
                int(alert.human_action_required),
                json.dumps(alert.evidence),
            ),
        )
        self.conn.commit()

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        tables = (
            "plants",
            "sensor_providers",
            "sensor_channels",
            "observations",
            "treatments",
            "alerts",
            "environments",
            "challenge_profiles",
            "experiments",
            "experiment_memberships",
            "genetic_profiles",
            "genetic_variants",
            "trait_observations",
            "perception_observations",
            "plant_state_estimates",
            "qualitative_observations",
            "knowledge_entries",
        )
        for table in tables:
            result[table] = int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return result
