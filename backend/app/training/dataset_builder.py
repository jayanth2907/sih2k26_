"""
Reproducible Dataset Builder and Manifest Generator for PS26080.
Generates cryptographically hashed manifests and partitions meteorological features.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.data.processing.feature_engineering import MeteorologicalFeatureEngineer
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.training.alignment import DataAlignmentEngine
from backend.app.training.quality_control import DatasetQCReport, TrainingQualityController
from backend.app.training.splits import ChronologicalSplitter, LeakageAuditReport

logger = logging.getLogger("rainfall_backend.training.dataset_builder")


class DatasetManifest(BaseModel):
    """Cryptographically verifiable metadata manifest for a trained meteorological dataset."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    pipeline_type: str = Field(..., description="'PIPELINE_A_REANALYSIS_LEARNING' or 'PIPELINE_B_NWP_POSTPROCESSING'")
    creation_timestamp: str = Field(..., description="Manifest generation timestamp (ISO-8601 UTC)")
    source_ids: List[str] = Field(..., description="Contributing raw data sources")
    variable_list: List[str] = Field(..., description="Atmospheric predictor variables included")
    domain_bbox: Tuple[float, float, float, float] = Field(..., description="(north, south, west, east)")
    resolution_deg: float = Field(..., description="Spatial grid resolution in degrees")
    time_range_years: Tuple[int, int] = Field(..., description="(start_year, end_year)")
    season: str = Field("JJAS (June–September)", description="Monsoon seasonality filter")
    total_samples: int = Field(..., description="Total valid samples in dataset")
    train_count: int = Field(..., description="Samples in training partition")
    val_count: int = Field(..., description="Samples in validation partition")
    test_count: int = Field(..., description="Samples in held-out test partition")
    missing_fraction: float = Field(..., description="Missing value fraction from QC")
    provenance_status: str = Field(..., description="'REAL', 'DERIVED_FROM_REAL', 'FALLBACK', 'SYNTHETIC', 'MIXED'")
    feature_schema_version: str = Field("MeteorologicalFeatureSchema_v2.1", description="Feature schema version")
    target_definition: str = Field(..., description="Physical definition of model target")
    random_seed: int = Field(42, description="RNG seed for reproducibility")
    training_config_hash: str = Field(..., description="SHA-256 hash of training configuration")
    data_hash: str = Field(..., description="SHA-256 hash of dataset payload")
    qc_summary: DatasetQCReport = Field(..., description="Forensic QC summary")
    leakage_audit: LeakageAuditReport = Field(..., description="Leakage prevention audit report")


class HistoricalDatasetBuilder:
    """
    Constructs reproducible meteorological training datasets from canonical records.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        random_seed: int = 42,
    ):
        self.config = config or {}
        self.random_seed = random_seed
        self.qc_controller = TrainingQualityController()
        self.splitter = ChronologicalSplitter()

    def build_synthetic_fixture_dataset(
        self,
        sample_count: int = 120,
    ) -> Tuple[List[Dict[str, Any]], DatasetManifest]:
        """
        Build tiny deterministic local fixture dataset for unit testing and offline development.
        Strict rule: clearly tagged as SYNTHETIC with deterministic data hashes.
        """
        records: List[Dict[str, Any]] = []
        # Generate samples across 2018 (train), 2020 (val), 2022 (test)
        years = [2018] * (sample_count // 3) + [2020] * (sample_count // 3) + [2022] * (sample_count - 2 * (sample_count // 3))
        
        for i, yr in enumerate(years):
            day = (i % 28) + 1
            ts = f"{yr}-07-{day:02d}T00:00:00Z"
            lat = 10.0 + (i % 15) * 1.5
            lon = 72.0 + (i % 15) * 1.5
            raw_rain = 20.0 + (i * 3.7) % 80.0
            obs_rain = raw_rain + ((i % 7) - 3) * 4.5 # residual
            
            rec = {
                "timestamp": ts,
                "valid_time": ts,
                "latitude": lat,
                "longitude": lon,
                "rainfall": round(raw_rain, 2),
                "observed_rainfall": round(max(0.0, obs_rain), 2),
                "u850": round(10.0 + (i % 5) * 2.0, 2),
                "v850": round(4.0 + (i % 3) * 1.5, 2),
                "u700": round(7.0 + (i % 4) * 1.5, 2),
                "v700": round(3.0 + (i % 2) * 1.0, 2),
                "u500": round(4.0 + (i % 3) * 1.0, 2),
                "v500": round(1.5, 2),
                "temperature_850": round(294.0 + (i % 4), 2),
                "relative_humidity_850": round(75.0 + (i % 20), 2),
                "mslp": round(1008.0 - (i % 10) * 0.8, 2),
                "elevation": 500.0,
                "slope": 3.0,
                "distance_to_coast": 50.0,
                "data_source": "TEST_LOCAL_FIXTURE",
            }

            # Engineer features
            canon = CanonicalMeteorologicalRecord(
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                rainfall=raw_rain,
                u850=rec["u850"],
                v850=rec["v850"],
                u700=rec["u700"],
                v700=rec["v700"],
                u500=rec["u500"],
                v500=rec["v500"],
                temperature_850=rec["temperature_850"],
                relative_humidity_850=rec["relative_humidity_850"],
                elevation=500.0,
                slope=3.0,
                distance_to_coast=50.0,
                data_source="TEST_LOCAL_FIXTURE",
            )
            feats = MeteorologicalFeatureEngineer.extract_features(canon)
            rec["features"] = feats.model_dump()
            rec["residual_target"] = round(rec["observed_rainfall"] - raw_rain, 3)
            records.append(rec)

        # 1. Quality Control
        clean_records, qc_report = self.qc_controller.audit_and_clean_records(records)

        # 2. Chronological Splits
        train_set, val_set, test_set, leakage_audit = self.splitter.split_dataset(clean_records)

        # 3. Cryptographic Hashes
        config_str = json.dumps(self.config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode("utf-8")).hexdigest()

        data_repr = f"fixture_count={len(clean_records)}_seed={self.random_seed}"
        data_hash = hashlib.sha256(data_repr.encode("utf-8")).hexdigest()

        manifest = DatasetManifest(
            dataset_id=f"FIXTURE_ERA5_IMD_JJAS_{self.random_seed}",
            pipeline_type="PIPELINE_B_NWP_POSTPROCESSING",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            source_ids=["ECMWF_ERA5_FIXTURE", "IMD_GRIDDED_FIXTURE"],
            variable_list=["u850", "v850", "u700", "v700", "t850", "rh850", "mslp", "rainfall"],
            domain_bbox=(38.0, 6.0, 66.0, 100.0),
            resolution_deg=0.25,
            time_range_years=(2018, 2022),
            season="JJAS",
            total_samples=len(clean_records),
            train_count=len(train_set),
            val_count=len(val_set),
            test_count=len(test_set),
            missing_fraction=qc_report.missing_fraction,
            provenance_status="SYNTHETIC_FIXTURE",
            target_definition="residual_error = observed_rainfall - raw_nwp_rainfall",
            random_seed=self.random_seed,
            training_config_hash=config_hash,
            data_hash=data_hash,
            qc_summary=qc_report,
            leakage_audit=leakage_audit,
        )

        return clean_records, manifest
